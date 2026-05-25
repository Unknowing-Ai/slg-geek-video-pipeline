# Storyboard Master Prompt（分镜表生成 LLM 提示词）

> 用途：把已配音脚本 + codex v2.0 模块文档喂给 gemini-3.1-pro-preview，输出 25 镜分镜表 JSON

## 完整 Prompt 模板

```
你是极客视觉 codex v2.0 的分镜师。基于已配音脚本 + codex v2.0 的 11 模块规则，输出完整 25 镜分镜表。

# 已配音脚本
{SCRIPT_YAML}

# codex 关键规则（必须严格遵守）

## 01-脚本到分镜（v1.0 7 模块基础）
{codex-v2.1/01-脚本到分镜.md 全文}

## 06-BIN 二分结构（v2.0 新）
{codex-v2.1/06-二分结构-BIN.md 全文}

## 07-HMI Hook 0-3s 子拆（v2.0 新）
{codex-v2.1/07-Hook-0-3s-HMI.md 全文}

## 08-SCT 主体延续（v2.0 新）
{codex-v2.1/08-主体延续性-SCT.md 全文}

# 任务

按 codex 推算镜头数（约 24-28 镜）。每镜输出：
1. shot_id（段位+序号，如 Hook-01）
2. time_start / time_end / duration
3. visual_description（具体人物/动作/构图/光线/情绪，不模糊）
4. camera（Mixed/Pan/Zoom_In/Zoom_Out/Static）
5. asset_type（Movie_Footage / Game_CG / Motion_Graphics / Live_Action / Static_Image）
6. emotional_fuel（Curiosity / Tension / Desire_Gap / Intellectual_Superiority / Ethnic_Superiority / Nostalgia / None）
7. notes（字幕/花字/特殊效果）
8. image_gen_prompt（中英混合，含主体+场景+风格+光线，至少 50 字）

# 必须显式应用 v2.0 4 个新模块

- BIN：Pivot 必须落在 Ad_Reversal 起点，ratio ∈ [40%, 50%]，Hard_Cut + 强反差
- HMI：首 3s 必有视觉锚点对应口播关键词，切 2-3 刀
- SCT：Part1 主体角色在 Part2 用同人物 CG 延续（Same_Character）
- FLU：Part2 每镜画面严格对应口播内容

# 输出纯 JSON（不要 markdown 包裹）

{完整 JSON Schema}
```

## 关键约束

1. **数据真实**：所有时间戳必须基于脚本时长推算，禁止编造
2. **段位严格**：semantic_role 必须从 Hook_Counter_Intuitive / Background / Core_Knowledge / Ad_Reversal / Selling_Point / CTA 选
3. **camera 固定枚举**：禁主观形容词
4. **image_gen_prompt 必须 ≥50 字**：含主体 + 场景 + 风格 + 光线 4 要素
5. **BIN Pivot**：必须明确标 ratio ∈ [40%, 50%]
6. **后期合成清单留 notes**：字幕/花字/LOGO 都在 notes 里描述（AI 不画）

## 生图 prompt 公共后缀（必加）

```
| Clean image without any text, captions, subtitles, logo, watermark, UI text, or written language anywhere in the frame. Pure visual content only.
```

加 negative_prompt（同步禁止）：

```
any text, any words, any letters, any numbers, captions, subtitles, logo, watermark, brand mark, signage, characters, signs, billboards, country flags, political symbols, country names, written language
```
