#!/usr/bin/env bash
# setup.sh — 把 SKILL.md 注册到 Claude Code，让 Agent 启动时自动加载
#
# 跑完后，Claude Code 启动时会自动扫描 .claude/skills/ 目录加载所有 SKILL。
# Agent 就能识别"极客号复刻"/"AI 视频流水线"等触发词，自动按 5 步跑。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$ROOT/.claude/skills"

echo "========================================"
echo "SLG 极客号 AI 视频流水线 — Setup"
echo "========================================"
echo ""
echo "工作目录: $ROOT"
echo "SKILL 装载目录: $SKILLS_DIR"
echo ""

mkdir -p "$SKILLS_DIR"

# SKILL 注册表: <name>:<相对路径>
# name 必须匹配 SKILL.md 头部 frontmatter 的 name 字段
SKILLS=(
  "geek-replication-master:pipeline/SKILL.md"
  "geek-script-generation:pipeline/01-脚本/SKILL.md"
  "geek-voice-pipeline:pipeline/02-配音/SKILL.md"
  "geek-storyboard-pipeline:pipeline/03-分镜/SKILL.md"
  "geek-video-pipeline:pipeline/04-视频/SKILL.md"
  "geek-subtitle-pipeline:pipeline/05-字幕/SKILL.md"
  "geek-aspect-adaptation:pipeline/04.5-画幅/SKILL.md"
)

INSTALLED=0
SKIPPED=0
for entry in "${SKILLS[@]}"; do
  name="${entry%%:*}"
  rel_path="${entry#*:}"
  src="$ROOT/$rel_path"
  dst_dir="$SKILLS_DIR/$name"

  if [ ! -f "$src" ]; then
    echo "  ⚠️  跳过 $name（源文件不存在: $rel_path）"
    SKIPPED=$((SKIPPED+1))
    continue
  fi

  mkdir -p "$dst_dir"
  cp "$src" "$dst_dir/SKILL.md"
  echo "  ✓ 装好 SKILL: $name"
  INSTALLED=$((INSTALLED+1))
done

echo ""
echo "----------------------------------------"
echo "SKILL 装载完成: 成功 $INSTALLED · 跳过 $SKIPPED"
echo "----------------------------------------"

# === 依赖检查 ===
echo ""
echo "[依赖检查]"

# 检查 Python
if command -v python3 >/dev/null 2>&1; then
  PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
  echo "  ✓ Python: $PY_VER"
else
  echo "  ✗ Python 未装。装法: https://python.org"
fi

# 检查 ffmpeg
if command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
  echo "  ✓ ffmpeg: $FFMPEG_VER"
else
  echo "  ✗ ffmpeg 未装。装法:"
  echo "      Mac:     brew install ffmpeg"
  echo "      Ubuntu:  sudo apt install ffmpeg"
  echo "      Windows: choco install ffmpeg"
fi

# 检查 Claude Code
if command -v claude >/dev/null 2>&1; then
  echo "  ✓ Claude Code 已装"
else
  echo "  ⚠️  Claude Code 未装。装法: npm install -g @anthropic-ai/claude-code"
fi

# 检查思源黑体
if command -v fc-list >/dev/null 2>&1; then
  if fc-list | grep -q "Source Han Sans SC"; then
    echo "  ✓ 思源黑体 SC 已装"
  else
    echo "  ⚠️  思源黑体未装（字幕渲染需要）。装法见 TUTORIAL.md 第 3 步"
  fi
else
  echo "  ⚠️  fc-list 不可用（无法检测字体）。Mac/Linux 自带，Windows 可能需额外配置"
fi

# === Python 依赖检查 ===
echo ""
echo "[Python 库检查]"
for lib in openai faster_whisper yaml jieba; do
  if python3 -c "import $lib" 2>/dev/null; then
    echo "  ✓ $lib"
  else
    echo "  ✗ $lib 未装"
  fi
done

# === .env 检查 ===
echo ""
echo "[环境变量检查]"
if [ ! -f "$ROOT/.env" ]; then
  echo "  ⚠️  .env 不存在"
  echo "      运行: cp .env.example .env"
  echo "      然后填进 4 个 API key"
else
  echo "  ✓ .env 已存在"
  # 检查关键 key 是否填好（非空）
  for key in LLM_PROXY_API_KEY VOLC_ICL_API_KEY; do
    val=$(grep "^$key=" "$ROOT/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
    if [ -z "$val" ] || [[ "$val" == *"xxxxx"* ]] || [[ "$val" == *"your_"* ]]; then
      echo "      ⚠️  $key 看起来还是模板值，请填实际 key"
    else
      echo "      ✓ $key 已填"
    fi
  done
fi

# === 完成 ===
echo ""
echo "========================================"
echo "✅ Setup 完成"
echo "========================================"
echo ""
echo "下一步："
echo ""
echo "  1) 如果上面有 ✗ 或 ⚠️，按提示装好对应依赖"
echo "  2) 启动 Claude Code（必须在仓库根目录运行）："
echo "     claude"
echo ""
echo "  3) 输入触发 prompt："
echo '     "帮我用 pipeline/03-分镜/examples/古代将军_v3/'
echo '      的配置，跑一遍极客号 AI 视频复刻流水线。环境变量已配在 .env。"'
echo ""
echo "  Agent 会自动按 5 步跑。每步跑完会暂停让你审。"
echo ""
echo "详细教程: TUTORIAL.md"
echo "原理介绍: README.md"
