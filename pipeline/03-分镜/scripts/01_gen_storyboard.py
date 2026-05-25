"""
Step 2 · 01 - 脚本→分镜表（LLM，跨产品通用）

输入：已配音脚本 yaml（含段位/口播）+ 产品配置 yaml（游戏名/风格描述等）
处理：用 LLM 按 codex-v2.1 11 模块转 25 镜分镜表
输出：storyboard.json + storyboard.md（含每镜 visual/camera/asset/emo + 每镜 AI 生图 prompt）

product_config.yaml 示例:
    game_name: "ROK 万国觉醒"
    game_genre: "SLG / 4X 策略"
    game_visual_style: "卡通写实 3D, 卡牌+大地图 RTS, 蓝金主色调"
    pivot_keyword_hint: "万国觉醒里 / 万龙觉醒里 / 战火勋章中"  # 转折句常用产品名/产品宣传句
    target_audience: "全球 SLG 用户"

Usage:
    python 01_gen_storyboard.py <script_yaml> <product_config_yaml> <out_dir>
"""
import json, re, sys, yaml
from pathlib import Path
from openai import OpenAI

SCRIPT_YAML = sys.argv[1]
PRODUCT_YAML = sys.argv[2]
OUT_DIR = Path(sys.argv[3])
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT = Path(SCRIPT_YAML).read_text(encoding="utf-8")
PRODUCT = yaml.safe_load(Path(PRODUCT_YAML).read_text(encoding="utf-8"))
GAME_NAME = PRODUCT.get("game_name", "<游戏名未指定>")
GAME_STYLE = PRODUCT.get("game_visual_style", "<风格未指定>")
PART1_ANCHOR = PRODUCT.get("part1_anchor", "<Part1 文化/服装/时代锚定未指定 — 由宿主在 product_config.yaml 定义>")
PART2_ANCHOR = PRODUCT.get("part2_anchor", GAME_STYLE)
LANG_NEG = PRODUCT.get("forbidden_language_neg", "latin letters, english characters, download")

ROOT = Path(__file__).parent.parent.parent.parent.parent
CODEX_DIR = ROOT / "pipeline/03-分镜/codex-v2.1"
CODEX_01 = (CODEX_DIR / "01-脚本到分镜.md").read_text(encoding="utf-8")
CODEX_06 = (CODEX_DIR / "06-二分结构-BIN.md").read_text(encoding="utf-8")
CODEX_07 = (CODEX_DIR / "07-Hook-0-3s-HMI.md").read_text(encoding="utf-8")
CODEX_08 = (CODEX_DIR / "08-主体延续性-SCT.md").read_text(encoding="utf-8")
CODEX_10 = (CODEX_DIR / "10-匹配剪辑-MAC.md").read_text(encoding="utf-8")

