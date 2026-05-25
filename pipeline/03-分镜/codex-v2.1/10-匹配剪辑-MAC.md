# 模块 K · 匹配剪辑（Matched_Cut / MAC）

## 1. 模块定位

本模块解决极客类「影视混剪」KOL 的核心剪辑魔法：**为什么硬切 71-96% 但看着不突兀**。

v1.0 codex 只记录了「Hard_Cut 占比高」这个事实；v2.0 的 BIN-03 也只说明「跨 Pivot 用 Hard_Cut + 强反差」。但这都没解释**段位内部** Hard_Cut 之间如何衔接 — 极客号大量使用「匹配剪辑」让相邻硬切镜头通过【主题/主体/动作】保持视觉连贯，硬切感被消除。

**未识别此模块的后果**：复刻视频每镜都是全新主题（每刀都是真正的"跨场景断"），观众感知视觉密度低、节奏碎、有断层 — 这就是 step3 PoC 全量产出实测的问题。

---

## 2. 核心规则

### MAC-00 ⭐ 匹配剪辑的正确定义（最关键，PoC 修订）
**一句话核心**：matched cut **必须是「同一持续动作的不同机位」**，不是「同主题不同瞬间的拼接」。

**两种 matched 的差异**（PoC 实测教训）：

| 类型 | 例 | 视觉效果 | 是否真匹配 |
|---|---|---|---|
| ❌ 同主题不同瞬间 | 运粮全景 → 冰冻骑兵特写 → 粮草地图 → 营帐倒塌（同"古代行军艰难"主题但不同动作） | 仍有断裂感，节奏碎 | **不算真正的 matched** |
| ✓ 同动作不同机位 | 骑兵冲锋正面远景 → 战马蹄部俯视特写 → 骑兵列队侧面 Pan（同一支骑兵+同一持续动作） | 完全连贯，硬切感消失 | **真正的 matched cut** |

**判断标准**：能不能用一句"主体 + 动词 + 持续状态"描述整组镜头？
- ✓「骑兵正在持续冲锋」 → 任何机位的冲锋画面都属于同一动作组
- ❌「关于古代行军的杂集」 → 不是同一动作，是同一主题

**执行方法**：每个 sequence_group 命名时必须用「主体 + 持续动作」格式（如 `cavalry_charging` / `wheel_stuck_spinning`），不能用「主题词」（如 `ancient_logistics`）

---

### MAC-01 匹配剪辑总占比
**一句话核心**：单段位内相邻镜头之间，**≥ 70%** 应该是「匹配剪辑」（matched=Y，按 MAC-00 标准）。

**数据支撑**：3 条样本验证 matched_ratio = 79.2% / 83.3% / 81.8%，中位数 81.8%，std=2.1。匹配剪辑是极客号混剪的**绝对主力手法**。

**断点（matched=N，~20%）**：几乎全部落在【跨 Pivot 那一刀】（实拍→游戏 UI），承接 BIN-03 的「Hard_Cut + 强反差」逻辑 — 极客刻意制造现实/游戏断层来强化反转。

**执行方法**：
```json
{
  "constraint_id": "MAC-01",
  "matched_ratio_target": 0.70,
  "allowed_breakpoint": ["跨 Pivot 那一刀"]
}
```

---

### MAC-02 匹配剪辑类型分布
**一句话核心**：4 种匹配类型中，**Same_Theme_Multi_Source 占 81% 是绝对主力**，其次 Same_Subject_New_State 占 16%。

**枚举 4 种类型**：

| 类型 | 占比 | 定义 | 例 |
|---|---|---|---|
| **Same_Theme_Multi_Source** | **81%** | 前后两镜来自不同物理素材，但展示同一主题/动作类型/场景类型的延续展开 | A 电影运粮全景 → B 纪录片运粮特写（同主题"古代运粮"） |
| Same_Subject_New_State | 16% | 同一主体类型/角色在不同情境延续 | 阿帕奇飞行 → 阿帕奇维护 → 阿帕奇开火 |
| Action_Match | 2% | 前镜动作的方向/节奏在后镜延续 | 箭飞出 → 箭射中目标 |
| Same_Scene_Multi_Angle | 0% | 前后两镜来自同一物理时空，机位/景别变化 | 极客号几乎不用（不拍原片） |

**反例**：
- ❌ 把每个镜头都设计为全新主题（运粮 → 行军 → 推车 → 沙漠 → 营帐 → 方阵），matched_ratio=0%
- ❌ 仅 Same_Scene_Multi_Angle 不够 — 极客号根本不用这一类（混剪没有原片）

**执行方法**：
```json
{
  "constraint_id": "MAC-02",
  "primary_match_type": "Same_Theme_Multi_Source",
  "secondary_match_type": "Same_Subject_New_State"
}
```

---

