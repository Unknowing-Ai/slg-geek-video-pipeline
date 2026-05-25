"""
Step 4 · 03 - V2 字幕：直接用原始口播脚本（消灭错别字）+ 加大字号

输入: mp4 + 原始 script.yaml
处理:
  1. 读 script.yaml 5 段口播文本 + 各段时长
  2. 按 mixed.mp3 段位时间（scaled × 0.85）映射到视频时间
  3. 段内按标点切句 → ≤22 字/行
  4. 段内按字数比例分配每条字幕时间
  5. 字号 96/144、CTA 段位 impact_style + popup + 红高亮关键词
  6. ffmpeg burn

输出: {out_dir}/古代将军_v3_字幕版_V2.mp4
"""
import yaml, subprocess, re
from pathlib import Path

V3 = Path("pipeline/04-视频/v3_full/古代将军_v3_BGM完整版.mp4")
SCRIPT = Path("pipeline/02-配音/script_60s_validate.yaml")
OUT_DIR = Path("pipeline/05-字幕/step2-端到端-v3字幕")
ASS = OUT_DIR / "subtitle_V4.ass"
FINAL = OUT_DIR / "古代将军_v3_字幕版_V4.mp4"

# v3 mixed.mp3 段位时间（基于 SEG_AUDIO_MIXED 计算）
SEG_TIMES = {
    "Hook_Counter_Intuitive": (0.00, 3.53),   # 4.152s × 0.85
    "Core_Knowledge": (3.53, 19.13),          # 18.36s × 0.85
    "Ad_Reversal": (19.13, 25.39),            # 7.368s × 0.85
    "Selling_Point": (25.39, 34.16),          # 10.32s × 0.85
    "CTA": (34.16, 39.21),                    # 5.952s × 0.85
}

# ============ Phase 1: 读脚本 ============
script = yaml.safe_load(SCRIPT.read_text(encoding="utf-8"))
print(f"[1] 读脚本: {len(script['segments'])} 段")

# ============ Phase 2: 段内按标点切句 ============
def split_segment(text, max_chars=22):
    """按标点优先切，超长再按字数硬切"""
    # 标点分割（保留标点附给前句）
    parts = re.split(r'([，。？！,.?!])', text)
    # 合并标点回前句
    merged = []
    i = 0
    while i < len(parts):
        if i+1 < len(parts) and parts[i+1] in '，。？！,.?!':
            merged.append(parts[i] + parts[i+1])
            i += 2
        else:
            if parts[i].strip():
                merged.append(parts[i])
            i += 1
    # 长句再硬切
    out = []
    for p in merged:
        p = p.strip()
        if not p: continue
        if len(p) <= max_chars:
            out.append(p)
        else:
            # 按 max_chars 硬切
            for k in range(0, len(p), max_chars):
                out.append(p[k:k+max_chars])
    # 剥离每条字幕的尾部标点（极客字幕实测：句末无标点）
    out = [re.sub(r'[，。？！,.?!、；;：:]+$', '', x).strip() for x in out]
    out = [x for x in out if x]
    return out

# ============ Phase 3: 段内按字数比例分时 ============
subs = []  # (start, end, text, segment_name)
for seg in script["segments"]:
    role = seg["semantic_role"]
    text = seg["text"]
    if role not in SEG_TIMES:
        continue
    seg_start, seg_end = SEG_TIMES[role]
    seg_dur = seg_end - seg_start
    lines = split_segment(text, max_chars=22)
    total_chars = sum(len(l) for l in lines) or 1
    t = seg_start
    for line in lines:
        line_dur = seg_dur * len(line) / total_chars
        subs.append((t, t + line_dur, line, role))
        t += line_dur
print(f"[2] 切完 {len(subs)} 条字幕")

# ============ Phase 4: 高亮规则 ============
# Normal 段位：黄高亮 #FFD700（BGR: 00D7FF）
# CTA 段位：红高亮 #FF0000（BGR: 0000FF）
NORMAL_HIGHLIGHT = ["万国觉醒", "霍去病", "卫青", "吕布", "汉武帝", "匈奴", "10万", "3千", "90%", "中式弓骑兵", "降维"]
CTA_HIGHLIGHT = ["万国觉醒", "现在下载", "下载", "现在", "立即", "免费", "名将", "征服"]

def apply_hl(text, is_cta):
    color = r"{\c&H000000FF&}" if is_cta else r"{\c&H0000D7FF&}"  # 红 / 金黄
    reset = r"{\c&H00FFFFFF&}"
    words = CTA_HIGHLIGHT if is_cta else NORMAL_HIGHLIGHT
    # 按词长降序避免短词先匹配（如"现在"先于"现在下载"）
    for w in sorted(set(words), key=len, reverse=True):
        if w in text:
            text = text.replace(w, f"{color}{w}{reset}", 1)
    return text

# ============ Phase 5: 生成 .ass ============
def to_ass_time(t):
    h, t = divmod(t, 3600); m, t = divmod(t, 60); s = int(t); cs = int(round((t-s)*100))
    if cs >= 100: cs = 99
    return f"{int(h)}:{int(m):02d}:{s:02d}.{cs:02d}"

# 字号加大: Normal 96 (≈8.9% 屏高), CTA 144 (≈13.3%)
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,Source Han Sans SC,96,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,4,0,1,5,3,2,40,40,110,1
Style: CTA,Source Han Sans SC Heavy,144,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,1,0,0,100,100,6,0,1,7,4,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

lines_out = []
for start, end, text, role in subs:
    is_cta = role == "CTA"
    style = "CTA" if is_cta else "Normal"
    text_hl = apply_hl(text, is_cta)
    if is_cta:
        text_hl = r"{\fad(150,150)}" + text_hl
    lines_out.append(f"Dialogue: 0,{to_ass_time(start)},{to_ass_time(end)},{style},,0,0,0,,{text_hl}")

ASS.write_text(ASS_HEADER + "\n".join(lines_out) + "\n", encoding="utf-8")
print(f"[3] .ass: {ASS}")

# ============ Phase 6: ffmpeg burn ============
print("[4] ffmpeg burn")
ass_escaped = str(ASS).replace(":", r"\:").replace("'", r"\'")
cmd = ["ffmpeg","-y","-i",str(V3),
       "-vf", f"subtitles={ass_escaped}",
       "-c:v","libx264","-pix_fmt","yuv420p","-preset","fast","-crf","20",
       "-c:a","copy", str(FINAL)]
r = subprocess.run(cmd, capture_output=True, text=True)
if FINAL.exists():
    size_mb = FINAL.stat().st_size // 1024 // 1024
    print(f"\n✅ {FINAL.name} | {size_mb}MB")
    print(f"路径: {FINAL}")
else:
    print(f"✗ ffmpeg failed:\n{r.stderr[-500:]}")
