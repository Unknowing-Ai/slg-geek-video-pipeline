# 极客复刻 v0.9 — SLG 买量 AI 视频生产 Pipeline

> 基于"极客号" KOL 视频拆解 + AI 生成工具链，搭建跨产品通用的"脚本 → 配音 → 分镜 → 视频 → 字幕"流水线。

## 🚀 跨 round 总入口

**新人 / Agent 首次接触 → 必读 [`SKILL.md`](./SKILL.md)（master pipeline）**

| Round | 范围 | SKILL |
|---|---|---|
| **Round 1** | 脚本生成（极客风格 60s 脚本 · 5 prompt 组件） | [01-脚本/SKILL.md](./01-脚本/SKILL.md) |
| **Round 2 Step 1** | 火山 ICL 克隆配音 + BGM 混音 | [02-配音/SKILL.md](./02-配音/SKILL.md) |
| **Round 2 Step 2** | LLM 28-35 镜分镜（含 MAC 模块） | [03-分镜/SKILL.md](./03-分镜/SKILL.md) |
| **Round 2 Step 3** | kling + doubao-seedance 视频生成 视频生成（kling + seedance） | [04-视频/SKILL.md](./04-视频/SKILL.md) |
| **Round 2 Step 3.5** | 16:9 → 9:16 / 1:1 画幅适配（设计稿） | [04.5-画幅/SKILL.md](./04.5-画幅/SKILL.md) |
| **Round 2 Step 4** | 极客字幕 codex + ass 自动渲染 | [05-字幕/SKILL.md](./05-字幕/SKILL.md) |

**跨产品入口**：[`product_config_template.yaml`](./04-视频/prompts/product_config_template.yaml)（改 6 字段定义新产品）

---

# 极客号风格复刻 · 脚本生成系统（Round 1）

> 把中国 SLG 国区头部达人"极客"号的视频脚本风格，做成一套 AI 能直接用的 prompt 工程组件。给 [产品] 和 [当下卖点]，模型输出 50 秒视频脚本（分镜级），跨产品复用（万国/战火/万龙均已验证）。

**版本**：v0.9.1 · 2026-05-20
**适用范围**：SLG / 4X / 策略品类 · 中国国区男性向硬核买量

**v0.9.1 vs v0.9 改动**：新增**反 few-shot 过拟合机制**——02 增加禁抄硬规矩 / 03 工作流增加 Step 6 Hook 差异化检查 + 自审表 8 / 04 Tier 1 从 5 条减为 3 条且每条加"应该学/不应该照搬"标注 / 推荐调用温度从 0.7 提到 0.85-0.9。v0.9 跨模型测试中 33% 输出抄样本，v0.9.1 修订即为此问题。

---

## 这套东西是什么

把人能读懂的"风格手册"，重组成 AI 能直接读取调用的工程组件：

```
极客复刻-v0.9/
├── README.md                    ← 你在这（给人读的整体说明）
└── prompts/                     ← 给 AI 读的 5 个工程组件
    ├── 01-knowledge-base.md
    ├── 02-system-prompt.md
    ├── 03-style-guide.md
    ├── 04-few-shot.md
    └── 05-eval-rubric.md
```

**人审视角**：读完 README，了解整体；遇到具体规则去 prompts/ 各文件。
**AI 调用视角**：02+03+04 拼成 System Prompt，01 做 RAG 检索源，05 做事后评分。

---

## 极客号风格的本体（在一页里讲完）

### 表层 vs 内核

人看极客号视频时，看到的是"硬核知识科普"——讲古代后勤、讲驱逐舰反潜、讲现代武器。但真正驱动用户下载的，是知识表层下的**情绪燃料内核**。

| 表层 | 内核 |
|---|---|
| 知识分享者 | 情绪传送装置 |
| "为什么古代一打仗就缺粮" | 智识优越感（你不知道的我知道） |
| "为什么只有中国人才能以步制骑" | 民族优越感（我们 vs 他们） |
| "为什么人类没有驯化老虎" | 欲望落差（现实做不到 → 游戏里能做到） |

**反例**："以步制骑"四个字本身是中性知识点，没有情绪。"为什么只有中国人才能以步制骑"才是带燃料的版本。**这是该号风格最容易学错的地方**。

### 情绪燃料三选一

每条脚本生成前必须先选 1 个主燃料：

