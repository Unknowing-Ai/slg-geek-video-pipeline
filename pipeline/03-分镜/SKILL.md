---
name: geek-storyboard-pipeline
description: 把任意 60s 已配音脚本（含段位结构+口播文案）按极客视觉 codex-v2.1 的 12 模块规则转成 28-35 镜分镜表（含 sequence_group + 同动作多视角连贯）+ N 张 AI 配图（nano_banana_pro 主 + doubao-seedream fallback），输出图文混排 markdown + 桌面副本 + 飞书 docx。基于 76 条极客号视频拆解的 codex-v2.1（含 BIN/HMI/SCT/FLU 宏观 + MAC 匹配剪辑模块）。**跨产品通用**：每接一个新 SLG 产品只需先要资产清单（含动作姿态资产 ⭐ v1.2 新增 · 详见 prompts/asset_request_template.md）+ 产品配置（含 part1_anchor 文化锚定 ⭐ v1.2 新增 · 详见 prompts/product_config_template.yaml），其他流程不动。当用户要把脚本转成可投放分镜方案、需要 AI 生成游戏风格的演示配图、或需要把分镜方案沉淀成云文档时使用。
version: "1.2"
---

# 极客号分镜 Pipeline (Round 2 - Step 2)

## v1.2 升级要点（基于 Step 3 PoC 反馈）

1. **新增 MAC 模块（codex-v2.1）**：matched_ratio ≥ 70%，每段位强制 sequence_group，**「同动作多视角连贯」而非「同主题多瞬间」**
2. **新增 storyboard 字段**：`sequence_group_id` + `match_type_to_prev` + `sequence_action`（主体+持续动词）
3. **新增 product_config 字段**：`part1_anchor` + `part2_anchor` + `part1_neg_extra` + `forbidden_language_neg`，由宿主自定义文化/服装/时代锚定
4. **新增动作姿态资产要求**：每角色 3-5 张同角色多动作 keyframe（极客号视觉连贯性的关键）
5. **首帧图设计原则**：必须画「动作进行中」姿态（蹄子半抬、士兵正用力推），给视频生成明确运动方向

## 用途（跨产品通用）

把一段 60s 已配音脚本（v0.9.1 + voice_codex）按极客视觉 codex-v2.1 转成完整分镜方案：

- **28-35 镜分镜表**（每镜含 visual / camera / asset / emo / sequence_group / match_type / prompt · 贴近极客 ASL 1.6s）
- **28-35 张 AI 配图**（Part1 文生图 + Part2 图生图带**宿主产品**官方 reference + 动作姿态 keyframe）
- **图文混排 markdown**（含 codex 模块落地说明 + 后期合成清单）
- **桌面副本** + **飞书 docx**

输出符合 **codex-v2.1 12 模块**（v1.0 的 STR/EMO/PACE/SUB/CAM/BGM/META + v2.0 BIN/HMI/SCT/FLU + v2.1 MAC）。

**适用产品**：任意 SLG / 4X 策略游戏（已验证 ROK / WGAME / Samo 等公开 IP）。本 skill 与产品无关，每次接入新产品替换：
- **资产清单**（含动作姿态 ⭐ v1.2）
- **产品配置 part1_anchor / part2_anchor / forbidden_language_neg**（⭐ v1.2）

## 5 个核心工程决策（基于实测教训）

| 决策 | 为什么 |
|---|---|
| **生图模型用 nano_banana_pro**（Gemini 3 Pro Image）| 比豆包 seedream 4.5 在风格统一性、画面细节上更稳。v1 用 seedream 在 LOGO/汉字渲染上全部乱码 |
| **全图禁画文字 + 跨产品禁词**（字幕/花字/LOGO/数字/英文一律后期合成）| AI 生图渲染中文准确率 <10%。按投放地区配置 `forbidden_language_neg`（中国境内禁英文、海外英文区禁中文等） |
| **Part 2 用宿主官方资产 + 动作姿态 keyframe 做图生图 reference** | 从产品方资产库抓立绘和**动作姿态 keyframe**（v1.2 新增），让生图同 sequence_group 内多视角动作连贯 |
| **CTA 类镜头 fallback 到 doubao-seedream** | nano_banana_pro 的 Google 安全机制对"古代征服 / 多国家旗帜"敏感会拦截，doubao 没此限制 |
| **首帧图必须是「动作进行中」姿态** (v1.2 新增) | 给后续视频生成明确运动方向。静态站位 → 视频只能做镜头推拉；动作中姿态 → 视频能延续动作 |