### MAC-03 序列组（Sequence Group）
**一句话核心**：每段位至少 1 个「序列组」 — **2+ 个相邻镜头共享同一主题/主体**，且整条视频至少存在 1 个**最大序列组 ≥ 8 镜**。

**数据支撑**：3 条样本最大序列组分别是 15/12/8 镜，**中位数 12 镜**。最大组几乎都集中在 Part 1 开头（Hook + CoreK），用一组同主题混剪建立强信息密度。

**段位分布**（基于 3 条样本观察）：
- **Part 1 (Hook + CoreK)**：1 个超大序列组（8-15 镜），所有镜头围绕同一核心主题
- **Part 2 (AdRev + Sell)**：2-3 个中型组（3-5 镜/组），每组围绕同一游戏功能/主体

**执行方法**：
```json
{
  "constraint_id": "MAC-03",
  "min_groups_per_segment": 1,
  "max_group_size_min": 8,
  "preferred_p1_group_size": [10, 15]
}
```

---

## 3. 与其他模块的协同

- **与 BIN-03 (Hard_Cut 主导) 的协同**：BIN-03 说"用硬切"，MAC 说"硬切之间用匹配剪辑接住"。两者合一：**段内硬切+匹配 / 跨 Pivot 硬切+反差**
- **与 SCT (主体延续性) 的协同**：SCT 解决跨 Pivot 同人物延续；MAC 解决段内同主题/同主体延续。两者构成「跨段+段内」的完整连贯性保障
- **与 STR (结构语法) 的协同**：MAC-03 的序列组天然对齐 STR 的段位边界 — Hook/CoreK 一组、AdRev 一组、Sell 多组
- **与 FLU (Part2 流畅度) 的协同**：FLU-01 要求"画面-口播匹配 ≥85%"，MAC 提供执行机制 — 一段口播配一个序列组（共享主题），匹配率自然拉高

---

## 4. 快速 Checklist

- ✅ **匹配率检查**：所有相邻镜头对中，matched=Y 比例 ≥ 70%？
- ✅ **类型主力检查**：Same_Theme_Multi_Source 是不是占了至少 70%？
- ✅ **序列组检查**：Part 1 是否存在 ≥ 8 镜的最大序列组？
- ✅ **段位组检查**：每个段位（Hook / CoreK / AdRev / Sell / CTA）是否至少有 1 个序列组（2+ 镜共享主题）？
- ✅ **断点合理性**：matched=N 是否集中在跨 Pivot 那一刀？还是被随机分散到段内？
- ❌ **反例排查**：是否所有 25 镜每镜都是全新主题、全新主体、全新场景类型？这是 codex 反面。

---

## 5. 应用到 storyboard 生成（Round 2 Step 2）

**Storyboard prompt 必须新增 4 条约束**（PoC 修订版）：

1. **CoreK 段强制 1 个超大序列组**：8-12 镜围绕**一个持续动作**（如"骑兵冲锋"/"大军雪原行军"/"运粮车陷泥推不动"），从不同机位 / 景别 / 角度展示该动作的不同阶段，**严禁跳到不同动作**
2. **AdRev 段强制 1 个序列组**：4-5 镜围绕**同一角色 + 同一持续动作**（如"霍去病释放冲锋技能"/"一键调度部队行军"）
3. **Sell 段允许 2 个序列组**：每个 3-4 镜围绕**同一兵种持续作战**（如"弓骑兵持续放箭"/"步兵方阵持续推进"）
4. **跨段位允许断点**：Pivot 那一刀（CoreK 末→AdRev 起）必须强反差，符合 BIN-03

**视觉 prompt 设计原则**：
- 序列组内每镜的 `visual_description` 必须显式标注 `sequence_group_id` + `sequence_action`（主体+动词+持续状态）
- 同组的 `image_gen_prompt` 共享 70% 关键词（主体/动作/场景/光线 grading），只在【机位/景别/动作进行阶段】变化
- **首帧图必须是"动作进行中"的姿态**（蹄子半抬、士兵正用力推车、车轮带速度感），让视频生成有明确运动方向
- 同组镜头优先使用同一 reference_images 集合（**或宿主提供的同角色多动作姿态资产**），保证生图视觉一致

## 6. 应用到 video 生成（Round 2 Step 3）

**video_prompt 必须强化主体内部动态**（PoC 实测：仅描述场景模型只做镜头推拉）：

- ❌ 静态描述："a war horse standing in deep snow, camera slowly zooms in"
- ✓ 动态循环描述："a war horse's hoof rhythmically lifts and stomps into the snow with multiple full strike cycles, snow particles spraying outward, leg muscles flexing"

**禁止内容**（写进 NEG）：
- `static image, no movement, freeze frame, slow motion pause`
- `latin letters, english characters, download button, click here`（中国境内素材禁英文）
- 跨产品文化锚定（由 `product_config.yaml` 的 `part1_anchor` / `part2_anchor` 提供）
