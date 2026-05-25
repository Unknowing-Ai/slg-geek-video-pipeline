# 新产品启动 · 跟宿主要资产模板 v2（含动作姿态资产）

> 接入新产品（如 WGAME / Samo / 新 IP）跑 Round 2 Step 3 视频生成时必备
> 把下面这段直接发给该产品的**美术 owner / 项目方制作人**

> **v2 升级点**：相比 v1，新增「动作姿态资产」类别（关键），用于 Part 2 sequence_group 的多视角动作连贯生成

---

## 📩 一段话发出（拷贝模板）

```
亲爱的 [产品方/美术 owner]，

我在做 [产品名] 的极客号风格 KOL 复刻视频 AI pipeline（端到端：脚本 → 分镜图 → 视频）。
Part 2（游戏内画面）的视频生成需要用你们官方资产作 reference，
否则生成出来的"游戏画面"不像真实游戏，且无法做「同一角色多视角动作连贯组」（这是极客号视觉连贯性的核心）。

请按下面 5 类提供资产（优先级高→低）：

【1. 主要英雄角色 - 立绘】（必给 3-6 个 · P0）
   - 优先：本期脚本里点名的角色
   - 次选：产品旗舰/封面级主角形象
   - 格式：高模 CG 立绘 PNG/JPG，≥1K 分辨率，单人正面构图

【2. 主要英雄角色 - 动作姿态 ⭐NEW】（强烈建议 · 每角色 3-5 张 · P0）
   - **每个 P0 角色额外提供 3-5 张同一角色的不同动作/姿态/视角**
     例：霍去病 → ① 持枪静立正面 ② 骑马冲锋侧面 ③ 释放技能特效中 ④ 胜利姿态背面 ⑤ 弓骑射箭俯视
   - 用途：Part 2 的 sequence_group（同角色多视角动作连贯组）必须用这些做 reference，
     否则视频生成会变成「同立绘 + 镜头推拉」的伪连贯
   - 格式：keyframe PNG/JPG，≥1K 分辨率
   - **缺这个资产 → Part 2 必然产生"动作顿挫感"**，是已实测教训

【3. 主要兵种 / 怪物 / NPC】（必给 2-3 个 · P1）
   - 如：T5 顶级兵种 / 主力 BOSS / 标志性 NPC
   - 同样建议附 2-3 张同兵种不同战斗姿态（攻击/防御/移动）
   - 用途：Part 2 战场镜头序列组的 reference

【4. 代表性建筑/环境】（必给 1-2 张 · P2）
   - 如：主城 / 战场全景 / 标志地图
   - 同样建议附俯视/平视/特写多角度

【5. LOGO / IP 标识】（必给 1 张 · P2，仅后期合成用）
   - 用途：CTA 段后期合成
   - 备注：AI 视频/图禁止画 LOGO 中文（容易乱码），所有 LOGO 由剪辑师后期添加

【6. 文化/视觉锚定文字描述】（必给 · P0）
   请用一段话回答：
   - Part 1（历史/纪实/科普 / 真人讲解片段）应该是什么文化/时代/服装风格？
     例：ROK → "中国古代各文明，时代-服装对应（汉代-汉服、罗马-罗马甲），禁混入欧美面孔"
     例：WGAME → "现代军事，NATO 标准装备，禁奇幻元素"
   - Part 2（游戏 CG 部分）的视觉风格关键词
     例：ROK → "卡通写实 3D RTS 4X，蓝金主色调，卡牌+大地图"
     例：WGAME → "写实军事 CG，沙漠/城市战，直升机坦克为主"
   - 投放地区的禁词语言
     例：中国境内投放 → 禁英文
     例：阿语区投放 → 禁英文/中文

提交方式（按可用性挑一个）：

A. 飞书 Base 表（最佳，可结构化检索）
   - 提供 base 链接 + 表名 + view/edit 权限

B. 飞书云盘文件夹
   - 上传到指定文件夹，把 folder 链接发我

C. 网盘 / SVN 路径
   - 提供下载链接 + 凭证

D. 直接发 .zip / 微信传文件

谢谢！本 pipeline 单条 60s 视频 ~25 min 跑通，跑出来会立即同步给你审风格。
```

---

## ✅ 拿到资产后做什么

### 1. 整理资产清单 → `manifest.json`（同 Step 2，新增 action_keyframes 字段）

```json
{
  "source": "feishu_base",
  "base_token": "<base_token>",
  "table_id": "<table_id>",
  "table_rev": 658,
  "assets": {
    "099-霍去病": "<file_token of 立绘>",
    "099-霍去病_action_charge": "<file_token of 冲锋动作 keyframe>",
    "099-霍去病_action_skill": "<file_token of 释放技能 keyframe>",
    "099-霍去病_action_archery": "<file_token of 射箭俯视 keyframe>",
    "06-骑兵T5": "<file_token>",
    "06-骑兵T5_action_charging": "<file_token of 冲锋姿态>",
    "06-骑兵T5_action_volley": "<file_token of 放箭姿态>"
  }
}
```

### 2. 写产品配置 `product_config.yaml`

参考 [`prompts/product_config_template.yaml`](product_config_template.yaml)，必填 7 字段：
- `game_name` / `game_genre` / `game_visual_style` / `pivot_keyword_hint` / `target_audience`
- ⭐ `part1_anchor`（Part 1 文化/服装/时代锚定，由宿主提供）
- ⭐ `part2_anchor`（Part 2 游戏画风锚定）
- ⭐ `part1_neg_extra` / `part2_neg_extra`（排除错误文化元素）
- ⭐ `forbidden_language_neg`（按投放地区定）

### 3. 设计 sequence_group → action_keyframe 映射

Step 2 输出 storyboard.json 后，对每个 Part 2 sequence_group 选择一个**主动作 keyframe** 做 reference：

```json
// shot_to_refs_mapping.json (v2)
{
  "AdRev-01": {"立绘": ["099-霍去病"], "动作": ["099-霍去病_action_charge"]},
  "AdRev-02": {"立绘": ["099-霍去病"], "动作": ["099-霍去病_action_charge"]},
  "AdRev-03": {"立绘": ["06-骑兵T5"], "动作": ["06-骑兵T5_action_charging"]}
}
```

同 sequence_group 内的多个镜头共享同一 action_keyframe，让模型理解「连续动作」。

### 4. 跑 02_extract_refs.py 验证

```bash
python scripts/02_extract_refs.py path/to/manifest.json out_dir/
```

成功后 `out_dir/asset_map.json` 含立绘和动作 keyframe 的 `{角色名: liclick_asset_id}`。

---

## 已知各产品资产入口（持续更新）

| 产品 | 资产 base | 主要 table | 动作 keyframe 是否完备 | 联系人 |
|---|---|---|---|---|
| ROK 万国觉醒 | `<your_asset_base_token>` | `<your_hero_table_token>` (英雄/兵种), `<your_env_table_token>` (环境) | **部分** | 待补 |
| Samo 万龙觉醒 | 同上 | `<your_hero_table_token>` (英雄), `<your_env_table_token>` (建筑场景) | 待确认 | 待补 |
| WGAME 战火勋章 | 同上 | 待补 | 待补 | 待补 |
| 你的新产品 | 项目方提供 | 项目方提供 | 待补 | 待补 |

> 接新产品时优先看上表。**动作 keyframe 是否完备**字段若标"待补"或"否"，建议优先和该产品方/美术 owner 沟通补齐，否则 Part 2 sequence_group 必然降级为"伪连贯"。
