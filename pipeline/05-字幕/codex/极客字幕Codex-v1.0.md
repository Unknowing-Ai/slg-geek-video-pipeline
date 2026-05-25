# 极客字幕 Codex v1.0（候选，5 条 PoC 抽取）

> **状态**：候选草案，基于 5 条 Tier 1 样本（ROK_头_01 / ROK_头_05 / ROK_尾_07 / WGAME_头_13 / Samo_头_23）抽取。
> **下一步**：用户审阅 → 通过则扩量到 20-30 条复核 → 锁定 v1.0 正式版。

---

## 一、硬规则（5/5 或 4/5 一致，可直接落 schema）

### 1. 位置（5/5 一致）

```yaml
position:
  vertical_region: bottom_third  # 5/5
  horizontal: center             # 5/5
  y_percent_from_top: 85         # 4/5（尾07 因 CTA 段位会上移到 75% / 跟随画面元素）
  stability: 非常稳定，整条视频位置不漂移
```

### 2. 颜色（5/5 完全一致）

```yaml
color:
  main_hex: "#FFFFFF"            # 白字
  stroke_hex: "#000000"          # 黑描边
  stroke_width: medium           # 4/5 medium；尾07 thick
  shadow: true                   # 4/5 有阴影
  background: none               # 5/5 无背景色块
```

### 3. 字号（4/5 一致）

```yaml
size:
  height_percent_of_frame: 6     # 4/5（尾07 CTA 段为 10%）
  category: medium               # 4/5（尾07 large）
  scaling_variation: 极少         # 头部段位字号恒定，无缩放变化
```

### 4. 字体（4/5 一致）

```yaml
font:
  weight: bold                   # 5/5 全部加粗
  style_category: modern_sans    # 4/5 现代无衬线（尾07 impact_style 倾斜加粗）
  family_candidates:
    - 思源黑体（Source Han Sans Bold）
    - 阿里巴巴普惠体（Alibaba PuHuiTi Bold）
    - 微软雅黑（Microsoft YaHei Bold）
  notes: 无衬线、粗体、清晰易读，无装饰
```

### 5. 切换（5/5 一致）

```yaml
switching:
  method: hard_cut                # 5/5 硬切，无淡入淡出
  in_animation: static            # 4/5（尾07 popup）
  out_animation: static           # 5/5
  alignment_to_speech: 严格对齐    # LLM 全部判定"话起字出，话落字收"
```

### 6. 时间精度（4/5 实测数据）

| 指标 | 中位数 | 说明 |
|---|---|---|
| 字幕领先口播 (lead_ms) | -200 ~ +59 ms | 几乎零延迟 |
| 字幕切换 vs 口播停顿对齐率 | 53-83% | 平均 ~70% 切换点严格踩在句末 |
| 最大空档 (median_gap_ms) | 0 ms | 无明显字幕真空段 |
| 是否逐字 | Y (4/5) | 字幕字数 ≈ 口播字数（85-115% 之间） |

### 7. 单行字数上限（5/5）

```yaml
line:
  max_chars_per_line: 22         # 中位数，范围 16-25
  max_simultaneous_lines: 1      # 4/5 单行（尾07 双行）
```

---

## 二、段位级差异（CTA / 强情绪段位特殊样式）

**触发条件**：尾段（CTA / 情绪 climax / 卖点强植入段）

**样式差异**：

```yaml
cta_segment_overrides:
  size: large (≈10% 屏高，比 normal 大 60%)
  font:
    style_category: impact_style
    weight: extra_bold
    italic: true
  animation:
    in_animation: popup                # 弹出放大动画
    default_duration_ms: 100
  highlight:
    method: combo (color_change + size_change)
    highlight_color_hex: "#FF0000"     # 红色（normal 段位用 #FFD700 黄色）
    trigger_frequency: 高              # 几乎每条都高亮
  background_position: 偶尔跟随画面人物 / 居中铺满（前 2s）
```

---

## 三、高亮规则（3/5 启用，2/5 不启用）

**启用 vs 不启用的差异**：
- **ROK / WGame 系**：启用高亮（品牌词/武将名/数字/金句）
- **Samo（魔幻题材）+ WGAME 实拍**：可不启用（依赖画面本身视觉冲击）

