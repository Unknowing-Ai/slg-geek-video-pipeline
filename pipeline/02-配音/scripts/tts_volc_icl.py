"""Step E3: 用火山豆包 ICL 克隆音色生成 60s 极客风口播
按 voice_codex.yaml 规则：6 段位 × 不同 speed_ratio
输出：tts_output/seg{N}_{role}.mp3 (每段) + final_60s.mp3 (concat + 后处理)
"""
import os
import sys
import json
import yaml
import base64
import uuid
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

API_KEY = os.environ["VOLC_ICL_API_KEY"]  # 火山 ICL api-key (env var)
CLUSTER = "volcano_icl"
ENDPOINT = "https://openspeech.bytedance.com/api/v1/tts"

ROOT = Path("pipeline/02-配音")
SCRIPT_FILE = ROOT / "script_60s_validate.yaml"
OUT_DIR = ROOT / "tts_output"
OUT_DIR.mkdir(exist_ok=True)

# 从命令行取 speaker_id（蛋仔训练后给的 voice_id）
SPEAKER_ID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("VOLC_SPEAKER_ID")
if not SPEAKER_ID:
    print("Usage: python tts_volc_icl.py <speaker_id>")
    print("   or: VOLC_SPEAKER_ID=S_xxx python tts_volc_icl.py")
    sys.exit(1)


def synth_one(seg):
    body = {
        "app": {"cluster": CLUSTER},
        "user": {"uid": "geek_codex"},
        "audio": {
            "voice_type": SPEAKER_ID,
            "encoding": "mp3",
            "speed_ratio": seg["speed_ratio"],
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": seg["text"],
            "operation": "query",
        }
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body_err}")
    if resp.get("code") != 3000:
        raise RuntimeError(f"TTS code={resp.get('code')}: {resp.get('message')}")
    return base64.b64decode(resp["data"])


def main():
    script = yaml.safe_load(open(SCRIPT_FILE))
    segs = script["segments"]
    print(f"[start] speaker_id={SPEAKER_ID}, {len(segs)} 段")

    mp3_paths = []
    for seg in segs:
        fname = f"seg{seg['segment_id']}_{seg['semantic_role']}.mp3"
        out = OUT_DIR / fname
        print(f"[seg{seg['segment_id']}] {seg['semantic_role']} speed={seg['speed_ratio']} chars={seg['actual_chars']}")
        print(f"  text: {seg['text'][:50]}...")
        try:
            mp3 = synth_one(seg)
            out.write_bytes(mp3)
            print(f"  → {out.name} {len(mp3)/1024:.0f}KB")
            mp3_paths.append(str(out))
        except Exception as e:
            print(f"  [FAIL] {e}")
            return

    # concat
    concat_list = OUT_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for p in mp3_paths:
            f.write(f"file '{p}'\n")
    raw = OUT_DIR / "final_60s_raw.mp3"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "concat", "-safe", "0", "-i", str(concat_list),
                    "-c", "copy", str(raw)], check=True)

    # 后处理：压气口 + 轻微加速（按 voice_codex.tts_implementation 规则）
    polished = OUT_DIR / "final_60s.mp3"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(raw),
                    "-af", "silenceremove=stop_periods=-1:stop_duration=0.15:stop_threshold=-30dB,atempo=1.03",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(polished)], check=True)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(polished)],
        capture_output=True, text=True
    ).stdout.strip()
    print(f"\n[final] {polished} | {dur}s (目标 60s)")
    print(f"[next] python scripts/validate_tts.py")


if __name__ == "__main__":
    main()
