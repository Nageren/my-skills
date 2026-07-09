---
name: jenkins-quick-deploy
description: 通过 Jenkins MCP 或 API 快速部署 GTSP/支付类服务到 develop 环境。使用 gtsp-k8s-slave 流水线触发构建、编译、重启。适用于用户说「部署」「jenkins 部署」「快速部署」或指定 pay-service-cashier 等应用名时。
---

# Jenkins 快速部署

## 前置条件

- Cursor 已配置 `jenkins-mcp`（见 `~/.cursor/mcp.json`）
- 环境变量由 MCP 注入：`JENKINS_URL`、`JENKINS_USERNAME`、`JENKINS_PASSWORD`

## 快速流程

```
1. 解析目标应用名 → 2. 确认 Git 分支 → 3. 触发构建 → 4. 轮询状态 → 5. 汇报结果
```

### Step 1：确定应用名

| 用户表述 | app 参数 |
|---------|----------|
| 当前仓库 `pay-service-cashier` | `pay-service-cashier` |
| 未指定应用 | 从 `spring.application.name` 或仓库目录名推断 |
| 指定其他服务 | 直接使用服务名 |

完整应用列表见 [reference.md](reference.md)。

### Step 2：确认分支（重要）

`pay-service-cashier` 流水线会执行 `git checkout settlement && git pull origin settlement`。

部署前检查：

```bash
git branch --show-current
git status -sb
```

当前分支与流水线不一致时，先告知用户；用户确认后再继续。

### Step 3：触发构建（优先 MCP）

**方式 A — Jenkins MCP（推荐）**

```
trigger_build:
  job_name: gtsp-k8s-slave
  parameters:
    app: <应用名>
    work_dir: /data/deploy/gtsp-develop
    BUILD: true
    RESTART: true
```

MCP 工具名：`mcp_jenkins-mcp_trigger_build`、`mcp_jenkins-mcp_get_build_status`、`mcp_jenkins-mcp_list_jobs`。

**方式 B — 部署脚本（MCP 不可用时）**

```bash
bash ~/.cursor/skills/jenkins-quick-deploy/scripts/deploy.sh pay-service-cashier
```

可选参数：

```bash
bash scripts/deploy.sh <app> [--no-build] [--no-restart] [--work-dir /data/deploy/gtsp-develop]
```

脚本从环境变量读取 Jenkins 凭证；未设置时尝试解析 `~/.cursor/mcp.json` 中 `jenkins-mcp.env`。

### Step 4：轮询构建状态

- MCP：`get_build_status(job_name=gtsp-k8s-slave, build_number=<构建号>)`
- 脚本：内置轮询，默认 15s 间隔、最长 15 分钟
- 构建页：`${JENKINS_URL}/job/gtsp-k8s-slave/<构建号>/`

### Step 5：汇报结果

使用以下模板：

```markdown
## 部署结果

| 项目 | 内容 |
|------|------|
| Jenkins 任务 | gtsp-k8s-slave |
| 应用 | {app} |
| 构建号 | #{number} |
| 结果 | {SUCCESS/FAILURE/...} |
| 耗时 | {duration} |

**构建链接：** {url}
```

失败时拉取控制台日志末尾 50 行，给出简要原因。

## 默认参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `job_name` | `gtsp-k8s-slave` | GTSP develop 环境统一部署任务 |
| `work_dir` | `/data/deploy/gtsp-develop` | 服务器源码目录 |
| `BUILD` | `true` | Maven 编译打包 |
| `RESTART` | `true` | 重启 K8s 服务 |

## 常见问题

**403 No valid crumb**：API 直连需 Cookie + Crumb，使用 `scripts/deploy.sh` 或 MCP。

**找不到应用**：用 `list_jobs` 或查阅 [reference.md](reference.md) 确认 `app` 名称。

**构建 SUCCESS 但服务异常**：检查 Nacos 注册与服务日志，不在本 skill 范围内。

## 安全

- 禁止在 skill、脚本或对话中硬编码 Jenkins 密码
- 凭证仅来自 MCP 环境变量或本地 `mcp.json`（不提交到 Git）
