"""Step E: 用火山引擎豆包 TTS 按 voice_codex 规则生成 60s 口播
- 输入: script_60s_validate.yaml + .env 火山 appid/access_token
- 输出: tts_output/seg{N}_{role}.mp3 (每段) + tts_output/final_60s.mp3 (concat)
- 后处理: ffmpeg silenceremove 压气口 + atempo 微调
"""
import os
import json
import yaml
import base64
import uuid
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path("pipeline/02-配音")
SCRIPT_FILE = ROOT / "script_60s_validate.yaml"
OUT_DIR = ROOT / "tts_output"
OUT_DIR.mkdir(exist_ok=True)

# 读 .env
def load_env():
    env = {}
    with open("./.env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

env = load_env()
APPID = env.get("VOLC_TTS_APPID")
TOKEN = env.get("VOLC_TTS_ACCESS_TOKEN")
CLUSTER = env.get("VOLC_TTS_CLUSTER", "volcano_tts")
ENDPOINT = env.get("VOLC_TTS_ENDPOINT", "https://openspeech.bytedance.com/api/v1/tts")
VOICE = env.get("VOLC_TTS_VOICE", "BV056_streaming")  # 解说男声 (改 BV701/BV012 试其他)

if not APPID or not TOKEN:
    print("[FATAL] .env 缺 VOLC_TTS_APPID / VOLC_TTS_ACCESS_TOKEN")
    print("  请在火山控制台 https://console.volcengine.com/speech/service/8 申请后填入")
    import sys; sys.exit(1)


def synth_one(seg):
    """调用火山 TTS 生成单段 mp3"""
    body = {
        "app": {"appid": APPID, "token": TOKEN, "cluster": CLUSTER},
        "user": {"uid": "geek_codex_test"},
        "audio": {
            "voice_type": VOICE,
            "encoding": "mp3",
            "speed_ratio": seg["speed_ratio"],
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": seg["text"],
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
        }
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{TOKEN}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read().decode())
    if resp.get("code") != 3000:
        raise RuntimeError(f"TTS fail: {resp.get('code')} {resp.get('message')}")
    return base64.b64decode(resp["data"])


def main():
    script = yaml.safe_load(open(SCRIPT_FILE))
    segs = script["segments"]
    print(f"[start] {len(segs)} 段, voice={VOICE}, cluster={CLUSTER}")

    mp3_paths = []
    for seg in segs:
        fname = f"seg{seg['segment_id']}_{seg['semantic_role']}.mp3"
        out = OUT_DIR / fname
        print(f"[seg{seg['segment_id']}] {seg['semantic_role']} | speed={seg['speed_ratio']} | chars={seg['actual_chars']} | target={seg['duration_target_sec']}s")
        print(f"  text: {seg['text'][:40]}...")
        mp3 = synth_one(seg)
        out.write_bytes(mp3)
        mp3_paths.append(str(out))

    # concat 6 段
    concat_list = OUT_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for p in mp3_paths:
            f.write(f"file '{p}'\n")
    raw_concat = OUT_DIR / "final_60s_raw.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", str(raw_concat)
    ], check=True)
    print(f"[concat] {raw_concat}")

    # 后处理：压气口 + 轻微加速（按 voice_codex.tts_implementation.post_processing_pipeline）
    polished = OUT_DIR / "final_60s.mp3"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(raw_concat),
        "-af", "silenceremove=start_periods=-1:stop_threshold=-30dB:stop_duration=0.15,atempo=1.03",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(polished)
    ], check=True)
    print(f"[polished] {polished}")

    # 时长 check
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(polished)],
        capture_output=True, text=True
    ).stdout.strip()
    print(f"[final] 时长 {dur}s (目标 60s)")
    print(f"\n[next] python scripts/validate_tts.py 跑 codex 验证")


if __name__ == "__main__":
    main()
