# 新产品启动 · 跟宿主要资产模板

> 接入新产品（如 WGAME / Samo / 新 IP）跑本 skill 时必备的"前置物料请求清单"
> 把下面这段直接发给该产品的**美术 owner / 项目方制作人**

---

## 📩 一段话发出（拷贝模板）

```
亲爱的 [产品方/美术 owner]，

我在做 [产品名] 的极客号风格 KOL 复刻视频分镜 AI pipeline，
Part 2 (游戏内画面) 的 AI 生图需要用你们官方的资产作 reference（图生图），
否则生成出来的"游戏画面"不像真实游戏，无法用于投放演示或风格审核。

请按下面 6 类提供资产（v1.2 升级 · 优先级高→低）：

【1. 主要英雄角色 - 立绘】（必给 3-6 个 · 优先级 P0）
   - 优先：本期脚本里点名的角色（如脚本说"霍去病""阿帕奇"就给对应资产）
   - 次选：产品旗舰/封面级名将形象
   - 格式：高模 CG 立绘 PNG/JPG，≥1K 分辨率，单人正面构图

【2. 主要英雄角色 - 动作姿态 keyframe】⭐ v1.2 新增（强烈建议 · 每角色 3-5 张 · 优先级 P0）
   - **每个 P0 角色额外提供 3-5 张同角色不同动作/姿态/视角**
     例：霍去病 → ① 持枪静立正面 ② 骑马冲锋侧面 ③ 释放技能特效中 ④ 胜利姿态背面 ⑤ 弓骑射箭俯视
   - 用途：Part 2 的 sequence_group（同角色多视角动作连贯组）reference，
     缺这个资产 → 生成的"游戏画面"会变成"同立绘+镜头推拉"的伪连贯（已实测教训）
   - 格式：keyframe PNG/JPG，≥1K 分辨率

【3. 主要兵种 / 怪物 / NPC】（必给 2-3 个 · 优先级 P1）
   - 如：T5 顶级兵种 / 主力 BOSS / 标志性 NPC
   - 建议附 2-3 张同兵种不同战斗姿态（攻击/防御/移动）
   - 用途：Part 2 战场镜头序列组的 reference

【4. 代表性建筑/环境】（必给 1-2 张 · 优先级 P2）
   - 如：主城 / 战场全景 / 标志地图
   - 建议附俯视/平视/特写多角度
   - 用途：大地图 / 城建相关镜头的 reference

【5. LOGO / IP 标识】（必给 1 张 · 优先级 P2，仅后期合成用）
   - 用途：CTA 段后期合成
   - 备注：AI 图禁止画 LOGO 中文（容易乱码），所有 LOGO 由剪辑师后期添加

【6. 文化/视觉锚定文字描述】⭐ v1.2 新增（必给 · 优先级 P0）
   请用一段话回答 3 个问题：
   a) Part 1（历史/纪实/科普片段）应该是什么文化/时代/服装风格？
      例：ROK → "中国古代各文明，时代-服装对应（汉代-汉服、罗马-罗马甲），禁混入欧美面孔"
      例：WGAME → "现代军事，NATO 标准装备，禁奇幻元素"
      例：Samo → "西方中世纪奇幻，巨龙骑士魔法师"
   b) Part 2（游戏 CG）的视觉风格关键词
      例：ROK → "卡通写实 3D RTS 4X，蓝金主色调，卡牌+大地图"
      例：WGAME → "写实军事 CG，沙漠/城市战，直升机坦克为主"
   c) 投放地区的禁词语言
      例：中国境内 → 禁英文；阿语区 → 禁英文+中文+中文字符
   → 这 3 项写进 product_config.yaml 的 part1_anchor / part2_anchor / forbidden_language_neg 字段

提交方式（按可用性挑一个）：

A. 结构化数据表（最佳，可检索）— 飞书 Base / Airtable / Notion DB
   - 提供 base/database 链接
   - 告诉我要拿哪个 table（如 "ROK 英雄&兵种" 表）
   - 给我 view/edit 权限

B. 云盘文件夹 — 飞书云盘 / Google Drive / Dropbox
   - 上传到指定文件夹，把 folder 链接发我

C. 网盘 / SVN / 版本控制路径
   - 提供下载链接 + 凭证

D. 直接发 .zip / 微信传文件

如方便，请额外补充：
- 游戏视觉风格的一句话描述（如"卡通写实 3D, 蓝金主色调, 卡牌+大地图 RTS"）
- 一段 CTA 段标准合规话术 + 官方 LOGO 高清 PNG

谢谢！本 pipeline 单条 60s 视频 ~13 min 跑通，跑出来会立即同步给你审风格。
```

---

## ✅ 拿到资产后做什么

### 1. 整理资产清单 → `manifest.json`

```json
{
  "source": "feishu_base",
  "base_token": "<从 base URL 提取, 如 <your_asset_base_token>>",
  "table_id": "<拉 lark-cli base +table-list 查到>",
  "table_rev": 658,
  "_comment": "拿 lark-cli base +base-get 查 rev",
  "assets": {
    "001-XXX 英雄": "<file_token>",
    "002-XXX 兵种": "<file_token>",
    "003-XXX 建筑": "<file_token>"
  }
}
```

**怎么拿 file_token**：

```bash
# 列出 base 下所有表
lark-cli base +table-list --base-token <base_token> --limit 50

# 拉某个表的 records（含 file_token）
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --limit 100
```

记录里 `image.png` 那个字段对应的 dict 里的 `file_token` 就是要的。

### 2. 写产品配置 `product_config.yaml`

```yaml
game_name: "<产品中英文全名>"
game_genre: "<品类，如 SLG/4X 策略 / 模拟经营 / 卡牌 RPG>"
game_visual_style: "<一句话描述视觉风格，影响所有 Part 2 镜头的 prompt 后缀>"
pivot_keyword_hint: "<转折句常用关键词，如 '万国觉醒里' / '战火勋章中' / '万龙觉醒里'>"
target_audience: "<目标受众，如 '全球 SLG 用户' / '欧美军事题材爱好者'>"
```

### 3. 跑 02_extract_refs.py 验证

```bash
python scripts/02_extract_refs.py path/to/manifest.json out_dir/
```

成功后 `out_dir/asset_map.json` 会有 `{角色名: liclick_asset_id}`，后续 03_genimg.py 直接用。

---

## 已知各产品资产入口（项目方维护）

| 产品 | 资产入口 | 联系人 |
|---|---|---|
| 你的产品 | 项目方提供 | 跟项目方/美术 owner 要 |
| 已部署 example | examples/古代将军_v3/ | 见 product_config.yaml |

> 接新产品时优先看本表，没有的找该产品方/美术 owner 索要。每次接入完补一行回来。具体 ID 不在仓库公开，向项目方索取。
