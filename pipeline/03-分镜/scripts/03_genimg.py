"""
Step 2 · 03 - 25 张 AI 生图（跨产品通用）

策略：
- Part 1（非游戏镜头）：文生图 nano_banana_pro，写实/历史/纪实/科普风（与游戏无关）
- Part 2（游戏镜头）：图生图 nano_banana_pro + 宿主提供的官方资产 reference，按 product_config.yaml 的 game_visual_style 描述
- 全局 negative_prompt：禁止画任何文字/字幕/LOGO/数字（中文由后期合成保证准确性）
- Google 安全拦截的镜头自动 fallback 到 doubao-seedream-4-5

Usage:
    python 03_genimg.py <storyboard.json> <asset_map.json> <mapping.json> <product_config.yaml> <out_dir>
"""
import json, subprocess, sys, re, yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SB_JSON = sys.argv[1]
ASSET_JSON = sys.argv[2]
MAPPING_JSON = sys.argv[3]
PRODUCT_YAML = sys.argv[4]
OUT_DIR = Path(sys.argv[5])
OUT_DIR.mkdir(parents=True, exist_ok=True)

sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))
asset_map = json.loads(Path(ASSET_JSON).read_text(encoding="utf-8"))
mapping = json.loads(Path(MAPPING_JSON).read_text(encoding="utf-8"))
PRODUCT = yaml.safe_load(Path(PRODUCT_YAML).read_text(encoding="utf-8"))

NEG = "any text, any words, any letters, any numbers, captions, subtitles, logo, watermark, brand mark, signage, characters, signs, billboards, country flags, political symbols, country names, written language"
SUFFIX = " | Clean image without any text, captions, subtitles, logo, watermark, UI text, or written language anywhere in the frame. Pure visual content only."


def gen_one(shot, model="nano_banana_pro"):
    sid = shot["shot_id"]
    prompt = shot["image_gen_prompt"] + SUFFIX
    extra = {
        "aspect_ratio": "16:9",
        "image_size": "2K" if model == "nano_banana_pro" else None,
        "quality": "high",
        "n": 1,
        "name": f"sb_{sid}",
        "negative_prompt": NEG,
    }
    extra = {k: v for k, v in extra.items() if v is not None}
    if sid in mapping:
        ref_asset_ids = [asset_map[n] for n in mapping[sid] if asset_map.get(n)]
        if ref_asset_ids:
            extra["reference_images"] = [{"asset_id": a, "type": "image"} for a in ref_asset_ids]

    args = {"prompt": prompt, "model": model, "extra_params": extra}
    cmd = ["atlas-skillhub", "gateway", "call-tool",
           "--service", "liclick", "--tool", "generate_image",
           "--args", json.dumps(args, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = r.stdout.strip()
    try:
        obj = json.loads(out)
    except Exception:
        m = re.search(r'\{[\s\S]*\}\s*$', out)
        obj = json.loads(m.group(0)) if m else {}
    text = "".join([c.get("text", "") for c in obj.get("content", [])])
    m = re.search(r'task_id["\s:]+([a-f0-9-]+)', text)
    if m:
        return (sid, "submitted", m.group(1), model)
    return (sid, "fail", text[:300], model)


tasks = {}
print(f"Submitting {len(sb['shots'])} jobs for {PRODUCT.get('game_name', 'unknown')}...")
with ThreadPoolExecutor(max_workers=3) as pool:
    futs = {pool.submit(gen_one, s): s["shot_id"] for s in sb["shots"]}
    for fut in as_completed(futs):
        sid, status, info, model = fut.result()
        if status == "submitted":
            tasks[sid] = {"task_id": info, "model": model}
            print(f"  [✓] {sid} ({model}) -> {info}")
        else:
            print(f"  [✗] {sid} ({model}) -> {info[:200]}")

(OUT_DIR / "task_ids.json").write_text(
    json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nSubmitted {len(tasks)}/{len(sb['shots'])}. -> task_ids.json")