| 燃料 | 适用题材 | 典型 Hook |
|---|---|---|
| 民族优越感 | 中国历史、军事、文明 | "为什么只有 X 才能…" / "他们直到 X 年才学会，我们 Y 千年前就在用" |
| 智识优越感 | 现代军事、科技、硬核装备 | "你以为这是 X，其实是 Y" / "它问世的时候我们村甚至还没有通电" |
| 欲望落差 | 奇幻、异世界、动物、神话 | "为什么人类没有 X" / "现实做不到的 X，但是在 [游戏] 里…" |

### 5 类 Hook（按使用频率排）

| 类型 | 占头部 Hook % | 句式 |
|---|---|---|
| B-1 揭秘式 | 60%+ | 为什么 X / 为何 X / 到底有多 X |
| B-2 反转式 | 20% | 你以为 X 其实 Y / 有人问 X…仔细看就明白 |
| B-5 类比式 | 10% | 古代 X，现代 Y / 我们 vs 他们 |
| B-3 极端式 | 5% | 它问世时 [反差锚] 还没 X / 仅 X 就 Y |
| B-4 数字式 | 5% | 通常嵌入 B-1/B-2 的展开段，不做主 Hook |

### 7 段位结构

```
[0-4s Hook] → [4-14s 铺垫A] → [14-26s 铺垫B-情绪峰值] → [26-33s 桥梁]
                                                      ↓
[33-41s 玩法A 因果回答 Hook] → [41-47s 玩法B 维度跳跃] → [47-50s CTA]
```

**桥梁那一句话是命脉**："然而在 [产品] 中" / "而今在 [产品] 中" / "但是在 [产品] 里"——用最朴素的句式一秒切。

**玩法 B 必须维度跳跃**——不是玩法 A 的并列第二卖点，而是从"单兵 → 兵种群"或"个体 → 体系"或"单点 → 世界感"的跳跃。

---

## 系统怎么工作（流程图）

```
用户输入：产品名 + 当下卖点 + 题材偏好（可选）
    ↓
┌──────────────────────────────────────────┐
│ Step 1 · 双起点矩阵筛选                  │
│  横轴：5-8 个真实卖点（01-KB E 节）       │
│  纵轴：10-15 个话题池（01-KB F 节）       │
│  每格评分桥接自然度（0-3 分）             │
│  从 3 分组合出发；没有 3 分 = 换卖点      │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ Step 2 · 选情绪燃料 + 锁主线词（带燃料）  │
│  例：以步制骑（裸）→ 为什么只有中国人才能… │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ Step 3 · 选 Hook 类型 + 写 Hook（20-35 字）│
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ Step 4 · 顺写 7 段位（按 01-KB C 节字数）  │
│  铺垫A → 铺垫B → 桥梁 → 玩法A → 玩法B → CTA │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ Step 5 · 7 张自审表 + JSON Schema 输出     │
│  人设外壳 / 情绪燃料 / 主线词因果 /         │
│  维度跳跃 / 字幕规则 / CTA / 换名检验       │
└──────────────────────────────────────────┘
    ↓
输出脚本（Markdown 分镜表） + 自审 JSON
    ↓
人审用 05-rubric 评分（100 分） → 总分 ≥ 80 进运营试投
                                  总分 < 80 走 B 节失败归因 + 修订重跑
```

---

## 5 个组件各是什么

| 文件 | 给谁 | 干什么 | 何时改它 |
|---|---|---|---|
| [01-knowledge-base.md](./prompts/01-knowledge-base.md) | AI · RAG 检索源 | 75 样本统计 / Hook 类型库 / 7 段位定义 / 9 类词库 / 卖点矩阵 / 话题池 / 情绪燃料定义 / 因果路径模板 | 接入新产品时（补卖点矩阵、补话题池） |
| [02-system-prompt.md](./prompts/02-system-prompt.md) | AI · System Prompt 主体 | 写作身份 / 价值观 / 情绪燃料三选一 / 风格质感对照表 / 禁忌清单 | 修订人格表达时（极少改） |
| [03-style-guide.md](./prompts/03-style-guide.md) | AI · System Prompt 技法部分 | 5 步工作流 / 7 段位 do-don't / 7 张自审表 / 输出 JSON Schema | 调整硬规矩时 |
| [04-few-shot.md](./prompts/04-few-shot.md) | AI · 校准层 | 5 条核心样本逐句标注 + 3 条扩展样本关键拆解，共 8 条覆盖 3 产品 5 类 Hook | 加入新成功样本时（如某条新投出爆款，把它的 Hook 拆解加入） |
| [05-eval-rubric.md](./prompts/05-eval-rubric.md) | 人 + AI · 调优 | 100 分评分卡 / 7 种失败归因模板 / A/B 测试流程 / 二次审核 prompt | 季度复盘后调整权重和锚点 |

