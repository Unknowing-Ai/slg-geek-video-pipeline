"""
Step 3 · 04 - ffmpeg 按 ASL 严格裁切 + Hard_Cut 拼接 60s（跨产品通用）

策略：
- 每镜按 storyboard.duration 取生成视频的中段（保留运动峰值）
- 统一编码 1920x1080 30fps + silent stereo audio (concat 需统一)
- ffmpeg -c copy 拼接（无渐变 = Hard_Cut 符合 BIN-03）

Usage:
    python 04_cut_concat.py <storyboard.json> <out_dir> [desktop_dir]
"""
import json, subprocess, sys, shutil
from pathlib import Path

SB_JSON = sys.argv[1]
OUT_DIR = Path(sys.argv[2])
DESK = sys.argv[3] if len(sys.argv) > 3 else None

sb = json.loads(Path(SB_JSON).read_text(encoding="utf-8"))
TITLE = sb.get("meta", {}).get("video_title", "video")
VID = OUT_DIR / "videos"
CUT = OUT_DIR / "videos_cut"; CUT.mkdir(exist_ok=True)

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","stream=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)], capture_output=True, text=True)
    for x in r.stdout.split():
        try: return float(x)
        except: continue
    return 5.0

cuts = []
print(f"[1] Cut {len(sb['shots'])} videos to ASL...")
for shot in sb["shots"]:
    sid = shot["shot_id"]
    target = shot["duration"]
    src = VID / f"{sid}.mp4"
    if not src.exists():
        print(f"  [✗] missing {sid}"); continue
    gen = dur(src)
    start = max(0, (gen - target) / 2)
    dst = CUT / f"{sid}.mp4"
    cmd = ["ffmpeg","-y",
           "-ss",f"{start:.3f}","-t",f"{target:.3f}","-i",str(src),
           "-f","lavfi","-t",f"{target:.3f}","-i","anullsrc=channel_layout=stereo:sample_rate=44100",
           "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fps=30",
           "-c:v","libx264","-pix_fmt","yuv420p","-preset","fast","-crf","20",
           "-c:a","aac","-b:a","128k",
           "-map","0:v:0","-map","1:a:0",
           str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if dst.exists():
        cuts.append(dst)
        print(f"  [✓] {sid}: cut {start:.2f}+{target:.2f}s")
    else:
        print(f"  [✗] {sid} ffmpeg:", r.stderr[-150:])

print(f"\n[2] Concat {len(cuts)} clips...")
list_file = OUT_DIR / "concat_list.txt"
list_file.write_text("\n".join(f"file '{p}'" for p in cuts), encoding="utf-8")
final = OUT_DIR / f"{TITLE}_60s_final.mp4"
r = subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(list_file),"-c","copy",str(final)], capture_output=True, text=True)
if final.exists():
    d = dur(final); sz = final.stat().st_size // 1024 // 1024
    print(f"  ✅ {final.name} | {d:.2f}s | {sz} MB")
    if DESK:
        Path(DESK).mkdir(parents=True, exist_ok=True)
        shutil.copy(final, Path(DESK) / final.name)
        clips_dir = Path(DESK) / "单镜"; clips_dir.mkdir(exist_ok=True)
        for c in cuts:
            shutil.copy(c, clips_dir / c.name)
        print(f"  -> Desktop: {DESK}/")
else:
    print(f"  ✗ concat failed:", r.stderr[-300:])
