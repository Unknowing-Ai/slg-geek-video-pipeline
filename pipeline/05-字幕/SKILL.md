---
name: geek-subtitle-pipeline
description: 用极客字幕 codex 给已配音视频自动渲染字幕（跨产品通用）。输入 mp4 + 原始脚本 yaml + product_config.yaml，输出带字幕 mp4。
---

# Geek Subtitle Pipeline (Round 2 · Step 4)

> 极客号字幕复刻：从 codex 抽取 → 工程渲染的端到端 pipeline。

## 核心定位

字幕是"画面服务口播"链路的最后一环。前 3 步（脚本/配音/视频/分镜）保证画面和声音对齐，字幕保证**口播信息的视觉冗余**。

## 三大铁律

字幕必须满足（PoC 5 条样本验证 4/5 一致）：

1. **跟口播高度匹配** — 字幕文本 = 原始脚本逐字（**禁止用 ASR 出文本**，因为 ASR 在 TTS 音质 + 军事/品牌专业词上误识率高，会把"匈奴"识别成"凶奴"、"万国觉醒"识别成"万国决心"）
2. **切换无缝丝滑** — hard_cut + 严格踩段位时间戳，不淡入淡出（CTA 段位除外）
3. **美观大方** — 思源黑体 Bold + 白字 + 黑描边 + 阴影 + 关键词高亮（详见 codex）

## 输入契约

```yaml
inputs:
  video: <带配音的 mp4>            # e.g. 04-视频/v3_full/古代将军_v3_BGM完整版.mp4
  script: <原始口播 script.yaml>    # e.g. 02-配音/script_60s_validate.yaml
  product_config: <product.yaml>   # 含 highlight_words_normal/cta、game_name 等
  segment_times: <yaml>            # 各段位在视频内的起止时间（s）
```

## 段位时间映射规则（关键）

**不要用脚本里的 duration_target_sec**（那是理想值）。**要用实际配音音轨的段位时间**。

```python
# 例：raw 配音 46.15s，mixed.mp3 (含 BGM) 39.21s → ratio 0.85
# 每段位 = raw_segment_dur × ratio
SEG_TIMES_IN_VIDEO = {role: (raw_dur × ratio_累加, ...)}
```

## 输出契约

```
{out_dir}/
├── subtitle.ass                          # ASS 字幕源文件（可独立编辑/调样式）
├── {video_name}_字幕版.mp4                # 烧字幕终片（H.264/AAC）
└── _asr_validation/                      # 可选：whisper ASR 出文本，比对脚本验证一致性
```

## Pipeline (4 阶段)

### Phase 1: 读脚本 + 段位时间映射

```python
script = yaml.safe_load(script_yaml)
for seg in script["segments"]:
    seg_start, seg_end = SEG_TIMES_IN_VIDEO[seg["semantic_role"]]
```

### Phase 2: 段内切句

```
切句规则:
1. 先按中文标点切（，。？！,.?!）— 标点用于切分位置定位
2. 单句仍 >22 字 → 按字数硬切（safety net）
3. 段内按各句字数比例分配时间（确保段位总时长精准对齐）
4. ⚠️ 剥离每条字幕的【尾部】标点（，。？！、；：）— 极客字幕实测末尾无标点
   保留句中并列符号"、"（如"冻死、饿死、迷路掉队"去掉读不通）
```

### Phase 3: 高亮规则（按段位）

```yaml
normal_segment (Hook/CoreK/AdRev/Sell):
  color: "#FFD700"  # 金黄
  applied_to:
    - 数字 (10万 / 3千 / 90%)
    - 武将/历史人名
    - 品牌词
    - 金句关键词

cta_segment:
  color: "#FF0000"  # 红
  font_override: impact_style + italic
  font_size_override: +50%  # large
  animation: popup (fad 150ms)
  applied_to: 高频触发 (现在 / 下载 / 立即 / 品牌名)
```

### Phase 4: .ass 生成 + ffmpeg burn

```ass
[V4+ Styles]
Style: Normal, Source Han Sans SC, 96, &H00FFFFFF, _, &H00000000, _, 1, 0, 0, 0, 100, 100, 4, 0, 1, 5, 3, 2, 40, 40, 110, 1
Style: CTA, Source Han Sans SC Heavy, 144, &H00FFFFFF, _, &H00000000, _, 1, 1, 0, 0, 100, 100, 6, 0, 1, 7, 4, 2, 40, 40, 120, 1
```

