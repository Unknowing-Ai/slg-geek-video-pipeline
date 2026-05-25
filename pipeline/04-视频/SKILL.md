---
name: geek-video-pipeline
description: 把 Round 2 Step 2 输出的 25-35 镜分镜方案（含首帧图）按极客视觉 codex-v2.1 + 视频生成 5 条铁律转成 60s 连贯成片。pipeline 含 first_frame 视频生成（kling Part1 + seedance Part2）、按 ASL 严格裁切、Hard_Cut 拼接、桌面/飞书产出。基于 PoC「汉军行军 3 镜连贯组」验证，输出符合「动作连续多视角 + 主体内部动态 + 人种/服装统一 + 禁英文 + 训练资产留口」5 条铁律。**跨产品通用**：每接入新产品按宿主提供的【动作姿态资产清单】参数化（prompts/asset_request_template_v2.md）。当用户要把分镜方案转成可投放 60s 视频、需要连续多视角的动作镜头组、或要把视频成片沉淀回飞书云盘时使用。
version: "1.0"
---

# 极客号视频生成 Pipeline (Round 2 - Step 3)

## 用途（跨产品通用）

把 Round 2 Step 2 输出的 25-35 镜分镜表（含 storyboard.json + 首帧 PNG/JPG）转成完整 60s 视频成片：

- **每镜 1 个 first_frame 视频片段**（4-5s，按 storyboard.duration 裁切到目标 ASL）
- **完整 60s mp4**（Hard_Cut 拼接，符合 BIN-03 + MAC「动作连续多视角」）
- **桌面副本** + **飞书云盘**

输出符合 **codex-v2.1 12 模块**，重点 MAC（匹配剪辑）和 BIN（二分结构）。

**适用产品**：任意 SLG / 4X 策略游戏（已验证 ROK / WGAME / Samo 等公开 IP）。本 skill 与产品无关。

## 5 条视频生成铁律（基于 PoC 实测教训）

| 铁律 | 为什么 | 落地方式 |
|---|---|---|
| **铁律 1：动作连续多视角** | matched cut 不是「同主题不同瞬间」，是「同一持续动作的不同机位」。骑兵冲锋正面→战马近景→冲锋侧面 ✓；运粮全景→冰冻骑兵特写→粮草地图（同主题但不同动作）✗ | storyboard 每个 sequence_group 内必须共享同一持续动作 + 不同机位 |
| **铁律 2：主体内部动态** | 模型对「轮子陷泥」的默认理解是「静态轮子图 + 镜头推近」，缺动态感。必须显式描述主体动作循环 | 每镜 video_prompt 必须含主体动作描述（轮子转/马蹄抬落/士兵推动/呼气/咀嚼），不能只描述场景 |
| **铁律 3：人种 + 服装统一** | nano_banana_pro 默认在「古代战争」会混入欧美面孔。Part 1 历史素材必须文化统一 | prompt 强约束「fully Asian East Asian Chinese / authentic Han Dynasty armor」+ NEG「non-asian people, european faces, caucasian, modern clothing」 |
| **铁律 4：禁英文 / Logo / Download** | 中国境内投放素材禁英文。CTA 段不能出现「Download」「Click Here」等英文按钮，全部用后期中文合成 | NEG 加「latin letters, english characters, download button」；CTA 段图生成只画画面，按钮由后期合成 |
| **铁律 5：训练资产留口** | Part 2 游戏画面与游戏内容不一致的根本原因是宿主提供的资产只有静态立绘，缺多动作姿态。模型只会复制立绘姿势 | 跟宿主要资产时新增【动作姿态资产】栏（同一角色多个 keyframe），用于 sequence_group 的多视角生成 |

## 模型分工（Part 1 vs Part 2）

| 段位 | 主模型 | 时长 | 理由 |
|---|---|---|---|
| Part 1 (Hook / CoreK) | **kling-v2-5-turbo** | 5s | 纪实风格稳定，运动语义理解强 |
| Part 2 (AdRev / Sell / CTA) | **doubao-seedance-2-0-260128** | 4s | 游戏 CG 特效细节强，4s 起步贴近 ASL |
| Fallback | **kling-v2-5-turbo** | 5s | seedance 偶发安全拦截（多文明/旗帜），切 kling 救回 |

## 5 维分析框架（reproducible）

