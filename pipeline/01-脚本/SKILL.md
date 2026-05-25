---
name: geek-script-generation
description: 用极客号风格 5 prompt 套件生成 60s SLG 买量短视频脚本。输入：产品名 + 当下卖点 + 题材偏好（可选）。输出：符合 voice_codex 段位结构 + 字数的 script.yaml（5 段位 · ~366 字 · 含每段 target_wpm/speed_ratio）。是 master pipeline 第 1 步，下游对接 step1 配音。当用户要为新 SLG 产品产出极客风格脚本，或要从产品卖点直接出可投放脚本时使用。
version: "0.9.1"
---

# Round 1 · 极客号脚本生成 SKILL

> 极客号风格 60s SLG 买量短视频脚本生成器。**纯 LLM prompt 工程**，无 Python 脚本。

## 你需要给我什么

```yaml
product_name: "你的游戏名"          # 例: 万国觉醒 / 万龙觉醒
current_selling_point: "本期卖点"   # 例: 中式文明体系 + 中国名将 + 诸葛弩
theme_preference: "题材偏好"         # 可选，例: 中国历史 / 现代军事
target_audience: "目标人群"          # 可选
```

## 我给你什么

`script.yaml` — 符合下游 step1 配音 SKILL 输入契约的 60 秒脚本：

```yaml
meta:
  title: "脚本标题"
  total_duration_target_sec: 60
  total_chars: 369                  # 字数（落 codex 安全区 [337, 393]）

segments:
  - segment_id: 1
    semantic_role: Hook_Counter_Intuitive
    duration_target_sec: 5
    target_wpm: 386                  # 段位目标语速
    target_cps: 6.43
    target_chars: 32
    actual_chars: 32
    speed_ratio: 1.12                # ICL 克隆音色 speed 参数（target_wpm / 345）
    text: "古代将军最大的敌人不是敌军？10万出关只回来3千。"

  - segment_id: 2
    semantic_role: Core_Knowledge
    duration_target_sec: 22
    target_wpm: 365
    target_cps: 6.08
    target_chars: 134
    actual_chars: 134
    speed_ratio: 1.06
    text: "..."

  # 5 段位共 5 个 segment（Hook / CoreK / AdRev / Sell / CTA）
```

## 5 段位结构（必须严格遵守）

| 段位 | semantic_role | 时长 | 字数 | 职责 |
|---|---|---|---|---|
| 1 | Hook_Counter_Intuitive | 5s | 32 | 抓眼球 + 反直觉问题 |
| 2 | Core_Knowledge | 22s | 134 | 给硬核知识 + 情绪燃料 |
| 3 | Ad_Reversal | 10s | 63 | 转折桥梁"但在 X 里" + 产品入场 |
| 4 | Selling_Point | 15s | 91 | 卖点 1 + 卖点 2 维度跳跃 |
| 5 | CTA | 8s | 49 | 行动召唤 + 产品名 |

## 工作流（5 步 + 自审）

### Step 1: 装入 5 个 prompt 组件
```
读：pipeline/01-脚本/prompts/
- 01-knowledge-base.md  (RAG 检索源 · 75 样本 + Hook 库 + 段位定义 + 词库 + 卖点矩阵 + 情绪燃料定义)
- 02-system-prompt.md   (写作身份 + 情绪燃料三选一 + 风格质感对照表 + 禁忌)
- 03-style-guide.md     (5 步工作流 + 7 段位 do-don't + 7 张自审表 + JSON Schema)
- 04-few-shot.md        (8 条样本逐句标注校准)
- 05-eval-rubric.md     (100 分评分卡 + 失败归因模板)
```

把 02 + 03 + 04 拼成 system prompt，01 作为知识库引用。

### Step 2: 双起点矩阵筛选（关键，不能跳）

- 横轴：5-8 个该产品真实卖点（产品方提供 / 01-KB E 节）
- 纵轴：10-15 个目标受众感兴趣的泛知识话题（01-KB F 节）
- 每格评分桥接自然度（0-3 分）
- **只从 3 分组合出发**

### Step 3: 选情绪燃料 + 锁带燃料主线词

3 种情绪燃料选 1：
- **民族优越感**：中国历史/军事/文明
- **智识优越感**：现代军事/科技/装备
- **欲望落差**：奇幻/异世界/动物/神话

主线词必须**自带情绪燃料**：
- ❌ "以步制骑"（中性）
- ✅ "为什么只有中国人才能以步制骑"（带燃料）

### Step 4: 选 Hook 类型 + 写 Hook（20-35 字）

