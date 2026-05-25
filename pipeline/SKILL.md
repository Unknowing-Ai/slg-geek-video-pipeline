---
name: geek-replication-master
description: 极客号 AI 复刻视频 master pipeline。跨产品通用：输入产品配置 + 60s 脚本，5 步骤产出带配音/分镜/视频/字幕/多画幅的成片。
---

# Geek Replication Master Pipeline

> **核心定位**：把"极客号风格的 60s 买量视频"从手工创作变成 AI 流水线。**跨产品通用**：ROK / WGame / Samo / 任意新 SLG 都能跑。

## 你正在调用的是什么

一个 **5 步 + 1 配置** 的 AI 视频生产 pipeline：

```
[product_config.yaml]  ← 唯一跨产品入口（改 6 个字段定义新产品）
        │
        ▼
[round1] 脚本生成    → script.yaml (60s 文本 + 5 段位)
        │
        ▼
[round2-step1] 配音  → final_60s_mixed.mp3 (ICL 克隆音色 + BGM)
        │
        ▼
[round2-step2] 分镜  → storyboard.json (28-35 镜 · MAC 模块)
        │
        ▼
[round2-step3] 视频  → video_BGM完整版.mp4 (28-35 镜 · 配音 · BGM)
        │
        ▼
[round2-step3.5] 画幅适配 (待开发)  → video_{16x9,9x16,1x1}.mp4
        │
        ▼
[round2-step4] 字幕  → 终片 × N 画幅 (带字幕 mp4)
```

## 5 步 SKILL 索引

| Step | 路径 | 状态 | 入参 | 出参 |
|---|---|---|---|---|
| round1 脚本 | `01-脚本/SKILL.md` (5 prompt 组件在 `prompts/`) | ✅ v0.9.1 | product_brief | script.yaml |
| step1 配音 | `02-配音/SKILL.md` | ✅ v1.0 | script.yaml | final_60s_{raw,mixed}.mp3 |
| step2 分镜 | `03-分镜/SKILL.md` | ✅ v1.2 | script.yaml + product_config.yaml | storyboard.json + images/ |
| step3 视频 | `04-视频/SKILL.md` | ✅ v1.0 | storyboard.json + images/ + audio | video_BGM完整版.mp4 |
| step3.5 画幅 | `04.5-画幅/SKILL.md` | 📐 设计稿 | video_16x9.mp4 | video_{9x16,1x1}.mp4 |
| step4 字幕 | `05-字幕/SKILL.md` | ✅ v1.0 | video.mp4 + script.yaml + product_config.yaml | final_字幕版.mp4 |

## 跨产品入口：product_config.yaml

**新增一个产品 = 改这一个文件**。

```yaml
# 必填 6 字段
game_name: "万国觉醒"                                   # 品牌词
game_genre: "SLG / 4X 策略"
target_audience: "中国市场，男性 25-45，历史/军事爱好者"

part1_anchor: "古代文明纪实风格，文化角色一致"            # Part 1 视觉锚定（step2/step3）
part2_anchor: "卡通写实 3D RTS CG，蓝金主色调"           # Part 2 视觉锚定
part1_neg_extra: "非亚洲人，欧洲面孔，现代服饰"           # Part 1 负向词

# 可选字段
forbidden_language_neg: "latin letters, english characters, download button"
highlight_words_normal:                                # step4 黄高亮词典
  - "万国觉醒"
  - "霍去病"
  - "卫青"
  - "汉武帝"
  - "中式弓骑兵"
highlight_words_cta:                                   # step4 红高亮词典
  - "万国觉醒"
  - "现在下载"
  - "立即"
```

模板：`pipeline/04-视频/prompts/product_config_template.yaml`

## 部署模式：里程碑制半自动

**不是全自动一键跑**，是 5 个 checkpoint 各自审完才进下一步。理由：
- 每 step 输出物（脚本/分镜/视频/字幕）都需人审
- AI 不稳定（LLM 输出漂移、视频生成失败、ASR 误识别）
- 跑垃圾的概率非 0，需要 checkpoint 可回退

**工作流**：

```
1. 项目方：「给 X 产品做一条 AI 复刻」
2. Agent 读 master SKILL → 知道按 5 步走
3. Step 准备：
   a. 复制 product_config_template.yaml → 改 6 必填字段
   b. 调 round1 prompt 套件出 script.yaml
4. 进 step 循环：
   for step in [step1, step2, step3, step3.5, step4]:
       a. Agent 调用 step SKILL
       b. 输出 checkpoint 到桌面
       c. 等用户审 → 通过则下一步
       d. 不通过则 step 内迭代
5. 出多画幅终片，归档
```

## 跨 step 输入输出契约

