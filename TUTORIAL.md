# 部署教程 — 从 0 到出第 1 条视频

> 完全新手版。跟着抄就行。
>
> 走完全部 6 步约 **2-3 小时**（含账号申请等待时间）。

---

## 流程概览

```
[准备阶段]
第 0 步：装机器 + 软件 (15 分钟)
第 1 步：下载仓库 (5 分钟)
第 2 步：装 Python 依赖 (10 分钟)
第 3 步：装思源黑体 (5 分钟)
第 4 步：申请 API key + 配置 .env (30-60 分钟，含等待)

[实战阶段]
第 5 步：跑现成示例（ROK 古代将军）(1 小时)
第 6 步：换个游戏跑（你的产品）(2-3 小时第 1 次；熟练后 1 小时)
```

---

## 第 0 步：你需要的硬件 + 软件

### 硬件

- 一台电脑（Windows / Mac / Linux 都行）
- 8GB 内存 + 10GB 硬盘空间
- 能联网（视频生成 API 比较吃带宽）

### 软件（必装）

| 软件 | 干啥用 | 装法 |
|---|---|---|
| Python 3.11+ | 跑所有脚本 | https://python.org 下载安装 |
| Git | 下载仓库 | https://git-scm.com 下载 |
| ffmpeg | 处理音视频 | Win: `choco install ffmpeg` · Mac: `brew install ffmpeg` · Linux: `sudo apt install ffmpeg` |
| GitHub CLI (gh) | 操作 GitHub | https://cli.github.com 下载（或 `brew install gh`） |
| Claude Code (可选) | 让 Agent 自动跑流水线 | `npm install -g @anthropic-ai/claude-code` |

### 软件（可选）

| 软件 | 干啥用 |
|---|---|
| VS Code | 看代码 / 改 .yaml 配置 |
| Chrome / Edge | 看生成的视频 |
| Notion / Obsidian | 写自己的方法论扩展 |

---

## 第 1 步：把仓库下载到电脑

打开终端（Win 用 PowerShell / Mac 用 Terminal / Linux 用 bash），输入：

```bash
# 找个你喜欢的目录（这里假设放在 ~/projects）
mkdir -p ~/projects
cd ~/projects

# 第一次用 GitHub CLI 要登录
gh auth login
# 选择: GitHub.com / HTTPS / Login with browser → 跟着浏览器走

# 下载仓库
gh repo clone Unknowing-Ai/rok-geek-prompt-kit
cd rok-geek-prompt-kit
```

**验证成功**：输入 `ls`，看到 `README.md`, `TUTORIAL.md`, `output/` 等文件夹即成功。

如果你也想要公开版（无敏感信息）：

```bash
gh repo clone Unknowing-Ai/slg-geek-video-pipeline
```

---

## 第 2 步：装 Python 依赖

```bash
# 在仓库根目录
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate              # Linux / Mac
# 或 Win: .venv\Scripts\activate

# 升级 pip
pip install -U pip

# 装核心库（按 SKILL 需要装）
pip install openai faster-whisper jieba pyyaml
```

**验证成功**：

```bash
python -c "import openai; import faster_whisper; import yaml; import jieba; print('OK')"
```

看到 `OK` 即成功。第一次 `faster-whisper` 加载会下载模型（~80MB），耐心等。

---

## 第 3 步：装思源黑体（字幕用）

```bash
# 创建用户字体目录
mkdir -p ~/.fonts

# 下载思源黑体 Bold + Heavy
cd ~/.fonts
curl -L -o SourceHanSansSC-Bold.otf \
  https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf
curl -L -o SourceHanSansSC-Heavy.otf \
  https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Heavy.otf

# 刷新字体缓存
fc-cache -fv ~/.fonts

# 验证
fc-list | grep "Source Han"
```

**预期输出**：看到 `Source Han Sans SC:style=Bold` 和 `Source Han Sans SC Heavy:style=Heavy` 即成功。

**Windows 用户**：双击 .otf 文件，点"安装"。

**Mac 用户**：双击 .otf 文件，Font Book 自动安装。

---

## 第 4 步：申请 API key + 配置 .env

### 4.1 复制环境变量模板

```bash
cd ~/projects/rok-geek-prompt-kit
cp .env.example .env
```

### 4.2 申请各服务 API key

下面 4 个服务都要申请（除非你只想跑部分 step）：

#### A. LLM（OpenAI 兼容，用于 step2 分镜 + step4 字幕）