---

## 新产品如何接入（4 步）

### Step 1 · 补卖点矩阵

打开 [01-knowledge-base.md](./prompts/01-knowledge-base.md) E 节，按格式追加新产品的卖点表：

```markdown
### E-4 [新产品名]

| 卖点类别 | 具体卖点 | 在样本中如何呈现（如无样本可写"产品方说明"） |
|---|---|---|
| ... | ... | ... |
```

**这一步必须由产品方提供，不能 AI 编**。

### Step 2 · 补话题池（如题材新）

如果新产品题材在 F-1/F-2/F-3 都没覆盖，新增 F-4 话题池。来源建议：
- 该产品已投放过的高 CTR 素材的 Hook 文案
- 目标受众活跃论坛/社群关心的话题
- 跟该题材最相关的"冷门但容易共鸣"的泛知识

### Step 3 · 复用 02 / 03 / 04 / 05

绝大多数情况下这 4 个文件不改。人格层、技法层、few-shot 范例、评分卡都是跨产品通用。

如果新产品题材完全不同（如非历史/军事/奇幻），考虑在 04-few-shot 加 1-2 条该产品已投出的爆款样本作为额外校准。

### Step 4 · 跑生成 → 评分 → 修订

按"系统怎么工作"流程跑。第一批生成质量不够时，看 05-eval-rubric B 节失败归因，回到 Step 1 或 Step 3。

---

## 调优循环（运营迭代）

```
生成 → A/B 测试投放 → CTR/CPM 数据回流 → 月度复盘
                                          ↓
                       哪类燃料表现好？哪种 Hook 形态高 CTR？哪个跳跃方向爆款？
                                          ↓
                       命中样本 → 拉出 self_audit JSON → 提取燃料/类型/跳跃方向
                                          ↓
                       01-KB 话题池打 ★ + 02 风格参考表加金句 + 04 加新样本
                                          ↓
                                       回到生成
```

**每月做一次**，每季度做一次大复盘（评分卡权重 + 失败归因更新）。

---

## 哪些资料 Claude 可以提供 / 哪些必须产品方提供

| 资料类别 | 提供方 | 当前状态 |
|---|---|---|
| 75 样本统计 + Hook 类型库 + 7 段位结构 + 9 类词库 + 情绪燃料定义 + 因果路径模板 | Claude（来自本研究） | ✅ 已写入 01-KB |
| 已投样本卖点矩阵（万国/战火/万龙） | Claude（从样本中提炼） | ✅ 已写入 01-KB E 节 |
| Few-shot 8 条样本标注 | Claude | ✅ 已写入 04 |
| 评分卡 + 失败归因模板 | Claude | ✅ 已写入 05 |
| **新产品的卖点知识库** | **产品方** | ❌ 接入新产品时必填 |
| **新产品的目标受众话题偏好** | **产品方 + 运营** | ❌ 接入新产品时必填 |
| **真实 CTR/CPM/消耗回流数据** | **投放团队** | ❌ 持续接入 |
| 跨题材验证（新题材模拟测试） | Claude + 用户协作 | ⚠️ 待用户拍板 |

---

## 附录 · 一键部署提示词（双形态）

### 形态 A · 单 prompt 直接喂模型（适合 ChatGPT / Claude 网页 / 单次调用）

把 02 + 03 + 04 全文拼成一份 System Prompt，用户 prompt 只写参数。

