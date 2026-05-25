"""
Step 3 · 02 - 提交 N 个视频生成任务（跨产品通用）

铁律应用：
- 铁律 1 动作连续：从 storyboard.visual_description + sequence_group_id 设计 video_prompt
- 铁律 2 主体内部动态：每镜 prompt 必须含主体动作循环描述
- 铁律 3 文化统一：Part 1 从 product_config.yaml 读 part1_anchor（由宿主定义）
- 铁律 4 禁英文：NEG 含 latin letters, english characters, download
- 铁律 5 训练资产：reference_images 用宿主提供的【动作姿态资产】

模型：Part 1 用 kling-v2-5-turbo, Part 2 用 doubao-seedance-2-0-260128
失败 fallback 到 kling

Usage:
    python 02_gen_video.py <storyboard.json> <frame_assets.json> <product_config.yaml> <out_dir>
"""
import json, subprocess, sys, re, time, yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SB_JSON = sys.argv[1]
ASSET_JSON = sys.argv[2]
PRODUCT_YAML = sys.argv[3]
OUT_DIR = Path(sys.argv[4])
OUT_DIR.mkdir(parents=True, exist_ok=True)

sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))
asset_map = json.loads(Path(ASSET_JSON).read_text(encoding="utf-8"))
PRODUCT = yaml.safe_load(Path(PRODUCT_YAML).read_text(encoding="utf-8"))

# 由宿主定义的文化/视觉锚定（跨产品参数化）
PART1_ANCHOR = PRODUCT.get("part1_anchor",
    "period-accurate historical drama with culturally consistent characters and costumes")
PART2_ANCHOR = PRODUCT.get("part2_anchor",
    f"{PRODUCT.get('game_visual_style','game CG art style')}")
PART1_NEG = PRODUCT.get("part1_neg_extra", "")
PART2_NEG = PRODUCT.get("part2_neg_extra", "")
LANG_NEG = PRODUCT.get("forbidden_language_neg",
    "latin letters, english characters, download button, click here")

# 通用 NEG（5 条铁律共性部分）
COMMON_NEG = ("any text, captions, subtitles, logo, watermark, UI text, score, numbers, "
              "transition effect, fade in, fade out, dissolve, wipe, cut to black, scene transition, "
              "time skip, montage, jump cut, slow motion pause, freeze frame, static image, no movement")

def build_neg(is_p2):
    parts = [COMMON_NEG, LANG_NEG]
    if not is_p2 and PART1_NEG: parts.append(PART1_NEG)
    if is_p2 and PART2_NEG: parts.append(PART2_NEG)
    return ", ".join(p for p in parts if p)

CAMERA_HINT = {
    "Static": "static camera at fixed position, no camera movement, only subtle in-frame motion",
    "Zoom_In": "slow continuous zoom-in",
    "Zoom_Out": "slow continuous zoom-out, gradually pulling back",
    "Pan": "smooth horizontal camera pan",
    "Mixed": "smooth combined camera movement",
}

def build_video_prompt(shot):
    """构造 video prompt — 落地铁律 1/2/3/4"""
    seg = shot["segment"]
    cam = shot["camera"]
    vis = shot["visual_description"]
    is_p2 = seg in ("Ad_Reversal", "Selling_Point", "CTA")
    cam_hint = CAMERA_HINT.get(cam, "smooth camera movement")
    if is_p2:
        head = "Game CG scene."
        anchor = PART2_ANCHOR
        motion = ("Continuous uninterrupted motion with internal subject animation — characters/objects/effects "
                  "must be visibly moving/cycling/animating throughout the entire clip, not just camera movement. "
                  "No scene change, no transition effect, no text overlay, no UI label, no numbers, no game logo.")
    else:
        head = "Cinematic scene."
        anchor = PART1_ANCHOR
        motion = ("Continuous uninterrupted motion with internal subject animation — subjects (people/animals/objects) "
                  "must be visibly moving/cycling/animating throughout the entire clip (e.g., legs cycling, hooves stomping, "
                  "wheels spinning, breath vapor visible, fabric flowing). "
                  "No scene change, no transition effect, no text overlay.")
    return f"{head} {vis} {anchor}. {cam_hint}. {motion}"

def submit(shot, model_override=None):
    sid = shot["shot_id"]
    if sid not in asset_map:
        return sid, "no_asset", "", ""
    seg = shot["segment"]
    is_p2 = seg in ("Ad_Reversal", "Selling_Point", "CTA")
    model = model_override or ("doubao-seedance-2-0-260128" if is_p2 else "kling-v2-5-turbo")
    duration = 4 if (is_p2 and "seedance" in model) else 5
    args = {
        "request_type": "first_frame",
        "prompt": build_video_prompt(shot),
        "negative_prompt": build_neg(is_p2),
        "model": model,
        "reference_images": [{"asset_id": asset_map[sid], "type": "image"}],
        "extra_params": {"duration": duration, "aspect_ratio": "16:9", "resolution": "1080p"}
    }
    cmd = ["atlas-skillhub", "gateway", "call-tool",
           "--service", "liclick", "--tool", "generate_video",
           "--args", json.dumps(args, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = r.stdout
    try:
        obj = json.loads(out)
    except Exception:
        mj = re.search(r'\{[\s\S]*\}\s*$', out)
        obj = json.loads(mj.group(0)) if mj else {}
    text = "".join([c.get("text", "") for c in obj.get("content", [])])
    m = re.search(r'task_id["\s:]+([a-f0-9-]+)', text)
    if m:
        return sid, "submitted", m.group(1), model
    return sid, "fail", (text or out)[:300], model

tasks_path = OUT_DIR / "video_tasks.json"
tasks = json.loads(tasks_path.read_text(encoding="utf-8")) if tasks_path.exists() else {}
to_submit = [s for s in sb["shots"] if s["shot_id"] not in tasks]
print(f"Submit {len(to_submit)}/{len(sb['shots'])} video jobs for {PRODUCT.get('game_name','?')} (concurrency=2)...")
print(f"  Part1 anchor: {PART1_ANCHOR[:80]}...")
print(f"  Part2 anchor: {PART2_ANCHOR[:80]}...")

with ThreadPoolExecutor(max_workers=2) as pool:
    futs = {pool.submit(submit, s): s["shot_id"] for s in to_submit}
    for fut in as_completed(futs):
        sid, st, info, model = fut.result()
        if st == "submitted":
            tasks[sid] = {"task_id": info, "model": model}
            print(f"  [✓] {sid} ({model}) -> {info}")
        else:
            print(f"  [✗] {sid} ({model}): {info[:200]}")

tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n-> video_tasks.json ({len(tasks)}/{len(sb['shots'])})")