## 🆕 新产品启动 SOP（关键，必读）

每接一个新产品，**第一步永远是跟宿主要资产 + 锚定文字**：

### Step 0 · 跟宿主要资产（v1.2 升级）

照 [`prompts/asset_request_template.md`](prompts/asset_request_template.md) 把模板请求**直接发给产品方 / 美术 owner**，6 类资产：
1. 主要英雄角色立绘 3-6 个（P0 必给）
2. **主要英雄角色动作姿态 keyframe 3-5 张/角色 ⭐ v1.2 新增**（P0，强烈建议）— 用于 Part 2 sequence_group 的多视角动作连贯生成
3. 主要兵种 / 怪物 / NPC 2-3 个（P1）
4. 代表性建筑/环境 1-2 张（P2）
5. LOGO / IP 标识 1 张（P2，后期合成用）
6. **文化/视觉锚定文字描述 ⭐ v1.2 新增**（P0，强制要）— 用于 product_config.yaml 的 part1_anchor / part2_anchor / forbidden_language_neg 字段填写

模板里还含：飞书 base / 云盘 / 网盘 / 微信 4 种提交方式 + 给宿主签字的清单。

**缺动作姿态 keyframe 的后果**：Part 2 sequence_group 必然降级为「同立绘 + 镜头推拉」的伪连贯（已实测教训）

### Step 1 · 整理 `manifest.json` 和 `product_config.yaml`

```json
// manifest.json
{
  "source": "feishu_base",  // 或 "local"
  "base_token": "...",
  "table_id": "...",
  "table_rev": 658,
  "assets": {"角色名-1": "file_token或本地路径", ...}
}
```

```yaml
# product_config.yaml (v1.2 升级 · 7 字段)
game_name: "<产品名>"
game_genre: "<品类>"
game_visual_style: "<一句话视觉风格描述>"
pivot_keyword_hint: "<转折句关键词>"
target_audience: "<目标受众>"
# v1.2 新增 4 字段（由宿主基于"文化/视觉锚定文字描述"填写）
part1_anchor: "<Part 1 文化/服装/时代锚定，如 ROK='Han Dynasty Asian characters' / WGAME='modern NATO military' / Samo='Western medieval fantasy'>"
part2_anchor: "<Part 2 游戏画风锚定，默认从 game_visual_style 推断>"
part1_neg_extra: "<Part 1 排除元素，与 anchor 互补>"
forbidden_language_neg: "<按投放区域，中国境内='latin letters, english characters, download'>"
```

### Step 2 · 写 `shot_to_refs_mapping.json`（v1.2 升级 · 立绘+动作）

分镜表跑完后，按每个 Part 2 镜头映射到 reference 资产（立绘+动作 keyframe）：

```json
// v1.2 推荐结构
{
  "AdRev-01": {"立绘": ["099-霍去病"], "动作": ["099-霍去病_action_charge"]},
  "AdRev-02": {"立绘": ["099-霍去病"], "动作": ["099-霍去病_action_charge"]},
  "Sell-03": {"立绘": ["09-诸葛连弩T5"], "动作": ["09-诸葛连弩T5_action_volley"]}
}
// 同 sequence_group 内的多个镜头共享同一 action keyframe，让模型理解连续动作
// v1.1 旧结构（仅立绘）仍兼容
```

### Step 3 · 跑 pipeline 6 步

详见下方 "6 步 Pipeline"。

## 6 步 Pipeline（产品无关）

