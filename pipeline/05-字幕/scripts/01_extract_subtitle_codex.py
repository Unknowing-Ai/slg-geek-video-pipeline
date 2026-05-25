"""
Step 4 · 01 - 字幕 codex PoC 抽取

混合管线：
- Whisper (faster-whisper, base 模型, zh) → 口播句级时间戳 (秒级精准)
- Gemini 3.1 Pro Preview (LiteLLM) → 字幕样式 + 字幕文本 + 大致时间戳
- 后处理 → 字幕↔口播匹配率 + 切换丝滑度 + 样式 codex

输出: {out_dir}/{video_id}_subtitle.json + {video_id}_subtitle.md
"""
import json, re, sys, base64, subprocess, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(".")
MATERIALS = ROOT / "materials/videos"
OUT = ROOT / "pipeline/05-字幕/step1-PoC-5条"
COMP = OUT / "compressed"
ASR = OUT / "asr"
LLM = OUT / "llm"
MERGED = OUT / "merged"
for d in (COMP, ASR, LLM, MERGED): d.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    "ROK_头_01_为何古代一打仗就缺粮.mp4",
    "ROK_头_05_东西方骑兵对比.mp4",
    "ROK_尾_07_中式魅魔诱惑.mp4",
    "WGAME_头_13_阿帕奇有多猛.mp4",
    "Samo_头_23_人类为何没有驯化老虎.mp4",
]

# ============ Phase 1: ffmpeg 压缩 (复用 step2 参数) ============
def compress(src, dst):
    if dst.exists() and dst.stat().st_size > 100_000: return
    cmd = ["ffmpeg","-y","-loglevel","error","-i",str(src),
           "-vf","scale=640:-2,fps=12","-c:v","libx264","-preset","veryfast","-crf","30",
           "-c:a","aac","-b:a","64k",str(dst)]
    subprocess.run(cmd, check=True)

# ============ Phase 2: Whisper ASR ============
def asr(comp_mp4, out_json):
    if out_json.exists(): return json.loads(out_json.read_text(encoding="utf-8"))
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(comp_mp4), language="zh", word_timestamps=False, vad_filter=True)
    segs = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    obj = {"duration": info.duration, "language": info.language, "segments": segs}
    out_json.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return obj

# ============ Phase 3: Gemini 多模态抽字幕样式 + 文本 ============
SUBTITLE_PROMPT = """你是极客视频字幕分析师。看完这条视频，输出严格 JSON。

# 任务
1. 抽取所有字幕段（字幕显示时间 + 文本，按时间顺序）
2. 抽取字幕样式 codex（位置/字号/字体/颜色/动画/高亮规则）
3. 标注美感判断（极客号字幕美感的具体体现）

# 输出 JSON Schema（严格遵守，不要 markdown 包裹）
{
  "subtitles": [
    {"start_sec": 0.5, "end_sec": 2.1, "text": "字幕文本", "is_highlighted_keyword": true, "highlight_words": ["关键词"]}
  ],
  "style": {
    "position": {
      "vertical_region": "bottom_third | middle | top_third | varying",
      "horizontal": "center | left | right",
      "y_percent_from_top_estimate": 75,
      "notes": "位置稳定性 / 例外情况"
    },
    "size": {
      "height_percent_of_frame": 8,
      "category": "small | medium | large | XL",
      "notes": "字号变化模式"
    },
    "font": {
      "weight": "regular | bold | extra_bold",
      "style_category": "modern_sans | brush_script | impact_style | traditional | mixed",
      "family_guess": "思源黑体 / 阿里巴巴普惠体 / 站酷高端黑 / 类似字体",
      "notes": "字体特征"
    },
    "color": {
      "main_hex": "#FFFFFF",
      "stroke_hex": "#000000",
      "stroke_width_estimate": "thin | medium | thick",
      "shadow": true,
      "background": "none | semi_transparent_block | solid_color",
      "background_hex": null
    },
    "animation": {
      "in_animation": "static | fade_in | popup | slide | typewriter",
      "out_animation": "static | fade_out | popup_out",
      "default_duration_ms": 200,
      "notes": "动画使用频率 (经常/偶尔/不用)"
    },
    "highlight_rule": {
      "is_used": true,
      "applied_to_categories": ["数字", "金句", "品牌词", "情绪词"],
      "method": "color_change | size_change | font_change | underline | popup | shake | combo",
      "highlight_color_hex": "#FFD700",
      "trigger_frequency": "高 | 中 | 低",
      "examples": ["XX词", "YY数字"]
    }
  },
  "aesthetic_judgement": {
    "overall_score_1to10": 8,
    "strengths": ["..."],
    "geek_signature": "极客号字幕美感的标志性特征",
    "differentiators_vs_generic": ["和泛广告字幕的差异点"]
  },
  "switching_observations": {
    "switch_method_dominant": "hard_cut | fade",
    "switch_alignment_to_speech": "字幕切换是否与口播停顿严格对齐？观察描述",
    "max_simultaneous_lines": 1,
    "max_chars_per_line_estimate": 18
  }
}

# 防幻觉
- 时间戳基于实际视频，不能编造
- 颜色 hex 用估算，无法精确则给"约 #XXXXXX"
- 字体只标"猜测"，不确定标 "unknown_modern_sans"
"""

