# 项目：SLG 极客号 AI 视频复刻流水线

## 这个仓库做什么

把"极客号"（一类中国 SLG 买量短视频 KOL 风格 — 硬核知识科普 + 情绪燃料 + 强卖点植入）的 60 秒爆款视频做成 AI 全自动生产流水线。

输入：产品配置 + 60 秒文案脚本 + 30 秒目标音色样本
输出：带字幕、带配音、带 BGM 的 60 秒成片

## Pipeline 5 步（详见 `pipeline/SKILL.md`）

```
Round 1 脚本生成   → script.yaml
Round 2 Step 1 配音 → final_60s_mixed.mp3
Round 2 Step 2 分镜 → storyboard.json + images/
Round 2 Step 3 视频 → BGM完整版.mp4
Round 2 Step 4 字幕 → 字幕版.mp4
```

## Agent 工作纪律

1. **Master SKILL 是唯一入口** — 接到"做复刻视频"需求时先读 `pipeline/SKILL.md`，禁直接进单 step
2. **里程碑制** — 每步跑完 checkpoint 到桌面 + 等用户审，禁一口气跑 5 步
3. **跨产品入口只看 product_config.yaml** — 任何 step 脚本禁 hardcode 产品信息（如 "ROK Han Dynasty"）；必须从 product_config.yaml 读 game_name / part1_anchor 等字段
4. **API key 必须用环境变量** — 仓库内所有 scripts 通过 `os.environ[...]` 读 key；.env 文件本地放，不入库

## 输出规范

- 中文输出，专有名词/产品名/技术词保留英文
- 结论先行，能用表格不用段落，能用数字不用形容词
- 标注置信度（不确定标 [高/中/低]）
- 不知道就说不知道，不编造

## 安全红线

- API keys / 内部 URL / 个人邮箱 不入库（用 env vars / .env.example）
- `trash` > `rm`（可恢复优于永久删除）
- commit / push / deploy / force-push / reset --hard / rm -rf — 必须明确得到用户指令

## 视频素材分析（如需）

- 3D 动画/CG 素材：必须每秒 1 帧抽帧（60s 视频 = 60 帧）
- 实拍素材：最低 10 帧 / 视频，3D/CG 不得低于 1 帧/秒
- 抽帧密度不够会导致 vision 模型"推断性幻觉"补全错误叙事

## 工作风格

- token 效率优先，搜索精简
- 一步一执行，每次拿到结果立即回复
- 禁止预告（"让我来分析..."）→ 直接做
- 表格替代段落，数字替代形容词
- 单次回复 ≤500 字，超过拆轮次

## 验证 Pipeline 通过的最小测试

```
1. 复制 examples/古代将军/product_config.yaml → 新产品 product_config.yaml
2. 改 6 必填字段
3. 准备新产品 60s script.yaml
4. 顺序跑 step1 → step4
5. 通过条件：5 步全部不修代码就跑通
```
