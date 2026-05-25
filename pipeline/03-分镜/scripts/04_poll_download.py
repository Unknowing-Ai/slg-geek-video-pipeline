"""
Step 2 · 04 - Poll liclick tasks + 下载图到本地

策略：
- 每 10 秒轮询一次，最多 8 分钟
- 完成的下载到 images/{shot_id}.png
- 失败的（"Failed" / "失败" / Google 安全拦截）记录到 failed.json
- 自动用 doubao-seedream-4-5 fallback 重生失败镜头（去掉敏感词）

输入：task_ids.json
输出：images/ + dl_results.json

Usage:
    python 04_poll_download.py <task_ids.json> <storyboard.json> <out_dir>
"""
import json, subprocess, sys, re, time, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TASKS_JSON = sys.argv[1]
SB_JSON = sys.argv[2]
OUT_DIR = Path(sys.argv[3])
IMG_DIR = OUT_DIR / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

tasks = json.loads(Path(TASKS_JSON).read_text(encoding="utf-8"))
sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))
shot_map = {s["shot_id"]: s for s in sb["shots"]}


def poll(sid, tid):
    for _ in range(50):
        cmd = ["atlas-skillhub", "gateway", "call-tool",
               "--service", "liclick", "--tool", "get_task_status",
               "--args", json.dumps({"task_id": tid, "task_type": "image"})]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        obj = json.loads(r.stdout.strip())
        text = "".join([c.get("text", "") for c in obj.get("content", [])])
        if "完成" in text or "Finished" in text:
            m = re.search(r'(https?://[^\s)]+)', text)
            if m:
                urllib.request.urlretrieve(m.group(1).rstrip(','), IMG_DIR / f"{sid}.png")
                return (sid, "ok", "")
        elif "失败" in text or "Failed" in text:
            return (sid, "failed", text[:300])
        time.sleep(10)
    return (sid, "timeout", "")


# 第一轮 poll
results = {}
with ThreadPoolExecutor(max_workers=8) as pool:
    futs = {pool.submit(poll, sid, info["task_id"]): sid for sid, info in tasks.items()}
    for fut in as_completed(futs):
        sid, status, info = fut.result()
        results[sid] = {"status": status, "info": info}
        print(f"  [{'✓' if status == 'ok' else '✗'}] {sid} -> {status}")

ok = sum(1 for r in results.values() if r["status"] == "ok")
failed = [sid for sid, r in results.items() if r["status"] == "failed"]

# 失败 fallback 到 doubao-seedream
if failed:
    print(f"\n{len(failed)} failed. Retry via doubao-seedream-4-5...")
    NEG = "any text, any words, captions, logo, watermark, country flags, political symbols, country names"
    for sid in failed:
        prompt = shot_map[sid]["image_gen_prompt"] + " | Clean image, no text, no logo"
        # 去掉敏感词
        prompt = re.sub(r'(Eurasian|conquest|战争|征服|国家|war)', '', prompt, flags=re.IGNORECASE)
        args = {"prompt": prompt, "model": "doubao-seedream-4-5-251128",
                "extra_params": {"aspect_ratio": "16:9", "quality": "high", "n": 1,
                                 "name": f"fallback_{sid}"}}
        cmd = ["atlas-skillhub", "gateway", "call-tool",
               "--service", "liclick", "--tool", "generate_image",
               "--args", json.dumps(args, ensure_ascii=False)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        obj = json.loads(r.stdout.strip())
        text = "".join([c.get("text", "") for c in obj.get("content", [])])
        m = re.search(r'task_id["\s:]+([a-f0-9-]+)', text)
        if m:
            tid = m.group(1)
            # 立即 poll 该 task
            sid2, status, info = poll(sid, tid)
            results[sid] = {"status": status, "info": f"fallback: {info}", "model": "doubao"}
            print(f"  [{'✓' if status == 'ok' else '✗'}] fallback {sid}")

(OUT_DIR / "dl_results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
ok2 = sum(1 for r in results.values() if r["status"] == "ok")
print(f"\nFinal: OK={ok2}/{len(tasks)}")