| 类型 | 占比 | 句式 |
|---|---|---|
| B-1 揭秘式 | 60%+ | 为什么 X / 为何 X / 到底有多 X |
| B-2 反转式 | 20% | 你以为 X 其实 Y |
| B-5 类比式 | 10% | 古代 X，现代 Y |
| B-3 极端式 | 5% | 它问世时 [反差锚] 还没 X |
| B-4 数字式 | 5% | 嵌入 B-1/B-2 展开段 |

### Step 5: 顺写 5 段位 + 7 张自审表

按 03-style-guide 工作流：
- 铺垫 A → 铺垫 B → 桥梁（"但在 X 里"）→ 玩法 A 因果回答 Hook → 玩法 B **维度跳跃** → CTA
- 跑完 7 张自审表，任一 FAIL 必须主动修订 v2

### Step 6: 输出 script.yaml + self_audit JSON

按上面"我给你什么"的 schema 输出 yaml。
另外输出 self_audit JSON（详见 03-style-guide），覆盖 7 个维度评分。

## 关键约束（必须遵守）

1. **5 段位字数严格**：Hook 32 / CoreK 134 / AdRev 63 / Sell 91 / CTA 49（误差 ±10%），否则 step1 配音段位时长对不齐
2. **target_wpm 不能瞎填**：按 codex 节奏（Hook 386 / CoreK 365 / AdRev 377 / Sell 364 / CTA 346），speed_ratio = target_wpm / 345
3. **主线词自带情绪燃料**：每一段必须能 trace 回 02-system-prompt 的情绪燃料三选一
4. **桥梁那句话是命脉**：用最朴素句式一秒切入产品，如"但在 X 里 / 然而在 X 中"
5. **玩法 B 必须维度跳跃**：不是玩法 A 的并列第二卖点，是从"单兵→兵种群"/"个体→体系"的跨级
6. **CTA 不做强引导**：极客号 Part 2 重点是画面流畅 + 内容表达到位，转化是隐性（参考 project_geek_no_cta.md）

## 跨产品适配

5 个 prompt 组件**全跨产品通用**。新产品只需要：

1. **补 01-KB E 节卖点矩阵**（产品方提供，不能 AI 编）
2. **补 01-KB F 节话题池**（如题材新）
3. 02/03/04/05 全部不动

## 调用方式（Agent 用）

**方式 A：单 prompt 直接喂模型**
```
把 02 + 03 + 04 全文拼成 System Prompt → User Prompt 只写参数：
  - product_name
  - current_selling_point
  - theme_preference (可选)
  - target_audience (可选)

输出格式：
  ===SCRIPT===  ← Markdown 脚本（人审用）
  ===YAML===    ← script.yaml（机器用，喂给 step1 配音）
  ===AUDIT===   ← self_audit JSON

如自审任一 FAIL，主动修订 v2。
```

**推荐调用参数**：
- temperature = **0.85-0.9**（v0.9.1 实测 0.7 时部分模型逐字抄 04 样本，提到 0.85-0.9 鼓励原创）
- max_tokens ≥ 6000
- top_p = 0.95

**方式 B：嵌入 Agent 流水线**

详见 `pipeline/README.md` 附录"形态 B · 模板 + 加载指令"。

## 输出契约（给下游 step1 配音）

```yaml
inputs_to_step1:
  script_yaml: <本 SKILL 输出的 script.yaml>
expected_behavior:
  step1 会读 script.yaml 的 segments[].text + speed_ratio
  调火山 ICL 克隆音色 TTS 生成 final_60s_raw.mp3
  再侧链混音生成 final_60s_mixed.mp3
```

## 已知工程坑

1. **逐字抄 04 样本**：v0.9 跨模型测试中 33% 输出抄样本。v0.9.1 已加反 few-shot 过拟合机制（02 禁抄硬规矩 + 03 Step 6 Hook 差异化检查 + 04 标注"应该学/不应该照搬"）+ 推荐 temp 提到 0.85-0.9
2. **情绪燃料缺失**：如果输出读起来像 wikipedia 词条 = 燃料漏了。回到 Step 3 重选燃料
3. **桥梁突兀**："但在 X 里" 必须自然，前一段铺垫要给桥梁留接口
4. **字数失控**：超过 ±10% 后下游 step1 配音段位时长对不齐，必须重写控字

## 相关 SKILL

- **下游 step1 配音**: `02-配音/SKILL.md` 读 script.yaml 出 mp3
- **prompt 套件**: `pipeline/01-脚本/prompts/01-05.md`
- **5 prompt 组件总览**: `pipeline/README.md`（Round 1 部分）

## 示例

参考产物：`02-配音/script_60s_validate.yaml`（ROK 古代将军主题，已验证可下游 step1 配音）