import os
client = OpenAI(
    base_url=os.environ.get("LLM_PROXY_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.environ["LLM_PROXY_API_KEY"],
)

PROMPT = f"""你是极客视觉 codex v2.1 的分镜师。基于已配音脚本 + codex v2.1 的 12 模块规则 + 产品视觉规范，输出完整 25-35 镜分镜表（贴近极客号节奏中位数 1.6s/镜）。

# 产品信息（决定 Part 2 视觉风格）
- **游戏**: {GAME_NAME}
- **视觉风格**: {GAME_STYLE}
- **完整配置**: {json.dumps(PRODUCT, ensure_ascii=False)}

# 已配音脚本
```yaml
{SCRIPT}
```

# codex 关键规则（必须严格遵守）

## 01-脚本到分镜（v1.0 7 模块基础）
{CODEX_01}

## 06-BIN 二分结构（v2.0 新）
{CODEX_06}

## 07-HMI Hook 0-3s 子拆（v2.0 新）
{CODEX_07}

## 08-SCT 主体延续（v2.0 新）
{CODEX_08}

## 10-MAC 匹配剪辑（v2.1 新 · 最关键 · 决定看着是否「不断节奏」）
{CODEX_10}

# 任务

按 codex 推算镜头数（**目标 28-35 镜**，贴近极客号 ASL 1.6s/镜节奏中位数）。每镜输出：
1. shot_id（段位+序号，如 Hook-01）
2. time_start / time_end / duration
3. **sequence_group_id**（v2.1 新 · 同动作序列组编号，从 1 开始）
4. **sequence_action**（v2.1 新 · 该 sequence_group 的「主体+持续动词」命名，全组共享，如 "Han Chinese army marching across snowy plain" / "wheel stuck in mud spinning" / "cavalry charging forward with arrows volleying"。**禁止用主题词如 "ancient warfare difficulties"**）
5. **match_type_to_prev**（v2.1 新 · 与前一镜的匹配关系，枚举：Same_Theme_Multi_Source / Same_Subject_New_State / Action_Match / N_Breakpoint，第一镜填 N/A）
6. visual_description（具体人物/动作/构图/光线/情绪，不模糊；**必须含主体动作进行中的描述**，不能是静态站位）
7. camera（Mixed/Pan/Zoom_In/Zoom_Out/Static）
8. asset_type（Movie_Footage / Game_CG / Motion_Graphics / Live_Action / Static_Image）
9. emotional_fuel（Curiosity / Tension / Desire_Gap / Intellectual_Superiority / Ethnic_Superiority / Nostalgia / None）
10. notes（字幕/花字/特殊效果）
11. image_gen_prompt（中英混合，至少 50 字；**Part 1 镜头必须含 "{PART1_ANCHOR}" 文化锚定**；**Part 2 镜头必须按"{PART2_ANCHOR}"风格**；**同 sequence_group 的镜头必须共享 70% 关键词 + 显式描述主体动作进行中姿态**（蹄子半抬/士兵正用力推/车轮带速度感），不能是静态站位；NEG 含 "{LANG_NEG}, static pose, frozen subject"）

# 必须显式应用 codex v2.1 全部 12 模块，重点 4 个新模块 + 1 个 v2.1 模块

- BIN：Pivot 必须落在 Ad_Reversal 起点，ratio ∈ [40%, 50%]，Hard_Cut + 强反差
- HMI：首 3s 必有视觉锚点对应口播关键词，切 2-3 刀
- SCT：Part1 主体角色在 Part2 用同人物 CG 延续（Same_Character）
- FLU：Part2 每镜画面严格对应口播内容
- **MAC（v2.1 最关键，PoC 修订）**：
  - **MAC-00 同动作多视角**：每个 sequence_group 是「同一持续动作的不同机位」，**不是「同主题不同瞬间」**
    - ✓ "Han cavalry charging" 的 3 机位：正面远 → 战马蹄部俯视 → 列队侧面（**同一动作**）
    - ❌ "古代行军困境" 的 3 镜：运粮全景 → 冰冻骑兵 → 粮草地图（**同主题但跳动作**）
    - 判断标准：sequence_action 是不是「主体 + 持续动词」格式？
  - matched_ratio 目标 ≥ 70%（≥70% 相邻镜头对 match_type 不为 N_Breakpoint）
  - Part1 必须设计 1 个超大序列组（8-15 镜围绕一个持续动作，如「汉军在雪原中持续行军」/「运粮车深陷泥地反复尝试推动」）
  - Part2 设计 2-3 个中型组（每组 3-5 镜围绕同一角色的同一持续动作，如「霍去病释放冲锋技能」/「弓骑兵持续放箭」）
  - 跨段位允许断点（特别是 Pivot 那一刀必须 N_Breakpoint，承接 BIN-03 强反差）

# 镜头数推算（基于极客中位数 ASL 1.6s）

60s 视频建议总镜头数 32-37 镜：
- Hook (0-5s): 2-3 镜
- Part1 CoreK (5-{{pivot}}s): 12-15 镜（**形成 MAC-03 最大序列组**）
- Pivot 后 AdRev (~{{pivot+5}}s): 5-7 镜
- Sell: 7-9 镜
- CTA (最后 4-6s): 2-3 镜

# 输出纯 JSON（不要 markdown 包裹）

{{
  "meta": {{
    "video_title": "string",
    "product": "{GAME_NAME}",
    "total_duration": 60,
    "shot_count": N,
    "binary_split": {{"pivot_second": X, "part1_duration": X, "part2_duration": X, "pivot_ratio": 0.45}},
    "mac_summary": {{"target_matched_ratio": 0.70, "designed_groups": [{{"group_id": 1, "shot_range": "Hook-01..CoreK-12", "theme": "...", "size": 14}}]}},
    "codex_modules_applied": ["BIN-01", "HMI-01", "MAC-01", "MAC-03", ...]
  }},
  "shots": [{{"shot_id":"Hook-01", "segment":"Hook_Counter_Intuitive", "time_start":0.0, "time_end":1.5, "duration":1.5, "sequence_group_id": 1, "sequence_action": "Han Chinese general gazing at retreating army in snow storm", "match_type_to_prev": "N/A", "visual_description":"...", "camera":"Mixed", "asset_type":"Movie_Footage", "emotional_fuel":"Curiosity", "notes":"...", "image_gen_prompt":"..."}}]
}}
"""

resp = client.chat.completions.create(
    model="gemini-3.1-pro-preview",
    messages=[{"role": "user", "content": PROMPT}],
)
raw = resp.choices[0].message.content.strip()
m = re.search(r'\{[\s\S]*\}', raw)
data = json.loads(m.group(0) if m else raw)

(OUT_DIR / "storyboard.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK -> storyboard.json | product={GAME_NAME} | shots={data['meta']['shot_count']} | pivot={data['meta']['binary_split']['pivot_second']}s")
print(f"tokens: prompt={resp.usage.prompt_tokens} completion={resp.usage.completion_tokens}")