1. **运动强度**：微动级 / 写实级 / 夸张特效级（跨模型语义化分级）
2. **镜头运动**：Static / Zoom_In / Zoom_Out / Pan / Mixed（复用 storyboard.camera）
3. **运动-音轨一致性**：与口播+BGM 节奏对齐
4. **纹理风格一致性**：Part1=纪实 / Part2=游戏CG
5. **时长严格匹配 ASL**：视频长度 = storyboard.duration（ffmpeg 取中段裁切）

**2 条硬约束（写进每个 prompt）**：
- 禁转场（无 dissolve/wipe/cut-to-black，纯 Hard_Cut）
- 禁气口（连续运动，无人为停顿，连续动作循环）

## 5 步 Pipeline（产品无关）

```bash
# Step 0 · 准备 Step 2 产物（人工 0 min，已有）
#   storyboard.json + 25-35 张首帧 PNG/JPG

# Step A · 压缩首帧图（PNG > 1MB 触发 atlas-skillhub HTTP 413，必须压成 JPG <1MB）
ffmpeg -y -i <each.png> -vf "scale='min(1920,iw)':-2" -q:v 4 <each.jpg>

# Step B · 上传首帧到 liclick（串行，并发 4 会 502，~1 min × 25-35）
python scripts/01_upload_frames.py <storyboard.json> <img_dir> <out_dir>

# Step C · 提交视频生成任务（Part1=kling Part2=seedance，并发 2，~30s 提交）
python scripts/02_gen_video.py <storyboard.json> <out_dir>/frame_assets.json <out_dir>

# Step D · poll + 下载（每镜 ~3-8 分钟生成，失败 fallback 到 kling）
python scripts/03_poll_download.py <out_dir>/video_tasks.json <out_dir>

# Step E · ffmpeg 按 ASL 裁切 + Hard_Cut 拼接 60s（~30s）
python scripts/04_cut_concat.py <storyboard.json> <out_dir> [desktop_dir]
```

## 验证产物（ROK 案例）

[`examples/古代将军/`](examples/古代将军/) 是 Step 2 产出的 34 镜方案（古代将军 + ROK 调度）按本 skill 跑出的 61.09s 成片。

PoC 验证产物 `poc_action/` 用 3 镜「汉军行军」动作连贯组验证了 5 条铁律。

| 指标 | 实测 v2 | 极客中位数 | 通过 |
|---|---|---|---|
| 总时长 | 61.09s | 49s | ✓ 设计 60s |
| 镜头数 | 34 | ~29 | ✓ +17% |
| 整体 ASL | 1.80s | 1.6s | ✓ |
| **matched_ratio** | **84%** | **82%** | ✓ |
| **最大序列组** | **14 镜** | **12 镜** | ✓ |
| Hook ASL | 1.67s | 1.61s | ✓ |
| CoreK ASL | 1.57s | 1.61s | ✓ |
| Pivot ratio | 45% | 46% | ✓ |
| 人种统一性 | Asian only | — | ✓ |
| 禁英文 | 100% | — | ✓ |
| **总分** | **9/9** | — | ✅ |

## 关键依赖

- Python 3.12 + `openai` + ffmpeg/ffprobe + lark-cli + atlas-skillhub
- liclick（via atlas-skillhub gateway）:
  - 主模型 Part 1: `kling-v2-5-turbo`
  - 主模型 Part 2: `doubao-seedance-2-0-260128`
  - Fallback: `kling-v2-5-turbo`
- 飞书 lark-cli（drive + docs）

## 跨产品复用注意

- **5 条铁律是 codex 层**：与产品无关
- **跨产品资产升级**：每次接入新产品**必须找宿主要[动作姿态资产]**（详见 [`prompts/asset_request_template_v2.md`](prompts/asset_request_template_v2.md)），否则 Part 2 序列组无法做多视角延续
- **后期合成**：所有中文字幕 / Logo / Download 按钮必须由剪辑师后期添加，AI 视频不含任何文字
- **成本估算**：单条 60s 视频约 ¥80-120（25-35 个视频 × ~¥3-4 kling/seedance），高于 Step 2 生图（~¥30）

## 与 Round 2 其他 Step 的关系

- **Round 1**：v0.9.1 脚本生成 prompt 套件
- **Round 2 Step 1**：脚本 → 60s 口播 + BGM mp3
- **Round 2a**：76 视频拆解 → codex-v2.1 + 3 条样本 MAC 拆解 → codex-v2.1
- **Round 2 Step 2**：脚本 → 25-35 镜分镜表 + AI 配图
- **Round 2 Step 3**（本 skill）：分镜方案 → 60s 视频成片（跨产品通用）
- **Round 2 Step 4-5**（未启动）：成片 → 字幕音轨合成 → 风格审核