**推荐方案 1：用 Anthropic Claude**
- 注册：https://console.anthropic.com
- 创建 API Key → 拷贝
- 填 `.env`：
  ```
  LLM_PROXY_BASE_URL=https://api.anthropic.com/v1
  LLM_PROXY_API_KEY=sk-ant-xxxxx
  ```

**推荐方案 2：用 Google Gemini**
- 注册：https://aistudio.google.com/apikey
- 拷贝 API Key
- 填 `.env`：
  ```
  LLM_PROXY_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
  LLM_PROXY_API_KEY=AIzaSyXXXXX
  ```

**推荐方案 3：用 LiteLLM Proxy 自建（多模型路由）**
- 安装：`pip install litellm`
- 起服务：`litellm --model claude-opus-4 --port 4000`
- 填 `.env`：
  ```
  LLM_PROXY_BASE_URL=http://localhost:4000
  LLM_PROXY_API_KEY=sk-anything-it-just-needs-to-be-set
  ```

#### B. 火山引擎 ICL TTS（用于 step1 配音克隆）

1. 注册火山引擎账号：https://www.volcengine.com
2. 进控制台 → 找"语音技术" → 申请"语音合成 TTS - 大模型音色定制"
3. 拿到 `appid` + `access_token` + `cluster=volcano_icl`
4. 填 `.env`：
   ```
   VOLC_ICL_API_KEY=你的_access_token
   ```

**克隆音色（首次必做）**：
- 准备 30 秒目标人声样本（mp3，单人清晰说话）
- 运行：`python pipeline/02-配音/scripts/clone_voice.py 你的样本.mp3`
- 等待 5-10 分钟训练完成
- 拿到 `speaker_id`（形如 `S_xxxxx`），填 `.env`：
  ```
  VOLC_SPEAKER_ID=S_xxxxx
  ```

#### C. 视频生成 API（step3）

**方案 1：快手 kling 直连**
- 申请：https://klingai.kuaishou.com → 开发者中心
- 获取 access_key + secret_key
- 填 `.env`：
  ```
  KLING_ACCESS_KEY=xxx
  KLING_SECRET_KEY=xxx
  ```

**方案 2：字节火山 Ark（doubao-seedance）**
- 注册：https://console.volcengine.com/ark
- 获取 API key
- 填 `.env`：
  ```
  VOLC_ARK_API_KEY=xxx
  ```

**方案 3：内部用户用 Atlas Skillhub**
- 需要公司内网访问权限
- 找你公司的 AI 工程团队配置

⚠️ **绝对不要把 `.env` 文件上传 GitHub**。仓库的 `.gitignore` 已经帮你屏蔽了，但 commit 前 `git status` 看一眼有没有意外加进来。

### 4.3 验证 .env 配置

```bash
# 看 .env 内容（别截图发人！）
cat .env

# 测 LLM 是否能连
python -c "
import os, openai
from pathlib import Path
# 简单加载 .env
for line in Path('.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v = line.split('=', 1)
        os.environ[k.strip()] = v.strip()
client = openai.OpenAI(base_url=os.environ['LLM_PROXY_BASE_URL'], api_key=os.environ['LLM_PROXY_API_KEY'])
print(client.models.list().data[0].id)
"
```

看到模型名（如 `claude-opus-4-7` / `gemini-3.1-pro-preview`）即配置成功。

---

## 第 5 步：跑一条示例视频（用现成的 ROK 古代将军）

### 5.1 用 Claude Code 自动跑（推荐）

进 Claude Code，告诉它：

```
帮我用 pipeline/03-分镜/examples/古代将军_v3/ 的配置，
跑通整个 5 步流水线出一条视频。环境变量已配在 .env，请加载。
```

Claude Code 会按 master SKILL（`pipeline/SKILL.md`）跑：

| 步骤 | 耗时 | 成本 | 输出 |
|---|---|---|---|
| 第 1 步 写脚本 | 30 秒 | ~¥0.1 | script.yaml |
| 第 2 步 配音 | 1 分钟 | ~¥0.5 | final_60s_mixed.mp3 |
| 第 3 步 拆分镜 + 生图 | 5-10 分钟 | ~¥15 | storyboard.json + images/ |
| 第 4 步 生成视频 | 30-40 分钟 | ~¥80-100 | BGM完整版.mp4 |
| 第 5 步 上字幕 | 30 秒 | ¥0 | 字幕版.mp4 |
| **合计** | **~1 小时** | **~¥100** | |

**关键**：每步会暂停让你审产物再继续。看不顺眼可以让 Claude Code 重跑那步。

### 5.2 不用 Claude Code，手动一步步跑

按 master SKILL 文档指引，依次执行：