```bash
# Step 0 · 准备宿主资产 + 配置（人工 ~30 min）
#   manifest.json + product_config.yaml + shot_to_refs_mapping.json

# Step A · 脚本 → 分镜表（LLM, ~1 min, ~¥0.5）
python scripts/01_gen_storyboard.py <script.yaml> <product_config.yaml> <out_dir>

# Step B · 拉宿主资产 → 上传 liclick（~1 min, 免费）
python scripts/02_extract_refs.py <manifest.json> <out_dir>

# Step C · 提交 25 张图生成任务（~30s 提交 / 8 min 生成, ~¥30）
python scripts/03_genimg.py <out_dir>/storyboard.json <out_dir>/asset_map.json <mapping.json> <product_config.yaml> <out_dir>

# Step D · poll + 下载（含失败 fallback, ~8 min, fallback 额外 ~¥1）
python scripts/04_poll_download.py <out_dir>/task_ids.json <out_dir>/storyboard.json <out_dir>

# Step E · 整合 markdown + 桌面副本（~5s, 免费）
python scripts/05_integrate.py <out_dir> [desktop_dir]

# Step F · 飞书 docx 创建 + 25 图嵌入（~3 min, 免费）
python scripts/06_upload_feishu.py <out_dir> "<docx 标题>"
```

## 验证产物（ROK 案例 - 唯一已跑通的样本）

[`examples/古代将军/`](examples/古代将军/) 是用 60s 脚本《古代将军最大的敌人不是敌军 + ROK 调度》跑出来的完整产物：

| 指标 | 实测 | codex 目标 | 通过 |
|---|---|---|---|
| 分镜数 | 25 | 24-28 | ✓ |
| Pivot 比例 | 45% | [40%, 50%] | ✓ |
| Part1/Part2 ASL Δ | <0.5s | <0.5s | ✓ |
| Hook 前 3s 切刀 | 2 | [1, 3] | ✓ |
| 视觉锚点命中 | Yes | ≥80% | ✓ |
| Part 2 主体延续 | Yes (霍去病) | Same_Character | ✓ |
| 中文文字准确性 | 100% (后期合成) | 100% | ✓ |
| **总分** | **8/8** | — | ✅ |

**新产品复用**：同样 8 个指标用同样方法验收（换成对应产品的角色/兵种 reference 即可）。每接入一个新产品建议建一份 `examples/<产品名>/` 沉淀产物。

## 关键依赖

- Python 3.12 + `openai` + `pyyaml` + lark-cli + atlas-skillhub
- LiteLLM Proxy (`gemini-3.1-pro-preview` for 分镜表生成)
- kling + doubao-seedance 视频生成 (liclick via atlas-skillhub gateway):
  - 主模型: `nano_banana_pro` (Gemini 3 Pro Image)
  - Fallback: `doubao-seedream-4-5-251128`
- 飞书 lark-cli (`base / docs / drive`)

## 复用注意

- **codex 边界**：codex-v2.1 基于 76 条**极客号**视频。如要复刻其他 KOL（非极客号），需先跑 Round 2a 重新拆解 → 出新 codex
- **跨产品资产**：每次接新产品**必须找宿主要资产**（见 [`prompts/asset_request_template.md`](prompts/asset_request_template.md)），否则 Part 2 生图风格走样
- **后期合成**：所有中文（字幕/花字/LOGO）必须由剪辑师后期添加，AI 图不含任何文字
- **成本估算**：单条 60s 脚本约 ¥30-35（25 张图 × ~¥1.2 nano_banana_pro）

## 与 Round 2 其他 Step 的关系

- **Round 1**（`prompts/`）：v0.9.1 脚本生成 prompt 套件
- **Round 2 Step 1**（[`02-配音/`](../02-配音/)）：脚本 → 60s 口播 + BGM mp3
- **Round 2a**（[`codex-v2.1/`](./codex-v2.1/)）：76 视频拆解 → codex-v2.1 + 3 条样本 MAC 验证 → codex-v2.1
- **Round 2 Step 2**（本 skill v1.2）：脚本 → 28-35 镜分镜表 + N 张 AI 配图（**跨产品通用 + MAC 序列组**）
- **Round 2 Step 3**（[`04-视频/`](../04-视频/)）：分镜方案 → 60s 视频成片（**跨产品通用 + 5 条铁律**）
- **Round 2 Step 4-5**（未启动）：成片 → 字幕音轨合成 → 风格审核
