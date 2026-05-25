---
name: geek-aspect-adaptation
description: 把 16:9 1080p 视频适配到投放端常用画幅（9:16 / 1:1 / 16:9）。插入 step3 (视频生成) 与 step4 (字幕) 之间。
status: 设计稿 v0.1（待开发实现）
---

# Step 3.5 · 画幅适配 SKILL

> 当前 pipeline 全部输出 1920×1080 16:9，但买量投放至少 3 种画幅。这是缺位的环节。

## 缺位定位

```
step3 视频生成 (16:9 1080p)
    │
    │ ❌ 缺：画幅适配
    │
step4 字幕 (只能在 16:9 上烧)
    │
最终：只有 1 个 16:9 终片
```

## 投放端画幅需求

| 渠道 | 主推画幅 | 次推画幅 | 占比 |
|---|---|---|---|
| TikTok / Reels / Shorts | 9:16 | 1:1 | ~60% |
| Facebook Feed / Instagram | 1:1 / 4:5 | 9:16 | ~20% |
| YouTube TrueView / Twitter | 16:9 | 9:16 | ~20% |

**结论**：必须输出 **9:16 / 1:1 / 16:9** 三套。

## 插入位置

```
step3 (视频生成 16:9 1080p)
    │
    ▼
[step3.5 画幅适配] ← 新增
    │ 输出: video_16x9.mp4, video_9x16.mp4, video_1x1.mp4
    ▼
step4 (字幕渲染，按每个画幅独立)
    │ 输出: final_16x9.mp4 + 字幕, final_9x16.mp4 + 字幕, final_1x1.mp4 + 字幕
```

**Why 插字幕之前**：字幕的位置/字号要按画幅独立调整。9:16 字幕底部 marginV 应该按比例放大，否则字幕会顶到视频底端遮挡画面。

## 3 种适配策略

### 策略 A：center crop（中心裁剪）

```bash
# 16:9 1920×1080 → 9:16 1080×1920
ffmpeg -i in.mp4 -vf "crop=608:1080:656:0,scale=1080:1920" out_9x16.mp4
# 16:9 1920×1080 → 1:1 1080×1080
ffmpeg -i in.mp4 -vf "crop=1080:1080:420:0,scale=1080:1080" out_1x1.mp4
```

**优点**：画质 100% 原生，无损失
**缺点**：左右大量画面被裁，如果主体偏左/右会被切掉

**适用**：step2 分镜时已约束"主体居中安全区"

### 策略 B：blur-pad（黑边 + 模糊背景填充）

```bash
# 16:9 → 9:16 (中央放 16:9 原画 + 上下用同画面模糊填充)
ffmpeg -i in.mp4 -filter_complex "
[0:v]scale=1080:608[fg];
[0:v]scale=1080:1920,boxblur=30:5[bg];
[bg][fg]overlay=0:656[v]
" -map "[v]" -map 0:a out_9x16.mp4
```

**优点**：原画 100% 保留，视觉不突兀
**缺点**：上下大段背景"虚化镜像"，部分平台审核挑刺（"看起来像素材凑数"）

**适用**：原始素材主体偏中或主体动态范围大不能裁

### 策略 C：smart pad（同色填充 + logo/CTA placeholder）

```
9:16 画幅:
┌─────────┐
│ [logo]  │ ← 顶部黑/深色块 + 游戏 logo
│         │
│ 16:9 原画 │
│         │
│ [CTA?]  │ ← 底部留给 step4 字幕 + 可选 CTA 浮动元素
└─────────┘
```

**优点**：商业感强，可植入 logo/CTA
**缺点**：开发成本高（要管 logo 资产 + 排版规则）

**适用**：高预算精修素材

## 推荐策略组合

| 场景 | 策略 | 备注 |
|---|---|---|
| 9:16 主战场（默认） | B blur-pad | 平衡画质与适配 |
| 1:1 Feed | A center crop | 1:1 横向裁剪损失少 |
| 16:9 桌面 | 原片不动 | step3 直出可用 |

## 与 step2 分镜的耦合

**v2.x 增强**：step2 分镜 prompt 加约束"主体居中安全区"（Center Safe Region），让画面主体始终在 1080×1080 中心区域内 → step3.5 可统一用策略 A center crop（无信息损失）。

```yaml
# storyboard prompt 新增字段
center_safe_region:
  width_percent: 56              # 1920 中央 1080 宽（9:16 安全区）
  height_percent: 100            # 全高
  rule: "主体（人物/武器/UI）必须落在中央 1080×1080 安全区内"
```

## 与 step4 字幕的耦合

字幕渲染时根据画幅缩放：

| 画幅 | Fontsize | MarginV | 横向 Margin |
|---|---|---|---|
| 16:9 (1920×1080) | 96 (Normal) | 110 | 40 |
| 9:16 (1080×1920) | 90 (Normal) | 200 | 60 |
| 1:1 (1080×1080) | 88 (Normal) | 100 | 50 |

**Why**：9:16 屏高更大，字幕距底部要留更多空间避开 TikTok UI（点赞/评论/分享按钮区）。

## Pipeline 实现草稿

```python
# scripts/01_aspect_adapt.py
INPUT_16x9 = "video.mp4"
ASPECTS = ["16:9", "9:16", "1:1"]
STRATEGIES = {"16:9": "passthrough", "9:16": "blur_pad", "1:1": "center_crop"}

for aspect in ASPECTS:
    strategy = STRATEGIES[aspect]
    out = f"video_{aspect.replace(':', 'x')}.mp4"
    if strategy == "passthrough":
        shutil.copy(INPUT_16x9, out)
    elif strategy == "center_crop":
        # ffmpeg center crop
        ...
    elif strategy == "blur_pad":
        # ffmpeg filter_complex blur+overlay
        ...
```

## 已知工程注意

1. **音轨保留**：所有画幅都用同一份音轨（mixed.mp3），不要重压
2. **CRF 控制**：blur-pad 会重编码，CRF=20 保画质
3. **元数据保留**：保留原视频的 metadata（duration / fps / 关键帧）
4. **批量并发**：3 种画幅可并发跑，节省时间
5. **TikTok 安全区**：9:16 必须避开顶部 100px + 底部 400px UI 遮挡区

## 与上下游 SKILL 关系

```
step3 (04-视频/SKILL.md)
    │ output: video_16x9_1080p.mp4
    ▼
[step3.5 (本 SKILL，待实现)]
    │ output: video_{16x9,9x16,1x1}.mp4
    ▼
step4 (05-字幕/SKILL.md)
    │ 每个画幅独立渲染字幕
    ▼
final: 3 个画幅 × 1 字幕策略 = 3 个终片
```

## 开发优先级

- **P0 (必做)**：策略 A + B 实现，覆盖 9:16 / 1:1 输出
- **P1 (后续)**：step2 分镜加 center_safe_region 约束 + step4 字幕按画幅缩放
- **P2 (远期)**：策略 C smart pad + logo/CTA 浮动元素

## Open Questions

1. 9:16 是否要做 5:6 / 4:5 子画幅适配？（Facebook 用 4:5）
2. 是否需要自动 saliency detection（用 AI 找主体位置）智能裁剪？
3. logo/CTA 浮动元素的素材库归属哪个 SKILL？
