---
name: geek-voice-bgm-codex
description: 把任意中文文案转成"极客号"KOL 风格的口播+BGM mp3。基于 65 条极客头部视频实测拆解，产出 voice_codex.yaml（WPM/段位语速/气口规则）和 bgm_codex.yaml（BPM/调性/混音规则），并提供端到端 pipeline：文案→ICL 克隆口播→demucs 抽 BGM→侧链混音→codex 自动评分。当用户要做 SLG 类抖音爆款视频的配音、或需要复刻特定 KOL 的语速节奏时使用。
version: "1.0"
---

# 极客号口播 + BGM Codex (Round 2 - Step 1)

## 用途

把一段中文文案（按段位结构 Hook/Background/Core_K/Ad_R/Selling/CTA）转成符合"极客号"风格的 60s 口播 mp3 + BGM 混音 mp3。

输出符合下列**实测量化规则**（基于 65 条极客头部样本，faster-whisper + Silero VAD + librosa）：

| 维度 | 量化规则 |
|---|---|
| **全局 WPM** | 中位 367（安全区 [337, 393]） |
| **段位语速** | Hook 386 > Background 385 > Ad_R 377 > Core_K 365 > Selling 364 > CTA 346 |
| **气口** | 全片气口总和 ≤ 1s（极客平均 0 气口） |
| **人声占比** | ≥ 0.95 |
| **BGM BPM** | 中位 112（前段 99-129 / 后段 129-185） |
| **混音 ducking** | 口播段 BGM 自动降 5.2dB |
| **段位 BGM 突变** | Core_K → Ad_R 起点必须黑屏 + boom + BGM 高能突变 |

## 输入

- 5 段中文文案（YAML 结构，参考 `script_60s_validate.yaml`）
- 段位标签（v0.9.1 codex 6 段位）
- 火山 ICL 克隆音色 `voice_id`（手动控制台训练 1 次即得）

## 输出

- `tts_output/seg{N}_{role}.mp3`：每段位独立 mp3
- `tts_output/final_60s.mp3`：纯口播版（已 silenceremove + atempo 后处理）
- `tts_output/final_60s_mixed.mp3`：含 BGM 侧链混音版

## 4 步流程

### Step A · 数据预处理（一次性，~30min）
对极客原视频 mp4 跑：
```bash
bash scripts/extract_audio.sh        # ffmpeg 抽 16k mono wav
python scripts/run_asr.py            # faster-whisper large-v3 word-level ASR
bash scripts/demucs_all.sh           # demucs 分离 vocals + no_vocals
```

### Step B · 出 codex（一次性，~15min）
```bash
python scripts/run_stats.py          # 跑 Silero VAD + 统计语速/气口/段位
python scripts/analyze_bgm.py        # librosa 跑 BPM/调性/突变/音量曲线
python scripts/write_bgm_codex.py    # LLM 总结成 bgm_codex.yaml
```

产物：`voice_codex.yaml` + `bgm_codex.yaml`

### Step C · 生成 60s 口播（每次新视频，~3min）
```bash
# 1. 改 script_60s_validate.yaml 的 segments[].text 为新文案
# 2. 跑 TTS
python scripts/tts_volc_icl.py <你的voice_id>
```

注意：`speed_ratio` 已按 codex 校准（基准 345 WPM，对应豆包 ICL 克隆音色）。每段位 speed_ratio 范围 1.00-1.12。

### Step D · BGM 混音 + 自动评分（每次新视频，~1min）
```bash
# 混音（侧链 ducking）
ffmpeg -i bgm_source.mp3 -i tts_output/final_60s.mp3 \
    -filter_complex "[0:a]volume=-6.6dB,aloop=loop=-1:size=2e9[bgm_loop]; \
                     [bgm_loop][1:a]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[bgm_duck]; \
                     [bgm_duck][1:a]amix=inputs=2:duration=shortest[out]" \
    -map "[out]" -c:a libmp3lame -b:a 192k final_60s_mixed.mp3

# 评分（自动用 ASR + VAD 复跑校验 codex）
python scripts/validate_tts.py
```

预期评分 5/5（WPM ∈ safe / 气口 ≤ 1s / 人声 ≥ 0.95 / 最长气口 ≤ 500ms / WPM ∈ [240, 430]）。

## 关键依赖

- Python 3.12 + `faster-whisper`, `demucs`, `librosa`, `openai`
- ffmpeg 6+
- GPU（faster-whisper / demucs 都能跑 CUDA，没 GPU 也能 CPU fallback）
- 火山引擎豆包 ICL（语音复刻 v2），api-key + cluster=volcano_icl
- LiteLLM Proxy（Gemini/Claude 用于 `write_bgm_codex.py`）

## 复用注意

- **样本边界**：65 有效样本来自 ROK/WGAME/Samo 三个产品的极客号视频。如换其他 KOL（同样需 demucs 分离 BGM + ICL 克隆），重跑 Step A-B 即可拿到该 KOL 的 voice/bgm codex
- **气口规则**：极客 = 0 气口。若 KOL 节奏更松，气口规则要重新拟合
- **BGM 选源**：当前用极客原视频的 no_vocals 轨（仅验证用，不商用）。商用需换 Epidemic Sound / 游戏厂商 BGM 库

## 与 Round 1 的关系

- Round 1（`prompts/`）：v0.9.1 脚本生成 prompt 套件（文案产出）
- Round 2 Step 1（本 skill）：脚本→口播+BGM mp3（语音产出）
- Round 2 Step 2-5：分镜图 → 视频 → 风格审核 → 剪辑包装（后续）