```yaml
# Step 1 (配音) 契约
input:
  script.yaml:                                 # round1 输出
    segments: [{semantic_role, text, duration_target_sec, target_wpm}]
output:
  final_60s_raw.mp3                            # 干音
  final_60s_mixed.mp3                          # 加 BGM
  seg_times.yaml (待规范化)                     # 实际配音段位时间 ← step4 依赖

# Step 2 (分镜) 契约
input:
  script.yaml + product_config.yaml
output:
  storyboard.json:
    meta: {pivot_second, mac_summary, codex_modules_applied}
    shots: [{shot_id, segment, sequence_group_id, sequence_action, match_type_to_prev, visual_description, camera, asset_type, image_gen_prompt}]
  images/{shot_id}.png

# Step 3 (视频) 契约
input:
  storyboard.json + images/ + audio.mp3
output:
  videos/{shot_id}.mp4                         # 单镜
  {product}_BGM完整版.mp4                       # 拼接 + mux

# Step 3.5 (画幅) 契约 [待开发]
input:
  video_16x9.mp4 + product_config.yaml (aspect_targets)
output:
  video_{16x9,9x16,1x1}.mp4

# Step 4 (字幕) 契约
input:
  video.mp4 + script.yaml + product_config.yaml (highlight_words_*)
output:
  subtitle.ass
  {video}_字幕版.mp4
```

## 标准产物目录

```
pipeline/examples/{product_id}/
├── product_config.yaml                # 产品定义（唯一入口）
├── script.yaml                        # round1 输出
├── voice/
│   ├── final_60s_raw.mp3
│   └── final_60s_mixed.mp3
├── storyboard/
│   ├── storyboard.json
│   ├── storyboard.md (可读版)
│   └── images/
├── video/
│   ├── videos/{shot_id}.mp4
│   └── {product}_BGM完整版.mp4
├── aspect/                            # step3.5 输出
│   ├── video_16x9.mp4
│   ├── video_9x16.mp4
│   └── video_1x1.mp4
└── final/                             # step4 输出（终片）
    ├── final_16x9_字幕版.mp4
    ├── final_9x16_字幕版.mp4
    └── final_1x1_字幕版.mp4
```

## 跨产品最小可复用集

要在新产品（如某新 SLG）跑通整条 pipeline，最小修改清单：

| 文件 | 修改内容 | 工作量 |
|---|---|---|
| product_config.yaml | 改 6 必填字段 + highlight 词典 | 30 分钟 |
| script.yaml | 用 round1 prompt 跑出 60s 脚本 | 1-2 小时 |
| ICL voice 资产 | 准备 30s 目标音色样本（克隆用） | 30 分钟 |
| 动作姿态 keyframes（step2 可选） | 5-10 张角色动作 keyframe | 1 小时 |

**总耗时**：第一次新产品 4-6 小时；熟练后 2-3 小时。

## 已部署 examples

| 产品 | 路径 | 状态 |
|---|---|---|
| ROK 古代将军 v1 | `examples/古代将军/` | ✅ 完整 |
| ROK 古代将军 v2 | `examples/古代将军_v2/` | ✅ 完整 |
| ROK 古代将军 v3 | `examples/古代将军_v3/` | ✅ 完整（带 step4 字幕） |

## 教 Agent 跑通 pipeline 的 3 个原则

### 原则 1：master SKILL 是唯一入口

Agent 接到"做一条复刻视频"需求时，**第一件事读这个 SKILL**。不要让 agent 直接去找单 step SKILL，否则会跳步骤。

### 原则 2：里程碑制不是全自动

每 step 跑完必须 checkpoint 到桌面 + 等审。Agent 不要"一口气把 5 步跑完出最终片"，因为：
- step2 分镜不审 → step3 生成的 28 张图全是错的，浪费 ¥100+ API
- step3 视频不审 → step4 字幕白渲染
- 任何一 step 失误，往前回退成本越高

### 原则 3：跨产品入口只看 product_config.yaml

任何 step 的脚本里，**不准 hardcode 产品相关信息**（不能写"ROK Han Dynasty"，必须从 product_config.yaml 读 `game_name` / `part1_anchor`）。
违反这条 → pipeline 失去跨产品复用价值。

## 验证：跨产品跑通的最小测试

```
1. 复制 examples/古代将军_v3/product_config.yaml → examples/新产品/product_config.yaml
2. 改 6 必填字段为新产品的（game_name / part1_anchor / part2_anchor / ...）
3. 准备新产品的 60s script.yaml
4. 依次跑 step1 → step4
5. 通过条件：5 步全部不修代码就跑通
```

## 与 Phase 3+ 的衔接

| Phase | 范围 | 时间 |
|---|---|---|
| **当前 Phase 2 (Round 2)** | 脚本→视频→字幕 全流水线 | 5-8 周（已完成大部分） |
| Phase 3 剪辑 Agent | 精细剪辑 + 字幕样式表 + BGM 库 | 4-8 周 |
| Phase 4 发布 Agent | 上传 + 标签 + 时机 + 数据回流 | 2-3 周 |
| Phase 5 数据驱动 codex 自动迭代 | 月度 hit pattern mining → 自动改 codex | 持续 |

## 紧急联系

- **方法论文档**：`pipeline/round2-*/docs/方法论.md`
- **codex 系列**：`pipeline/03-分镜/codex-v2.1/`
- **字幕 codex**：`pipeline/05-字幕/极客字幕Codex-v1.0-候选.md`
- **跨产品 product_config 模板**：`pipeline/04-视频/prompts/product_config_template.yaml`
