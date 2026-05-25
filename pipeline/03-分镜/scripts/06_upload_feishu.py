"""
Step 2 · 06 - 飞书 docx 创建 + 25 图嵌入

策略：
- 用 lark-cli docs +create 创建 docx + 初始 markdown（标题/概述/对比表）
- 循环每镜：先 +update --mode append 加 heading + 描述，再 +media-insert 加图（按时间顺序）
- lark-cli +media-insert 只能从 cwd 相对路径上传，所以 cwd 切到 images/

输入：storyboard.json + images/
输出：飞书 docx URL（owner = 当前 user，无需额外加权限）

Usage:
    python 06_upload_feishu.py <out_dir> <title>
"""
import json, subprocess, sys, time
from pathlib import Path

OUT_DIR = Path(sys.argv[1])
TITLE = sys.argv[2]
IMG_DIR = OUT_DIR / "images"

data = json.loads((OUT_DIR / "storyboard.json").read_text(encoding="utf-8"))
m = data["meta"]
shots = data["shots"]

INITIAL = f"""# {TITLE}

> **总时长**: {m['total_duration']}s | **镜头数**: {m['shot_count']} | **Pivot**: {m['binary_split']['pivot_second']}s ({m['binary_split']['pivot_ratio']*100:.0f}%)
> **应用 codex 模块**: {', '.join(m['codex_modules_applied'])}

## 二分结构

- **Part 1 (0-{m['binary_split']['part1_duration']}s)**: 非游戏铺垫（写实电影感）
- **Part 2 ({m['binary_split']['pivot_second']}-{m['total_duration']}s)**: ROK 游戏 CG（卡通写实 3D + ROK reference 图生图）
- **Pivot**: Hard_Cut + 强反差

## 后期合成（AI 图禁画文字，全部由后期添加）

- 全片字幕 / 关键花字 / 游戏 UI 元素 / 角色名字 / LOGO + CTA 按钮

---

## 25 镜分镜（图文混排）
"""

r = subprocess.run([
    "lark-cli", "docs", "+create",
    "--title", TITLE,
    "--markdown", INITIAL,
], capture_output=True, text=True, timeout=120)
obj = json.loads(r.stdout.strip())
doc_token = obj["data"]["doc_id"]
doc_url = obj["data"].get("doc_url", f"https://your-org.feishu.cn/docx/{doc_token}")
print(f"docx: {doc_url}")

SEG_LABELS = {
    "Hook_Counter_Intuitive": "🎬 Hook · 反直觉钩子",
    "Core_Knowledge": "📖 Core_Knowledge · 核心知识",
    "Ad_Reversal": "⚡ Ad_Reversal · 广告反转（Pivot 切点）",
    "Selling_Point": "🎯 Selling_Point · 卖点轰炸",
    "CTA": "📢 CTA · 行动指令",
}

current_seg = None
for i, s in enumerate(shots, 1):
    if s["segment"] != current_seg:
        current_seg = s["segment"]
        seg_md = f"\n### {SEG_LABELS.get(current_seg, current_seg)}\n"
        subprocess.run(["lark-cli", "docs", "+update", "--doc", doc_token,
                        "--mode", "append", "--markdown", seg_md],
                       capture_output=True, text=True, timeout=60)
        time.sleep(0.3)

    shot_md = f"""
#### `{s['shot_id']}` · {s['time_start']}–{s['time_end']}s ({s['duration']}s)

- **画面**：{s['visual_description']}
- **运镜**：`{s['camera']}` | **素材**：`{s['asset_type']}` | **情绪**：`{s['emotional_fuel']}`
"""
    if s.get("notes"):
        shot_md += f"- **备注**：{s['notes']}\n"
    subprocess.run(["lark-cli", "docs", "+update", "--doc", doc_token,
                    "--mode", "append", "--markdown", shot_md],
                   capture_output=True, text=True, timeout=60)
    time.sleep(0.3)

    r2 = subprocess.run(["lark-cli", "docs", "+media-insert", "--doc", doc_token,
                         "--file", f"{s['shot_id']}.png",
                         "--caption", f"{s['shot_id']} · {s['time_start']}–{s['time_end']}s",
                         "--align", "center"],
                        capture_output=True, text=True, timeout=120, cwd=str(IMG_DIR))
    print(f"  [{i}/{len(shots)}] {'✓' if r2.returncode == 0 else '✗'} {s['shot_id']}")
    time.sleep(0.5)

print(f"\n完成。docx: {doc_url}")
