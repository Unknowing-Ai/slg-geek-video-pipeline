# SLG 极客号 AI 视频流水线

> 给 AI Agent 装一套"工作手册"，Agent 接到一句话就能从**写脚本**到**出带字幕成片**全自动跑完。

---

## 这是什么

不是命令行工具。是 7 个 SKILL（markdown 文件）+ 配套 scripts/codex/prompts，告诉 AI Agent 怎么按极客号买量视频的方法论一步步出 60 秒成片。

```
你给 Agent 一句话:
"用 examples/古代将军/product_config.yaml 跑一遍极客号 AI 视频流水线"
                              ↓
Agent 自动按 SKILL 走 5 步:
  Step 1 写脚本 (LLM)       → script.yaml          → 你审 → 继续
  Step 2 配音 (火山 ICL)    → final_60s.mp3        → 你审 → 继续
  Step 3 分镜 (LLM+生图)    → storyboard + 28 PNG  → 你审 → 继续
  Step 4 生成视频 (kling/seedance) → 28 mp4 + 拼接 → 你审 → 继续
  Step 5 上字幕 (codex+ass) → 最终带字幕 mp4       ← 出片
                              ↓
            60s 带字幕、带配音、带 BGM 成片
```

**成本/时间**：1 小时 / ~¥100 API 费 / 5 个 checkpoint 等审。
**对比传统人工**：1 周 / ¥5000-15000 / 编剧+配音+剪辑 3 人。

---

## 新人 0→1 部署（5-15 分钟）

### 第 1 步 · 装工具

```bash
# Agent 容器
npm install -g @anthropic-ai/claude-code

# Python 库
pip install openai faster-whisper jieba pyyaml

# ffmpeg
brew install ffmpeg                # Mac
sudo apt install ffmpeg            # Linux
choco install ffmpeg               # Windows
```

### 第 2 步 · 下载本仓库

```bash
git clone https://github.com/Unknowing-Ai/slg-geek-video-pipeline
cd slg-geek-video-pipeline
```

### 第 3 步 · 装 SKILL 给 Agent ⭐ 关键

```bash
bash setup.sh
```

这一步把 `pipeline/` 下 7 个 SKILL.md 复制到 `.claude/skills/`。Claude Code 启动时扫描这个目录，把所有 SKILL 装进 Agent 的"工具箱"。

**没跑这步 = Agent 看不到 SKILL = 自运转失败**。

### 第 4 步 · 装思源黑体（字幕用）

```bash
mkdir -p ~/.fonts && cd ~/.fonts
curl -L -o SourceHanSansSC-Bold.otf \
  https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf
curl -L -o SourceHanSansSC-Heavy.otf \
  https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Heavy.otf
fc-cache -fv ~/.fonts
```

### 第 5 步 · 填 API key

```bash
cp .env.example .env
# 用编辑器打开 .env，填进 2 个最低必填 key：
#  - LLM_PROXY_API_KEY     (Anthropic Claude / Google Gemini / OpenAI 任选一)
#  - VOLC_ICL_API_KEY      (字节火山 ICL TTS)
```