**启用时的细则**：

```yaml
highlight_rule:
  applied_to_categories:
    - 品牌词 (如"万国觉醒"、"霍去病")
    - 武将/历史人名
    - 数字 (战绩、规模)
    - 金句 (情绪重音、爆点词)
    - 情绪词 (CTA 段位)
  method:
    normal_segment: color_change           # 头部用单色变色
    cta_segment: combo (color + size + popup)
  highlight_color:
    normal: "#FFD700"                       # 金黄色
    cta: "#FF0000"                          # 警示红
  trigger_frequency:
    normal: 中（关键节点触发）
    cta: 高（密集触发）
```

---

## 四、画面中央"飞字大字"补充模块（来自 ROK_头_05 观察）

LLM 标注 ROK_头_05 有 "画面中央的大字弹出版式"（如"闪电战"、"霍去病"用毛笔书法体居中弹出）。

**这是底部常规字幕之外的独立模块**，schema 需补字段：

```yaml
center_callout:
  is_used: false                   # 默认关
  trigger: 强卖点 / 转折点关键词
  position: center (画面中央)
  size: XL (≈15-20% 屏高)
  font: brush_script / impact (与底部字幕不同)
  duration_ms: 500-1500
  animation: popup_zoom_in + popup_zoom_out
```

---

## 五、画风美感"标志性特征"（LLM 主观判断聚合）

> 三个高频"极客 signature" tag（按出现频次排序）：

1. **硬核直接、信息优先** — 4/5 都强调"清晰易读 > 装饰花哨"，与买量"打 CTR/CVR"目标一致
2. **底边稳定 + 偶发中央大字** — 双轨：底部稳定走口播，中央偶发强化卖点
3. **描边+阴影应对复杂背景** — 5/5 都有黑描边，4/5 有阴影，保证画面再花字幕也能看清

---

## 六、Pipeline 自动渲染参考（Step 4 实现侧）

```yaml
ass_subtitle_default_style:
  Fontname: "Source Han Sans CN Bold"
  Fontsize: 56                     # 1080p 高度 1080 × 6% / 8 (单 5em 高)
  PrimaryColour: "&H00FFFFFF"      # 白
  OutlineColour: "&H00000000"      # 黑描边
  Outline: 3                       # medium 描边
  Shadow: 2
  Alignment: 2                     # 底部居中
  MarginV: 80                      # 距底部 ≈ 屏高 7%
  Bold: 1

ass_subtitle_cta_style:
  Fontname: "Source Han Sans CN Heavy"  # 或 impact
  Fontsize: 96                     # large
  PrimaryColour: "&H000000FF"      # 红
  Outline: 5
  Italic: 1
  Bold: 1
```

---

## 七、PoC 局限 + 待全量验证项

| 局限 | 当前样本表现 | 全量验证目标 |
|---|---|---|
| 样本量 5 | 4/5 一致已能形成 codex 雏形 | 扩 20-30 条验证段位级差异是否稳定 |
| 高亮规则 5/3 | 仅 60% 启用，标准化空间大 | 全量统计：哪类产品/题材必启用？ |
| 中央飞字模块 | 仅 1 条明确观察 | 全量看是否多条都有，能否标准化 |
| LLM 时间戳异常 1/5 | ROK_头_05 输出归一化为 0-0.09s | 加 sanity check + 异常重试 |
| 字幕字号绝对值 | LLM 给"屏高百分比"估值 | 全量需 OCR 抽 bbox 拿像素级精确高度 |

---

## 八、结论

PoC 通过条件 ✅：
1. Schema 覆盖度足够（5 维全部能稳定填）
2. 硬规则有 5-6 项 4/5 以上一致 → 直接落 codex
3. 段位级差异（CTA 特殊样式）能稳定识别
4. 异常率 1/5（LLM 时间戳归一化）可通过工程手段修复

**建议**：扩量到 25-30 条 → 验证 CTA 段位规则 + 高亮规则的产品/题材分布 → 锁定 codex v1.0 正式版 → 写 step4 SKILL + 实现 ass 渲染 pipeline。
