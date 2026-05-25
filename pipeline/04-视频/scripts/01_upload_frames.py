"""
Step 3 · 01 - 压缩首帧图 + 上传到 liclick（跨产品通用）

输入：storyboard.json + 首帧图目录（PNG 或 JPG）
处理：
- PNG > 1MB 触发 atlas-skillhub HTTP 413 → 全部 ffmpeg 压成 1920w JPG (~500KB)
- 串行上传（并发 4 会偶发 502）
- 失败 retry 3 次
输出：frame_assets.json {shot_id: liclick_asset_id}

Usage:
    python 01_upload_frames.py <storyboard.json> <img_dir> <out_dir>
"""
import json, subprocess, sys, re, time
from pathlib import Path

SB_JSON = sys.argv[1]
IMG_DIR = Path(sys.argv[2])
OUT_DIR = Path(sys.argv[3])
OUT_DIR.mkdir(parents=True, exist_ok=True)

sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))
shots = [s["shot_id"] for s in sb["shots"]]

# Step 1: compress PNG -> JPG
JPG_DIR = OUT_DIR / "frames_jpg"
JPG_DIR.mkdir(exist_ok=True)
print(f"[1] Compress {len(shots)} frames to JPG (1920w, q4)...")
for sid in shots:
    src = IMG_DIR / f"{sid}.png"
    if not src.exists():
        src = IMG_DIR / f"{sid}.jpg"
    if not src.exists():
        print(f"  [✗] {sid} no source"); continue
    dst = JPG_DIR / f"{sid}.jpg"
    if dst.exists() and dst.stat().st_size < 1_000_000:
        continue
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", "scale='min(1920,iw)':-2", "-q:v", "4", str(dst)], check=True)
print(f"  done: {len(list(JPG_DIR.glob('*.jpg')))}/{len(shots)}")

# Step 2: serial upload (avoid 502)
asset_map_path = OUT_DIR / "frame_assets.json"
asset_map = json.loads(asset_map_path.read_text(encoding="utf-8")) if asset_map_path.exists() else {}
to_upload = [s for s in shots if s not in asset_map]
print(f"\n[2] Upload {len(to_upload)} frames (serial)...")

for sid in to_upload:
    fp = JPG_DIR / f"{sid}.jpg"
    for attempt in range(3):
        cmd = ["atlas-skillhub", "gateway", "call-tool",
               "--service", "liclick", "--tool", "upload_asset",
               "--args", json.dumps({"asset_type": "image"}, ensure_ascii=False),
               "--file", f"file_path={fp}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        out = r.stdout
        try:
            obj = json.loads(out)
        except Exception:
            mj = re.search(r'\{[\s\S]*\}\s*$', out)
            obj = json.loads(mj.group(0)) if mj else {}
        text = "".join([c.get("text", "") for c in obj.get("content", [])])
        m = re.search(r'asset_id["\s:]+([a-zA-Z0-9_-]+)', text)
        if m:
            asset_map[sid] = m.group(1)
            print(f"  [✓] {sid} -> {m.group(1)}")
            break
        time.sleep(2)
    else:
        print(f"  [✗] {sid} failed after 3 attempts")
    time.sleep(0.5)

asset_map_path.write_text(json.dumps(asset_map, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n-> frame_assets.json ({len(asset_map)}/{len(shots)})")