各服务申请链接见 [TUTORIAL.md 第 4 步](./TUTORIAL.md#第-4-步申请-api-key)。

### 第 6 步 · 触发 Agent 跑流水线

```bash
# 必须在仓库根目录运行
claude
```

然后输入这句话：

```
帮我用 pipeline/03-分镜/examples/古代将军/product_config.yaml 的配置，
跑一遍极客号 AI 视频复刻流水线，从 round1 脚本生成开始。
环境变量已配在 .env。
```

Agent 会自动：
1. 读 master SKILL (`pipeline/SKILL.md`) 知道按 5 步走
2. 调 round1 SKILL → 出 script.yaml → 你审 → 继续
3. 调 02-配音 SKILL → 出 mp3 → 你审 → 继续
4. 调 03-分镜 SKILL → 出 storyboard + 28 张图 → 你审 → 继续
5. 调 04-视频 SKILL → 出 28 mp4 + 拼接 → 你审 → 继续
6. 调 05-字幕 SKILL → 烧字幕 → 最终成片到桌面

✅ **跑通**。

---

## 整套流水线在做什么（脚本到字幕全流程）

### Round 1 · 脚本生成（[01-脚本/SKILL.md](./pipeline/01-脚本/SKILL.md)）

**输入**：游戏名 + 当下卖点 + 题材偏好（可选）+ 目标人群（可选）
**做什么**：用 5 个 prompt 组件让 LLM 按极客号 codex 出 60s 5 段位脚本（Hook / CoreK / AdRev / Sell / CTA）
**输出**：`script.yaml`（含每段位 target_wpm/speed_ratio 用于下游 TTS 控速）

5 个 prompt 组件在 [`pipeline/01-脚本/prompts/`](./pipeline/01-脚本/prompts/)：
- `01-knowledge-base.md` — 75 样本统计 / Hook 类型库 / 段位定义 / 词库 / 情绪燃料定义（RAG 检索源）
- `02-system-prompt.md` — 写作身份 + 情绪燃料三选一 + 风格质感
- `03-style-guide.md` — 5 步工作流 + do/don't + 7 张自审表 + JSON Schema
- `04-few-shot.md` — 8 条样本逐句标注
- `05-eval-rubric.md` — 100 分评分卡 + 失败归因

### Round 2 Step 1 · 配音 + BGM 混音（[02-配音/SKILL.md](./pipeline/02-配音/SKILL.md)）

**输入**：`script.yaml` + 30s 目标音色样本
**做什么**：
1. `clone_voice.py` 用样本训练火山 ICL voice_id（5-10 分钟）
2. `tts_volc_icl.py` 用 voice_id 按段位 speed_ratio 出 5 段 mp3
3. ffmpeg concat 拼成 `final_60s_raw.mp3`（干音）
4. 侧链混音叠加 BGM 出 `final_60s_mixed.mp3`（含 BGM 终片）

**输出**：`final_60s_{raw,mixed}.mp3`

### Round 2 Step 2 · 分镜（[03-分镜/SKILL.md](./pipeline/03-分镜/SKILL.md)）

**输入**：`script.yaml` + `product_config.yaml`（含 part1_anchor 文化锚定）
**做什么**：用 LLM 按 [codex-v2.1 12 模块](./pipeline/03-分镜/codex-v2.1/) 把 60s 脚本拆成 28-35 镜分镜表
- 关键模块：BIN 二分结构 / MAC 匹配剪辑（同动作多视角）/ SCT 主体延续 / HMI Hook 0-3s
- 每镜含：sequence_group_id, sequence_action（主体+动词）, match_type_to_prev, visual_description, camera, image_gen_prompt
- 用 nano_banana_pro / doubao-seedream 生 28 张 PNG 配图

**输出**：`storyboard.json` + `images/{shot_id}.png` × 28-35

### Round 2 Step 3 · 视频生成（[04-视频/SKILL.md](./pipeline/04-视频/SKILL.md)）

**输入**：`storyboard.json` + `images/` + `final_60s_mixed.mp3`
**做什么**：每镜按段位选模型生 4-5 秒视频片段
- Part 1（Hook + CoreK）：**kling-v2-5-turbo**（5s · 纪实风格强）
- Part 2（AdRev + Sell + CTA）：**doubao-seedance-2-0**（4s · 游戏 CG 强）
- Fallback：kling（seedance 偶发安全拦截切换）
- 拼接 + mux 配音 → BGM 完整版

**输出**：`{product}_BGM完整版.mp4`（28-35 镜拼接 · ~40s）

5 铁律：[04-视频/docs/方法论.md](./pipeline/04-视频/docs/方法论.md)
- 动作连续多视角 + 主体内部动态 + 人种统一 + 禁英文 + 训练资产留口

### Round 2 Step 3.5 · 画幅适配（[04.5-画幅/SKILL.md](./pipeline/04.5-画幅/SKILL.md)）⚠️ 设计稿

**输入**：1920×1080 16:9 mp4
**做什么**：center crop / blur-pad / smart pad 三策略适配 9:16 / 1:1
**输出**：`video_{16x9,9x16,1x1}.mp4`

### Round 2 Step 4 · 字幕（[05-字幕/SKILL.md](./pipeline/05-字幕/SKILL.md)）

**输入**：mp4 + `script.yaml` + `product_config.yaml`（含 highlight 词典）
**做什么**：
1. 读原始脚本逐字（**不用 ASR**，避免错别字如"万国觉醒"→"万国决心"）
2. 按段位时间映射 + 段内字数比例分时
3. 按 [极客字幕 codex v1.0](./pipeline/05-字幕/codex/极客字幕Codex-v1.0.md) 渲染 .ass：
   - Normal 段位：思源黑体 Bold 96px / 白字黑描边 / 关键词金黄 #FFD700 高亮
   - CTA 段位：思源黑体 Heavy 144px italic / 红色 #FF0000 + popup 动画
   - 字距 Spacing 4-6 / 末尾标点剥离
4. ffmpeg 烧字幕到 mp4

**输出**：`{product}_字幕版.mp4`（带字幕终片）

---

## 跨产品复用：改 1 个文件

新增任意 SLG 游戏，只改 [`product_config.yaml`](./pipeline/04-视频/prompts/product_config_template.yaml) 的 6 个必填字段：

```yaml
game_name: "你的游戏名"                  # 例：万龙觉醒 / 战火勋章
game_genre: "SLG / 4X 策略"
target_audience: "目标人群描述"

# Part 1（历史/纪实段）视觉锚定
part1_anchor: "Ancient Han Dynasty Chinese..."

# Part 2（游戏 CG 段）视觉锚定
part2_anchor: "Cartoon-realistic 3D RTS CG..."

# Part 1 禁止元素
part1_neg_extra: "non-asian people, modern clothing..."
```

然后告诉 Agent：

```
用 my_game/product_config.yaml 跑一遍流水线
```

详见 [TUTORIAL.md 第 6 步](./TUTORIAL.md#第-6-步换个游戏跑)。

---

## 7 个 SKILL 速查

| SKILL | 路径 | 触发关键词 | 干啥 |
|---|---|---|---|
| Master | [pipeline/SKILL.md](./pipeline/SKILL.md) | 极客号复刻 / AI 视频流水线 | 5 步流程编排 + 跨产品入口 |
| 01 脚本 | [pipeline/01-脚本/SKILL.md](./pipeline/01-脚本/SKILL.md) | 脚本生成 / script | 5 prompt → 60s yaml |
| 02 配音 | [pipeline/02-配音/SKILL.md](./pipeline/02-配音/SKILL.md) | 配音 / 克隆音色 / TTS | 火山 ICL + BGM 混音 |
| 03 分镜 | [pipeline/03-分镜/SKILL.md](./pipeline/03-分镜/SKILL.md) | 分镜 / storyboard | LLM 28-35 镜 + 生图 |
| 04 视频 | [pipeline/04-视频/SKILL.md](./pipeline/04-视频/SKILL.md) | 视频生成 / AI 出视频 | kling+seedance + 拼接 |
| 04.5 画幅 | [pipeline/04.5-画幅/SKILL.md](./pipeline/04.5-画幅/SKILL.md) | 画幅适配 | 16:9 → 9:16/1:1（设计稿） |
| 05 字幕 | [pipeline/05-字幕/SKILL.md](./pipeline/05-字幕/SKILL.md) | 字幕 / 上字幕 / ass | 极客 codex + 自动渲染 |

---

## 跨 Agent 平台部署

`setup.sh` 默认装到 Claude Code。其他平台手动：

| Agent | 装载位置 |
|---|---|
| **Claude Code** | `.claude/skills/<name>/SKILL.md`（`bash setup.sh` 自动） |
| **Cursor** | `.cursor/rules/<name>.mdc`（需手动改 frontmatter） |
| **Gemini CLI** | `~/.gemini/skills/<name>/SKILL.md`（手动） |
| **Copilot CLI** | `~/.copilot/skills/<name>/SKILL.md`（手动） |
| **自建 Agent (Anthropic SDK)** | 把 SKILL.md 读进 system prompt |

欢迎 PR 贡献其他平台的 setup 适配。

---

## 工作纪律 3 条铁律（已写进 master SKILL，Agent 自动遵守）

1. **Master SKILL 是唯一入口** — Agent 接到"做复刻视频"先读 master SKILL
2. **里程碑制** — 每步跑完停下等审，禁一口气跑 5 步（任意一步失误，回退成本翻倍）
3. **跨产品入口只看 product_config.yaml** — 任何脚本禁 hardcode 产品信息

---

## 仓库结构

```
slg-geek-video-pipeline/
├── README.md                    # 你在这（5 分钟新手入门）
├── TUTORIAL.md                  # 详细 FAQ + 故障排查
├── CLAUDE.md                    # Agent 工作手册
├── .env.example                 # API key 模板
├── setup.sh                     # 自动装 7 SKILL 到 .claude/skills/
│
└── pipeline/                    # 7 个 SKILL + 配套资产
    ├── SKILL.md                # master
    ├── README.md
    │
    ├── 01-脚本/                # Round 1
    │   ├── SKILL.md
    │   └── prompts/            # 5 prompt 组件
    │
    ├── 02-配音/                # Round 2 Step 1
    │   ├── SKILL.md
    │   ├── scripts/            # clone_voice / tts_volc_icl / validate
    │   ├── voice_codex.yaml
    │   └── script_60s_example.yaml
    │
    ├── 03-分镜/                # Round 2 Step 2
    │   ├── SKILL.md
    │   ├── docs/方法论.md
    │   ├── prompts/            # asset_request + product_config
    │   ├── scripts/            # 01_gen + 02-06 配套
    │   ├── codex-v2.1/         # 12 模块视觉 codex
    │   └── examples/古代将军/   # final example
    │
    ├── 04-视频/                # Round 2 Step 3
    │   ├── SKILL.md
    │   ├── docs/方法论.md      # 5 铁律
    │   ├── prompts/            # product_config_template
    │   └── scripts/            # 01_upload → 04_concat
    │
    ├── 04.5-画幅/              # Step 3.5（设计稿）
    │   └── SKILL.md
    │
    └── 05-字幕/                # Round 2 Step 4
        ├── SKILL.md
        ├── docs/方法论.md      # 7 决策
        ├── codex/极客字幕Codex-v1.0.md
        ├── scripts/            # 01_extract (PoC) + 03_apply (final)
        └── examples/subtitle_final.ass
```

---

## 我应该看什么

| 你的角色 | 看哪个 |
|---|---|
| 实习生第一天部署 | 本 README + `bash setup.sh` |
| 想看完整 FAQ + 故障排查 | [TUTORIAL.md](./TUTORIAL.md) |
| 想了解每步原理 | [pipeline/SKILL.md](./pipeline/SKILL.md) + 各 step SKILL |
| 想看代码（Python） | `pipeline/0*-*/scripts/` |
| 想看字幕样式 codex | [pipeline/05-字幕/codex/极客字幕Codex-v1.0.md](./pipeline/05-字幕/codex/极客字幕Codex-v1.0.md) |
| 想看视觉 codex（12 模块） | [pipeline/03-分镜/codex-v2.1/README.md](./pipeline/03-分镜/codex-v2.1/README.md) |
| 想看示例分镜方案 | [pipeline/03-分镜/examples/古代将军/storyboard.json](./pipeline/03-分镜/examples/古代将军/storyboard.json) |

---

## 关键依赖

- **LLM**：任意 OpenAI 兼容 API（推荐 Anthropic Claude 4.x / Google Gemini 3.x / OpenAI GPT-4o）
- **TTS**：字节火山 ICL（[申请](https://console.volcengine.com/speech)）
- **视频生成**：kling-v2-5-turbo（快手）+ doubao-seedance-2-0（字节）
- **字体**：思源黑体 SC Bold + Heavy
- **本地**：Python 3.11+ / ffmpeg / faster-whisper / openai SDK

---

## 历史

| 版本 | 时间 | 里程碑 |
|---|---|---|
| v0.9 | 2026-05 | round1-step3 全流水线打通 |
| v0.9.1 | 2026-05-25 | + MAC 模块 / 字幕 codex / step3.5 设计稿 |
| **v1.0** | 2026-05-25 | 仓库整理：only final / 0→1 newcomer 友好 README + setup.sh |

---

## 反馈

仓库 [Issues](https://github.com/Unknowing-Ai/slg-geek-video-pipeline/issues)。
