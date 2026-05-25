"""Step E 验证：把 TTS 生成的 final_60s.mp3 用同一套 ASR+VAD pipeline 跑一遍
对照 voice_codex.yaml 的 tts_validation_checklist 出评分。
"""
import os
import json
import yaml
import wave
import subprocess
from pathlib import Path

NV = "./.venv/lib/python3.12/site-packages/nvidia"
os.environ["LD_LIBRARY_PATH"] = f"{NV}/cublas/lib:{NV}/cudnn/lib:" + os.environ.get("LD_LIBRARY_PATH", "")

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions

ROOT = Path("pipeline/02-配音")
MP3 = ROOT / "tts_output" / "final_60s.mp3"
SCRIPT_FILE = ROOT / "script_60s_validate.yaml"
CODEX_FILE = ROOT / "voice_codex.yaml"


def is_chinese_char(c):
    return '一' <= c <= '鿿'


def count_chars(t):
    return sum(1 for c in t if is_chinese_char(c))


def main():
    if not MP3.exists():
        print(f"[FATAL] {MP3} 不存在，先跑 tts_volc.py")
        return

    script = yaml.safe_load(open(SCRIPT_FILE))
    codex = yaml.safe_load(open(CODEX_FILE))

    # mp3 -> 16k mono wav
    wav = ROOT / "tts_output" / "final_60s.wav"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(MP3), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)
    ], check=True)

    # ASR
    print("[load] large-v3...")
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    print("[asr]...")
    segs, info = model.transcribe(str(wav), word_timestamps=True, language="zh", beam_size=5)
    asr_segs = list(segs)
    duration = info.duration
    all_text = "".join(s.text for s in asr_segs)
    total_chars = count_chars(all_text)

    # VAD
    with wave.open(str(wav), "rb") as w:
        sr = w.getframerate(); n = w.getnframes()
        audio = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    ts = get_speech_timestamps(audio, vad_options=VadOptions(threshold=0.5, min_silence_duration_ms=80, min_speech_duration_ms=150))
    speech_segs = [{"start": s["start"]/sr, "end": s["end"]/sr} for s in ts]
    speech_total = sum(s["end"] - s["start"] for s in speech_segs)
    breath_gaps = [speech_segs[i+1]["start"] - speech_segs[i]["end"] for i in range(len(speech_segs)-1)]
    breath_total = sum(g for g in breath_gaps if g > 0.02)
    breath_max_ms = max(breath_gaps) * 1000 if breath_gaps else 0

    cps_global = total_chars / max(speech_total, 0.001)
    wpm_global = cps_global * 60
    voice_ratio = speech_total / duration

    print(f"\n=== TTS 实测 ===")
    print(f"时长: {duration:.1f}s (目标 60s)")
    print(f"识别字数: {total_chars} (目标 {script['meta']['total_chars']})")
    print(f"全局 WPM: {wpm_global:.0f} (目标 367, safe [337, 393])")
    print(f"全局 CPS: {cps_global:.2f} (目标 6.11)")
    print(f"人声占比: {voice_ratio:.3f} (目标 ≥0.95)")
    print(f"气口总: {breath_total:.2f}s (目标 ≤2s)")
    print(f"最长气口: {breath_max_ms:.0f}ms (目标 ≤500ms)")

    # codex 检查
    print(f"\n=== Codex 校验 ===")
    rules = codex["tts_validation_checklist"]
    score = 0; total = 0
    def chk(cond, name):
        nonlocal score, total
        total += 1
        if cond:
            score += 1
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")

    safe_lo, safe_hi = codex["global"]["safe_range_wpm"]
    chk(safe_lo <= wpm_global <= safe_hi, f"全片 WPM ∈ [{safe_lo}, {safe_hi}] (实际 {wpm_global:.0f})")
    chk(voice_ratio >= 0.95, f"人声占比 ≥0.95 (实际 {voice_ratio:.3f})")
    chk(breath_total <= 2.0, f"气口总 ≤2s (实际 {breath_total:.2f}s)")
    chk(breath_max_ms <= 500, f"最长气口 ≤500ms (实际 {breath_max_ms:.0f}ms)")
    chk(240 <= wpm_global <= 430, f"WPM 极限 [240, 430] (实际 {wpm_global:.0f})")

    print(f"\n[评分] {score}/{total} = {score/total*100:.0f}%")
    if score == total:
        print("[判定] ✅ 符合极客风 codex，TTS 路线验证通过")
    else:
        print("[判定] ⚠️ 部分指标超标，调整 speed_ratio 或换音色重试")


if __name__ == "__main__":
    main()
