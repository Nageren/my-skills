# MISSION — awesome-rules 仓库使命（治理文件）

> 状态：S0 v0.2（2026-09-29 工厂迁出修订；v0.1 2026-08-21）。
> 本文件属于治理层：修订只走人工 PR（分支保护 + CODEOWNERS 强制人审）。
> 工厂运行时与治理已迁至 [im47cn/awesome-factory](https://github.com/im47cn/awesome-factory)
>（其 MISSION.md 承接 v0.1 宪法语义，设计沿革见该仓 docs/design/）。

## 为什么存在

awesome-rules 是研发规范与 AI 审查技能的唯一真相源（见 [README.md](README.md)）。
规范与技能的规模增长快于人工维护预算——技术通缩下，正确反应是把可判定的维护工作
交给机器，把人类的稀缺输入（意图、判断、信任锚）留给宪法与周界。

## 维护模型

本仓库是被巡检/分发的下游真相源：自动化维护循环（issue → triage → 实现 →
确定性门 → 独立验证 → PR → 合并）的工厂运行时与治理随
[im47cn/awesome-factory](https://github.com/im47cn/awesome-factory) 独立演进，
本仓不再是工厂宿主。本仓的变更一律走人工 PR（分支保护 + CODEOWNERS 强制
人审）；工厂侧以 downstream-check 分发面消费本仓的规范与技能。

## 周界（PERIMETER）

以下路径变更只能走人类 PR（分支保护 + CODEOWNERS 强制人审）：

- 治理：`MISSION.md`、`steering/`、`CONTRIBUTING.md`、`docs/design/`
- 质检线：`scripts/`、`hooks/`、`.github/`
- 发布面：`.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/`、`.kimi-plugin/`、
  `.grok-plugin/`、`.opencode/`、`.pi/`、`.crush/`、`.agents/`、`.vscode/`、
  `package.json`、`.versionrc.js`、`lefthook.yml`、`.gitignore`

> 周界清单是利益权衡（宁宽勿窄：过宽的代价是多走人审，过窄的代价是被绕过），
> 由人类定期复核收窄。

## 铁律

宪法六条（holdout 独立验证、二值 triage、治理不可自改、dispatcher 零 LLM、
门灵敏度先行、不可信输入隔离）随工厂迁至 awesome-factory MISSION.md 继续生效。
本仓保留其精神内核：**治理与门禁面变更（周界路径）不走任何自动化通道，
一律人工 PR。**