关键字段（1080p 基准）：
- **Fontsize 96 (Normal) / 144 (CTA)** — 约 8.9% / 13.3% 屏高，PoC v3 验证清晰度足
- **Outline 5 / 7** — 黑描边足够厚，复杂背景仍能看清
- **Shadow 3 / 4** — 轻阴影增加层次
- **MarginV 110 / 120** — 距底部 ≈ 10% 屏高，避开播放器进度条遮挡区
- **Spacing 4 / 6** — 字符间距，避免黏连
- **Bold=1 / Italic=1 (CTA)**

```bash
ffmpeg -i video.mp4 -vf "subtitles=subtitle.ass" -c:v libx264 -crf 20 -c:a copy out.mp4
```

## 跨产品适配

字幕样式 codex 全产品通用（位置/字体/颜色/切换）。需要按产品定制的是：

```yaml
# product_config.yaml 字段
highlight_words_normal:        # 黄高亮词典
  - "{game_name}"              # e.g. "万国觉醒" / "万龙觉醒"
  - <核心武将/角色名>            # 各产品列 5-10 个
  - <高频品类词>
  - <数字 pattern (\d+万, \d+%)>

highlight_words_cta:           # 红高亮词典
  - "{game_name}"
  - "下载" / "现在" / "立即" / "免费"
  - <产品 CTA 文案核心词>

subtitle_segment_overrides:    # 可选：覆盖特定段位
  CTA:
    font: "Source Han Sans SC Heavy"
    size_multiplier: 1.5
```

## 字体依赖

```bash
# 必装：思源黑体 SC (Bold + Heavy)
mkdir -p ~/.fonts
cd ~/.fonts
curl -L -o SourceHanSansSC-Bold.otf https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf
curl -L -o SourceHanSansSC-Heavy.otf https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Heavy.otf
fc-cache -fv ~/.fonts
```

降级字体（系统自带）：`WenQuanYi Zen Hei`（不推荐，清晰度不足）。

## 验证清单

| 检查项 | 目标 | 工具 |
|---|---|---|
| 字幕文本 = 脚本逐字 | 100% | diff |
| 字幕段位时间 = 配音段位时间 | ±200ms | ffprobe + 段位映射表 |
| 单行字数 | ≤22 字 | 脚本统计 |
| Hard_cut 严格踩句末 | 100% | 看片 |
| 高亮词命中 | 关键词全部命中 | 看片 |
| CTA 段位样式生效 | 大字 + 红 + popup | 看片 |
| 字体清晰度 | 思源黑体 Bold | ffprobe / fc-list |

## 反模式（禁止）

- ❌ 用 Whisper ASR 出文本当字幕源 — 错别字太多（PoC 实测：万国觉醒→万国决心、匈奴→凶奴、冻死→动死）
- ❌ 用 LLM 时间戳 — Gemini 多模态有归一化 bug（PoC 实测：1/5 视频时间戳压成 0-0.09s）
- ❌ 字幕用 fade_in/fade_out 默认动画 — 极客号都是 hard_cut，淡入会拖累节奏
- ❌ 字幕字号小 (<6% 屏高) — 移动端看不清
- ❌ 单行 >25 字 — 移动端要分两行，破坏底边稳定
- ❌ 字幕末尾保留标点（"？" "，" "。"）— 视觉冗余，极客字幕实测一律剥离

## 已知工程坑

1. **字体未装会 fallback 到等宽字体**（视觉很糟）— 务必先验证 `fc-list | grep "Source Han"`
2. **ass 路径中文/空格**需 escape — 用 `:` → `\:`
3. **CRF=20 字幕清晰度足**，更低（如 23）字幕边缘会糊
4. **CTA segment_times 计算误差 ±100ms** — 大问题：CTA 字幕错位影响转化体验，必须精准对齐

## 输出示例

参考：`step2-端到端-v3字幕/古代将军_v3_字幕版_V3.mp4`（39.16s · 65MB · 26 字幕 · 5 段位）

## 相关 SKILL

- **上游 step3**: `04-视频/SKILL.md` 出带配音的 mp4
- **下游 step3.5 (待开发)**: `04.5-画幅/SKILL.md` 字幕渲染前/后做 9:16 / 1:1 / 16:9 适配
- **依赖 codex**: `极客字幕Codex-v1.0.md`
- **依赖脚本**: `02-配音/script_*.yaml`