```text
[把 02-system-prompt.md 全文粘贴在此]

---

[把 03-style-guide.md 全文粘贴在此]

---

[把 04-few-shot.md 全文粘贴在此]

---

# 任务

请基于以下输入生成一条 50 秒视频脚本：

- 产品名：{{product_name}}
- 当下卖点：{{current_selling_point}}
- 题材偏好（可选）：{{theme_preference}}
- 目标人群（可选）：{{target_audience}}

按 03-style-guide 工作流 Step 1-5 执行：
1. 双起点矩阵筛选（横轴卖点 × 纵轴话题池）
2. 选情绪燃料 + 锁带燃料主线词
3. 选 Hook 类型 + 写 Hook
4. 顺写 7 段位
5. 7 张自审表 + JSON Schema 输出

输出格式：先输出 ===SCRIPT=== Markdown 脚本，再输出 ===AUDIT=== JSON。

如果自审任一表 FAIL，必须主动修订并输出 v2 版。
```

**注意**：单 prompt 形态适合**单次手工调用 + 偶尔生成**场景。如果要批量生成或频繁迭代，用形态 B。

**推荐调用参数**：
- temperature = **0.85-0.9**（v0.9 实测 0.7 时部分模型会逐字抄 04 样本；提高到 0.85-0.9 鼓励原创）
- max_tokens ≥ 6000（让模型有空间输出完整脚本 + self_audit + 必要时 v2 修订）
- top_p = 0.95（与 temperature 配合）

### 形态 B · 模板 + 加载指令（适合 Agent 工程化 / 批量生成）

```python
# 伪代码示意
from anthropic import Anthropic

client = Anthropic()

# 加载 5 个组件
with open("prompts/01-knowledge-base.md") as f: KB = f.read()
with open("prompts/02-system-prompt.md") as f: SYS = f.read()
with open("prompts/03-style-guide.md") as f: GUIDE = f.read()
with open("prompts/04-few-shot.md") as f: SHOTS = f.read()
with open("prompts/05-eval-rubric.md") as f: RUBRIC = f.read()

# RAG 检索（按需）
relevant_kb_chunks = rag_retrieve(KB, query=f"{product_name} {selling_point}")

# 构造 System Prompt
system_prompt = f"{SYS}\n\n---\n\n{GUIDE}\n\n---\n\n{SHOTS}\n\n---\n\n# 相关知识库片段\n{relevant_kb_chunks}"

# User Prompt
user_prompt = f"""
请基于以下输入生成 1 条 50 秒视频脚本：
- 产品：{product_name}
- 卖点：{selling_point}
- 题材偏好：{theme}
- 目标人群：{audience}

按 03-style-guide Step 1-5 执行，输出 ===SCRIPT=== 和 ===AUDIT===。
"""

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=8000,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}]
)

# 二次审核（用 05 评分卡）
audit_prompt = f"{RUBRIC}\n\n---\n\n# 对刚才输出做自评\n{response.content[0].text}"
audit_response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4000,
    messages=[{"role": "user", "content": audit_prompt}]
)
# 解析 audit_response 的 JSON，如果 total_score < 80 自动触发修订重跑
```

**优点**：可批量、可日志化、可加 RAG、可自动修订
**适合**：把脚本生成嵌入更大的 Agent 流水线（如 Phase 2 分段视频 Agent / Phase 3 剪辑 Agent）

---

## 接下来的路线（远期阶段)

| 阶段 | 周期 | 核心产出 |
|---|---|---|
| **Phase 1 当前 - 脚本生成** | ✅ 完成 v0.9 | 5 个 prompt 组件 + 评分卡 |
| Phase 2 分段视频 Agent | 4-6 周 | 分镜 → 素材（库复用 + AI 生成 + 真人补拍清单） |
| Phase 3 剪辑 Agent | 4-8 周 | FFmpeg + 字幕 + BGM 库自动组装 |
| Phase 4 发布 Agent | 2-3 周 | 上传 + 标签 + 投放时机 + 数据回流 |
| Phase 5 数据驱动自动迭代 | 持续 | 命中样本自动回流 → 01-KB / 02 / 04 自动更新 |

---

## 关键资产指引

| 资产 | 路径 |
|---|---|
| 本组件包 | `pipeline/` |
| 75 条样本视频 | `materials/videos/` |
| 75 条样本脚本（Gemini 抽取） | 桌面 `极客复刻/scripts/`（150 文件 = 75×.md + 75×.json） |
| 样本索引 + 元数据 | `materials/index.csv` |
| Step 2 结构模式分析 | `research/structure-patterns-v2.md` |
| Step 3 语言风格指纹 | `research/language-fingerprint-v2.md` |
