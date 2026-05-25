"""
Step 3 · 03 - poll + 下载视频（跨产品通用）

策略：
- 每 30s 轮询，最多 40 轮（20 min）
- MCP 返回中文「完成」匹配
- 失败自动 fallback：seedance 切 kling（多文明/旗帜安全拦截常发）

Usage:
    python 03_poll_download.py <video_tasks.json> <storyboard.json> <product_config.yaml> <out_dir>
"""
import json, subprocess, sys, re, time, urllib.request, yaml
from pathlib import Path

TASKS_JSON = sys.argv[1]
SB_JSON = sys.argv[2]
PRODUCT_YAML = sys.argv[3]
OUT_DIR = Path(sys.argv[4])
VID = OUT_DIR / "videos"; VID.mkdir(exist_ok=True)

tasks = json.loads(Path(TASKS_JSON).read_text(encoding="utf-8"))
sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))

def status(tid):
    r = subprocess.run(["atlas-skillhub","gateway","call-tool","--service","liclick","--tool","get_task_status",
                       "--args", json.dumps({"task_id":tid,"task_type":"video"})], capture_output=True, text=True, timeout=60)
    out = r.stdout
    try: obj = json.loads(out)
    except Exception:
        mj = re.search(r'\{[\s\S]*\}\s*$', out)
        obj = json.loads(mj.group(0)) if mj else {}
    return "".join([c.get("text","") for c in obj.get("content",[])]) or out

def dl(url, fp):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(fp, "wb") as f:
        f.write(r.read())

pending = {sid: t for sid, t in tasks.items() if not (VID / f"{sid}.mp4").exists()}
failed = {}
print(f"Polling {len(pending)} video tasks...")
for rnd in range(40):
    if not pending: break
    print(f"--- Round {rnd+1} | pending={len(pending)} ---")
    done = []
    for sid, info in pending.items():
        text = status(info["task_id"])
        if "完成" in text or "Finished" in text:
            m = re.search(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
            if m:
                try:
                    dl(m.group(0), VID / f"{sid}.mp4")
                    print(f"  [✓] {sid} dl ({(VID/f'{sid}.mp4').stat().st_size//1024}KB)")
                    done.append(sid)
                except Exception as e:
                    print(f"  [?] {sid} dl err: {e}")
        elif "失败" in text or "failed" in text.lower() or "rejected" in text.lower():
            print(f"  [✗] {sid} FAILED: {text[:200]}")
            failed[sid] = info; done.append(sid)
    for sid in done: del pending[sid]
    if pending: time.sleep(30)

# fallback: 失败的转 kling 重提
if failed:
    print(f"\n{len(failed)} failed, retry with kling fallback...")
    PRODUCT = yaml.safe_load(Path(PRODUCT_YAML).read_text(encoding="utf-8"))
    asset_map = json.loads((OUT_DIR / "frame_assets.json").read_text(encoding="utf-8"))
    PART1_ANCHOR = PRODUCT.get("part1_anchor","")
    PART2_ANCHOR = PRODUCT.get("part2_anchor", PRODUCT.get("game_visual_style",""))
    LANG_NEG = PRODUCT.get("forbidden_language_neg","latin letters, english characters, download")
    COMMON_NEG = ("any text, captions, subtitles, logo, watermark, UI text, transition, fade, dissolve, wipe, "
                  "cut to black, jump cut, static image, no movement")
    shot_map = {s["shot_id"]: s for s in sb["shots"]}
    for sid in failed:
        shot = shot_map[sid]
        is_p2 = shot["segment"] in ("Ad_Reversal","Selling_Point","CTA")
        anchor = PART2_ANCHOR if is_p2 else PART1_ANCHOR
        prompt = f"Cinematic scene. {shot['visual_description']} {anchor}. Continuous uninterrupted motion with internal subject animation. No transition, no text."
        args = {"request_type":"first_frame","prompt":prompt,"negative_prompt":f"{COMMON_NEG}, {LANG_NEG}",
                "model":"kling-v2-5-turbo","reference_images":[{"asset_id":asset_map[sid],"type":"image"}],
                "extra_params":{"duration":5,"aspect_ratio":"16:9","resolution":"1080p"}}
        cmd = ["atlas-skillhub","gateway","call-tool","--service","liclick","--tool","generate_video","--args", json.dumps(args, ensure_ascii=False)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        out = r.stdout
        try: obj = json.loads(out)
        except Exception:
            mj = re.search(r'\{[\s\S]*\}\s*$', out); obj = json.loads(mj.group(0)) if mj else {}
        text = "".join([c.get("text","") for c in obj.get("content",[])])
        m = re.search(r'task_id["\s:]+([a-f0-9-]+)', text)
        if m:
            tasks[sid] = {"task_id": m.group(1), "model": "kling-v2-5-turbo"}
            print(f"  [✓] fallback {sid} -> {m.group(1)}")
            # poll
            for _ in range(30):
                time.sleep(30)
                text = status(m.group(1))
                if "完成" in text or "Finished" in text:
                    mu = re.search(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
                    if mu:
                        dl(mu.group(0), VID / f"{sid}.mp4"); print(f"    [✓] {sid} dl"); break
                elif "失败" in text or "failed" in text.lower():
                    print(f"    [✗] {sid} fallback also failed"); break
    Path(TASKS_JSON).write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

final_count = len(list(VID.glob("*.mp4")))
print(f"\nDone: {final_count}/{len(tasks)} videos downloaded.")
