"""
Step 2 · 05 - 整合 25 张图 + storyboard.md（含 v2.0 模块落地说明）

输入：storyboard.json + images/
输出：storyboard.md（图文混排，按时间轴 + 段位分组）+ 可选复制到桌面

Usage:
    python 05_integrate.py <out_dir> [desktop_dir]
"""
import json, sys, shutil
from pathlib import Path

OUT_DIR = Path(sys.argv[1])
DESKTOP = Path(sys.argv[2]) if len(sys.argv) > 2 else None
IMG_DIR = OUT_DIR / "images"

data = json.loads((OUT_DIR / "storyboard.json").read_text(encoding="utf-8"))
m = data["meta"]
shots = data["shots"]

SEG_LABELS = {
    "Hook_Counter_Intuitive": "🎬 Hook · 反直觉钩子",
    "Core_Knowledge": "📖 Core_Knowledge · 核心知识",
    "Ad_Reversal": "⚡ Ad_Reversal · 广告反转（Pivot 切点）",
    "Selling_Point": "🎯 Selling_Point · 卖点轰炸",
    "CTA": "📢 CTA · 行动指令",
}

lines = [f"# 分镜表 · {m['video_title']}\n"]
lines.append(f"> **总时长**: {m['total_duration']}s | **镜头数**: {m['shot_count']} | **Pivot**: {m['binary_split']['pivot_second']}s ({m['binary_split']['pivot_ratio']*100:.0f}%)")
lines.append(f"> **应用 codex 模块**: {', '.join(m['codex_modules_applied'])}\n")

lines.append("## 二分结构\n")
lines.append(f"- **Part 1 (0-{m['binary_split']['part1_duration']}s)**: 非游戏铺垫（写实电影感）")
lines.append(f"- **Part 2 ({m['binary_split']['pivot_second']}-{m['total_duration']}s)**: ROK 游戏 CG（卡通写实 3D + ROK reference 图生图）")
lines.append(f"- **Pivot**: Hard_Cut + 强反差（色彩/BGM/能量同步突变）\n")

lines.append("---\n")
lines.append("## 25 镜分镜（含 AI 生成配图）\n")

current_seg = None
for s in shots:
    if s["segment"] != current_seg:
        current_seg = s["segment"]
        lines.append(f"\n### {SEG_LABELS.get(current_seg, current_seg)}\n")
    lines.append(f"#### `{s['shot_id']}` · {s['time_start']}–{s['time_end']}s ({s['duration']}s)\n")
    lines.append(f"![{s['shot_id']}](images/{s['shot_id']}.png)\n")
    lines.append(f"- **画面**：{s['visual_description']}")
    lines.append(f"- **运镜**：`{s['camera']}` | **素材**：`{s['asset_type']}` | **情绪**：`{s['emotional_fuel']}`")
    if s.get("notes"):
        lines.append(f"- **备注**：{s['notes']}")
    lines.append("")

lines.append("---\n")
lines.append("## 后期合成清单（所有文字由剪辑师后期添加）\n")
lines.append("- 全片字幕：每镜按口播原文同步上字幕")
lines.append("- 关键花字 / 高亮词（按 SUB-01 字幕色彩语法：白=信息 / 金=价值 / 红=冲击）")
lines.append("- 游戏 UI 元素（兵力数字 / 倒计时 / 满编标记）")
lines.append("- 角色名字标注")
lines.append("- LOGO + CTA 按钮\n")

(OUT_DIR / "storyboard.md").write_text("\n".join(lines), encoding="utf-8")
print(f"OK -> {OUT_DIR}/storyboard.md")

if DESKTOP:
    DESKTOP.mkdir(parents=True, exist_ok=True)
    (DESKTOP / "images").mkdir(exist_ok=True)
    shutil.copy(OUT_DIR / "storyboard.md", DESKTOP / "storyboard.md")
    shutil.copy(OUT_DIR / "storyboard.json", DESKTOP / "storyboard.json")
    for img in IMG_DIR.glob("*.png"):
        shutil.copy(img, DESKTOP / "images" / img.name)
    print(f"OK -> Desktop: {DESKTOP}")