def build_llm_call(comp_mp4, out_json):
    if out_json.exists(): return json.loads(out_json.read_text(encoding="utf-8"))
    import os
    from openai import OpenAI
    client = OpenAI(
        base_url=os.environ.get("LLM_PROXY_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.environ["LLM_PROXY_API_KEY"],
    )
    video_b64 = base64.b64encode(comp_mp4.read_bytes()).decode("utf-8")
    resp = client.chat.completions.create(
        model="gemini-3.1-pro-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": SUBTITLE_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
            ],
        }],
    )
    raw = resp.choices[0].message.content.strip()
    m = re.search(r'\{[\s\S]*\}', raw)
    obj = json.loads(m.group(0) if m else raw)
    obj["_usage"] = {"prompt": resp.usage.prompt_tokens, "completion": resp.usage.completion_tokens}
    out_json.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return obj

# ============ Phase 4: 后处理对比 ============
def match_subtitle_to_asr(subs, asr_segs):
    """计算字幕↔口播的匹配率 + 切换丝滑度"""
    if not subs or not asr_segs:
        return {"asr_text_match_rate": 0, "switch_alignment_rate": 0, "max_gap_ms": 0, "max_overlap_ms": 0}

    # 时间对齐：每条字幕找最重叠的 ASR 段
    aligned, lead_ms_list = 0, []
    for sub in subs:
        ss, se = sub["start_sec"], sub["end_sec"]
        best_overlap, best_asr = 0, None
        for a in asr_segs:
            overlap = max(0, min(se, a["end"]) - max(ss, a["start"]))
            if overlap > best_overlap:
                best_overlap, best_asr = overlap, a
        if best_asr and best_overlap > 0.3:
            aligned += 1
            lead_ms_list.append(int((ss - best_asr["start"]) * 1000))

    align_rate = aligned / len(subs)

    # 字幕切换点 vs ASR 句末点对齐
    sub_starts = sorted(s["start_sec"] for s in subs)
    asr_ends = sorted(a["end"] for a in asr_segs)
    switch_aligned = 0
    for ss in sub_starts:
        if any(abs(ss - ae) < 0.4 for ae in asr_ends): switch_aligned += 1
    switch_align_rate = switch_aligned / len(sub_starts) if sub_starts else 0

    # 时间空档 / 重叠
    sub_sorted = sorted(subs, key=lambda x: x["start_sec"])
    gaps, overlaps = [], []
    for i in range(len(sub_sorted)-1):
        diff = sub_sorted[i+1]["start_sec"] - sub_sorted[i]["end_sec"]
        if diff > 0: gaps.append(int(diff*1000))
        else: overlaps.append(int(-diff*1000))

    # 字幕文本是否逐字 (粗判：字符总数对比)
    sub_total_chars = sum(len(s["text"]) for s in subs)
    asr_total_chars = sum(len(a["text"]) for a in asr_segs)
    char_ratio = sub_total_chars / asr_total_chars if asr_total_chars else 0
    is_verbatim = 0.85 <= char_ratio <= 1.15  # 字数差 15% 内视为逐字

    return {
        "asr_alignment_rate": round(align_rate, 3),
        "switch_alignment_rate": round(switch_align_rate, 3),
        "subtitle_lead_ms_median": int(sorted(lead_ms_list)[len(lead_ms_list)//2]) if lead_ms_list else None,
        "subtitle_lead_ms_iqr": [int(sorted(lead_ms_list)[len(lead_ms_list)//4]), int(sorted(lead_ms_list)[len(lead_ms_list)*3//4])] if len(lead_ms_list) >= 4 else None,
        "max_gap_ms": max(gaps) if gaps else 0,
        "median_gap_ms": sorted(gaps)[len(gaps)//2] if gaps else 0,
        "max_overlap_ms": max(overlaps) if overlaps else 0,
        "subtitle_chars": sub_total_chars,
        "asr_chars": asr_total_chars,
        "char_ratio_sub_to_asr": round(char_ratio, 3),
        "is_likely_verbatim": is_verbatim,
        "avg_subtitle_duration_sec": round(sum(s["end_sec"]-s["start_sec"] for s in subs)/len(subs), 2),
    }

# ============ Pipeline ============
def process(video_name):
    vid = video_name.replace(".mp4","")
    src = MATERIALS / video_name
    comp_mp4 = COMP / f"{vid}.mp4"
    asr_json = ASR / f"{vid}.json"
    llm_json = LLM / f"{vid}.json"
    merged_json = MERGED / f"{vid}_subtitle.json"

    print(f"\n=== {vid} ===")
    print("[1] compress")
    compress(src, comp_mp4)

    print("[2] ASR")
    asr_obj = asr(comp_mp4, asr_json)
    print(f"    {len(asr_obj['segments'])} segments, {asr_obj['duration']:.1f}s")

    print("[3] LLM")
    llm_obj = build_llm_call(comp_mp4, llm_json)
    print(f"    {len(llm_obj.get('subtitles', []))} subtitles, tokens={llm_obj['_usage']}")

    print("[4] merge")
    metrics = match_subtitle_to_asr(llm_obj.get("subtitles", []), asr_obj["segments"])
    merged = {
        "video_id": vid,
        "duration_sec": asr_obj["duration"],
        "asr_segments": asr_obj["segments"],
        "subtitles_from_llm": llm_obj.get("subtitles", []),
        "style_codex": llm_obj.get("style", {}),
        "aesthetic_judgement": llm_obj.get("aesthetic_judgement", {}),
        "switching_observations": llm_obj.get("switching_observations", {}),
        "alignment_metrics": metrics,
        "_llm_usage": llm_obj.get("_usage", {}),
    }
    merged_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    ✓ {merged_json.name}")
    return vid

if __name__ == "__main__":
    # 串行跑（whisper 单卡 + LLM 大 prompt，避免 OOM）
    for s in SAMPLES:
        try:
            process(s)
        except Exception as e:
            print(f"✗ {s}: {e}")
    print(f"\n✅ done -> {MERGED}")