```bash
cd ~/projects/rok-geek-prompt-kit

# Step 1 配音
python pipeline/02-配音/scripts/tts_volc_icl.py $VOLC_SPEAKER_ID

# Step 2 分镜
python pipeline/03-分镜/scripts/01_gen_storyboard.py \
  pipeline/02-配音/script_60s_validate.yaml \
  pipeline/03-分镜/examples/古代将军/product_config.yaml \
  pipeline/03-分镜/examples/古代将军_v3/

# Step 3 视频（按你装的视频 API 改 script）
# ... 详见 04-视频/SKILL.md

# Step 4 字幕（用现成 v3 视频测）
python pipeline/05-字幕/scripts/03_apply_codex_from_script.py
```

### 5.3 验证：你应该拿到的产物

- **音频**：`pipeline/02-配音/tts_output/final_60s_mixed.mp3` (~640KB)
- **分镜**：`pipeline/03-分镜/examples/古代将军_v3/storyboard.json` (~25KB)
- **图片**：`images/Hook-01.png` ~ `images/CTA-03.png` (28 张, ~5MB 每张)
- **视频**：`pipeline/04-视频/v3_full/古代将军_v3_BGM完整版.mp4` (~70MB)
- **字幕成片**：`pipeline/05-字幕/step2-端到端-v3字幕/古代将军_v3_字幕版_V4.mp4` (~65MB)

---

## 第 6 步：换个游戏跑

### 6.1 复制配置模板

```bash
cd pipeline/04-视频/prompts/

# 复制到你自己的产品目录
cp product_config_template.yaml ~/我的新游戏/product_config.yaml
```

### 6.2 改 6 个必填字段

打开 `~/我的新游戏/product_config.yaml`：

```yaml
# 基础 3 字段
game_name: "你的游戏名"
  # 例：万龙觉醒 / 战火勋章 / 我的新游

game_genre: "SLG / 4X 策略"
  # 例：模拟经营 / 卡牌 RPG / 生存策略

target_audience: "目标人群描述"
  # 例：中国市场，男性 25-45，历史/军事爱好者

# 视觉锚定 3 字段（关键！决定 AI 生成的画风）
part1_anchor: "Part 1（历史/纪实段）的视觉风格描述"
  # 例（古代题材）: "古代中国汉朝纪实风格，汉族角色，时代准确服装"
  # 例（魔幻题材）: "西方魔幻战场，骑士甲胄，史诗风格"
  # 例（科幻题材）: "Cyberpunk neon city, futuristic suits"

part2_anchor: "Part 2（游戏 CG 段）的视觉风格描述"
  # 例（卡通 3D）: "卡通写实 3D RTS CG，蓝金主色调"
  # 例（暗黑）: "Dark grimdark ARPG CG, red-black palette"
  # 例（二次元）: "Anime cel-shaded, vibrant colors"

part1_neg_extra: "Part 1 禁止出现的元素"
  # 例: "非亚洲人，欧洲面孔，现代服饰"
  # 例: "modern military, real-world flags"
```

### 6.3 准备 60 秒脚本

**方案 1：用 round1 prompt 套件让 AI 写**
- 把 round1 仓库的 5 个 prompt 文件拼起来给 Claude / GPT
- 给它你的产品 + 卖点 + 题材偏好
- 它会输出符合极客号风格的 60 秒脚本 YAML

**方案 2：参考现成 script 改**
- 复制 `pipeline/02-配音/script_60s_validate.yaml`
- 改里面的 5 段文本，保持 5 段位结构（Hook / CoreK / AdRev / Sell / CTA）
- 字数对照 actual_chars 字段，别差太多（影响配音时长对齐）

### 6.4 准备 30 秒音色样本

- 找一段 30 秒目标音色（任何说中文的人声音频）
  - 来源：极客号视频抽干声 / 配音演员样本 / 你自己录
- 保存为 `voice_sample.mp3`
- 跑 `clone_voice.py` 训练新音色（5-10 分钟）

### 6.5 跑整条流水线

```bash
# 用 Claude Code（最省事）
"用 ~/我的新游戏/product_config.yaml + 我准备的 script.yaml + voice_sample.mp3，跑整个 5 步流水线"

# 或手动跑 5 步
```

**第一次跑预计 2-3 小时**（含每 step 审核停顿），熟练后 1 小时跑通。

---

## 常见问题（FAQ）

### Q: 跑第 3 步报错 "atlas-skillhub 502 / 413"

A: 视频生成 API 偶尔抽风：
- **502**：API 临时过载 → 让 Claude Code 重跑那一镜
- **413**：图片太大 → 检查 PNG 是否 > 1MB，如果是先用 ffmpeg 压成 JPG <1MB
- 或者切换模型（kling ↔ seedance）

### Q: 字体显示成方块怎么办

A: 思源黑体没装好。回到第 3 步：
- 检查 `fc-list | grep "Source Han"` 是否能看到
- 如果看不到，重新跑 `fc-cache -fv ~/.fonts`
- Windows 用户记得双击 .otf 安装

### Q: 配音听起来不像目标音色

A:
- 检查 `.env` 里的 `VOLC_SPEAKER_ID` 是不是你最新克隆的那个
- 训练样本质量不够好（背景噪音/多人混音）→ 重新准备一段 30 秒纯净人声
- 详见 `02-配音/SKILL.md`

### Q: 字幕跟口播对不上

A:
- 检查 `05-字幕/scripts/03_apply_codex_from_script.py` 里的 `SEG_TIMES`
- 这是你视频内各段位的起止时间（秒）
- 用 `ffprobe -i your_video.mp4` 看实际时长，反推每段位时间
- 详见 `05-字幕/SKILL.md`

### Q: AI 生成的画面里有英文乱码 / Download 按钮

A: codex 防线没生效。检查：
- `product_config.yaml` 的 `forbidden_language_neg` 是否填了 `"latin letters, english characters, download"`
- step3 视频生成的 negative prompt 是否包含这条
- 详见 `04-视频/docs/方法论.md` 5 大铁律

### Q: 视频里的人物种族 / 服装不对

A: codex 视觉锚定没生效。检查：
- `product_config.yaml` 的 `part1_anchor` 是否描述清楚目标文化
- `part1_neg_extra` 是否列出禁止元素
- 跑 storyboard 时 LLM 是否把锚定信息放进 image_gen_prompt 里
- 看 `pipeline/03-分镜/codex-v2.1/` 的 SCT 模块

### Q: 我想看每一步的成本明细

A:

| 步骤 | API | 单次成本 | 时间 |
|---|---|---|---|
| 第 1 步 脚本 | LLM (Claude/Gemini) | ~¥0.1 | 30 秒 |
| 第 2 步 配音 | 火山 ICL TTS | ~¥0.5 | 1 分钟 |
| 第 3 步 拆分镜 + 生图 | LLM + 莉刻/Bytedance 生图 | ~¥15 | 5-10 分钟 |
| 第 4 步 生成视频 | kling × 14 + doubao × 14 | ~¥80-100 | 30-40 分钟 |
| 第 5 步 字幕 | （本地跑，无 API） | ¥0 | 30 秒 |
| **合计** | | **~¥100** | **~1 小时** |

### Q: 想批量跑多条视频

A: 写个外层 for 循环：

```python
for product_config in [config1, config2, config3]:
    for script in [script_a, script_b]:
        run_full_pipeline(product_config, script)
```

注意：成本是 N×M 倍。

### Q: 想接入 A/B 实验跟数据回流

A: 这是 Phase 5 的工作（见 README 末尾）。当前 v0.9.1 只到出片，不含投放归因。

---

## 进阶玩法

跑通基础流程后，可以：

1. **调字幕样式**：改 `05-字幕/scripts/03_apply_codex_from_script.py` 里的 `ASS_HEADER` 字段
2. **加新画风**：改 `part1_anchor` / `part2_anchor`，做不同朝代/题材
3. **批量出片**：写外层 for 循环，多 product_config × 多 script 跑
4. **9:16 适配**：等 [step3.5 画幅适配](./pipeline/04.5-画幅/SKILL.md) 开发完
5. **加新 KOL 风格**：用同一套架构拆解另一个 KOL，建 `output/{新KOL}-v0.x/`

---

## 出错了找谁

- **API key 申请问题** → 各服务商客服（火山引擎 / OpenAI / Anthropic / 快手）
- **流水线代码 bug** → 仓库 Issue 区
- **生成质量不对** → 看对应 step 的 `docs/方法论.md` 自检
- **彻底懵了** → 仓库 Issue 区

---

## 升级日志

- **2026-05-25 v0.9.1**：完成 step4 字幕训练 + step3.5 设计稿 + 老奶奶 README/TUTORIAL + 全量 sanitization 准备 public 发布
- **2026-05-22 v0.9**：完成 round1-step3 全流水线（MAC 模块 + 跨产品通用化）

---

## 致谢

- 极客号 KOL 视频拆解（76 条样本）
- 思源黑体 (Adobe Source Han Sans) 字体
- faster-whisper (Systran/CTranslate2)
- OpenAI / Anthropic / Google / 字节火山 / 快手 各 API 厂商
