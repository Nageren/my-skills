---
name: icode
metadata:
  author: icode
  version: "1.0.0"
description: |
  iCode 研发工具集，提供代码评审全流程自动化能力。支持登录认证、代码库克隆、CR 提交与追加、添加评审人、机器检查修复、AI 代码评审、打分与合入，覆盖从代码提交到合入的完整研发流程。
allowed-tools:
  - "Bash(git *)"
  - "Bash(icode-cli *)"
  - "Bash(~/.icode/bin/icode-cli *)"
  - "Bash(icafe-cli *)"
  - "Bash(~/.icafe-cli/bin/icafe-cli *)"
  - "Bash(~/.claude/skills/icode/scripts/*)"
  - "Bash(~/.claude/skills/icode/scripts/* *)"
---

## 前置检查（必须执行）

在执行任何 iCode 操作之前，先运行前置检查脚本验证环境：

```bash
./scripts/test-preflight.sh
```

> 注：`./scripts/` 路径相对于 skill 目录，执行时需使用完整路径（如 `~/.claude/skills/icode/scripts/test-preflight.sh`）。

如果检查失败：
- **icode-cli 未安装或版本过低**：执行 `curl -sSL http://icode-cli.bj.bcebos.com/install.sh | bash -s -- --no-skills` 强制安装最新版（要求 >= 0.1.9）
- **未登录**：执行 `icode-cli login` 进行登录
- **不是 git 仓库**：确保当前目录是有效的 git 仓库，或使用 `icode-cli git clone` 克隆代码库

本 skill 依赖 `icafe-official` skill，如未安装请先执行：
```bash
ducc skill install icafe-official   # ducc/dodo 环境
zulu skill install icafe-official   # comate-iCode 环境
```

## 功能概览

### 1. 登录认证

管理 iCode 认证状态。详见 [login.md](references/login.md)

**常用命令：**

- `login`: 检查登录状态或进行登录（交互式/非交互式）
  ```bash
  # 参考命令
  icode-cli login
  icode-cli login --token "eyJ..."
  icode-cli login --method comate --token "Bearer-xxx"
  ```
  详见 [login.md](references/login.md)

- `logout`: 登出并清除认证信息
  ```bash
  # 参考命令
  icode-cli logout
  ```
  详见 [login.md](references/login.md)

## 场景

以下场景脚本位于 skill 的 `./scripts/` 目录，**但必须在 git 仓库目录下执行**（即用户的工作目录）。

执行方式：在 git 仓库目录下，使用 skill 脚本的完整路径调用。

### 1. 提交 CR

智能判断新建 CR 或追加到已有 CR（Amend 模式）。
```bash
# 参考命令
./scripts/submit-cr.sh [target-branch] [commit-message]
```
详见 [submit-cr.md](references/feature/submit-cr.md)

**功能说明：**
- 自动检测是否有工作区修改
- 通过 commit hash 或 iCafe 卡片号匹配已有 CR
- 匹配到则执行 amend 模式，否则新建 CR
- 支持指定目标分支（默认 master）

**Agent 执行流程：**

1. **先调用脚本检测 CR 状态**：`./scripts/submit-cr.sh [branch]`
2. **根据返回结果处理**：
   - **退出码 0**：匹配到已有 CR，脚本已自动完成 amend 提交，流程结束
   - **退出码 2**：需要新建 CR，进入选卡流程（见下方）

**选卡流程（仅当需要新建 CR 时）：**

**情况一：用户明确要求智能选卡**
- 若用户在请求中明确表达使用智能选卡（如"自动选卡"、"智能绑卡"、"帮我自动选一个卡片"等），则直接调用 `icafe-official` skill 使用智能选卡，无需询问

**情况二：用户未明确指定选卡方式**
1. **询问用户**选择卡片获取方式：
   ```
   请选择卡片获取方式：
   1. 智能选卡（推荐）- 自动匹配最相关的卡片
   2. 交互式选卡 - 手动选择卡片
   ```
2. 根据用户选择调用 `icafe-official` skill，获取卡片 ID

**最后：调用脚本提交**
- `./scripts/submit-cr.sh [branch] "<卡片ID> <描述>"`

这样可以确保 CR 与 iCafe 卡片正确关联，后续修改也能自动 amend 到同一 CR

### 2. 添加评审人

从历史 CR 中自动选择评审人，或使用指定的评审人。
```bash
# 参考命令
./scripts/add-reviewer.sh [cr-number] [reviewer]
```
详见 [add-reviewer.md](references/feature/add-reviewer.md)

**功能说明：**
- 不指定 CR 时自动检测当前 commit 对应的 CR
- 不指定评审人时从历史已合入的 CR 中随机选择
- 支持手动指定评审人用户名

### 3. 修复机器检查

检测 CR 的机器检查结果，输出失败项详情供 Agent 分析修复。
```bash
# 参考命令
./scripts/fix-machine-check.sh [cr-number] [max-retries]
```
详见 [fix-machine-check.md](references/feature/fix-machine-check.md)

**功能说明：**
- 获取机器检查结果（代码规范、缺陷检查等）
- 输出失败项的详细信息（检查项、状态、行内评论）
- 失败时退出码为 2，等待 Agent 修复后重新运行

### 4. AI 代码评审

**触发条件**: 当用户要求"AI 代码评审"、"AI 评审"、"ACR"时，**优先使用此脚本**
触发 AI 代码评审并分析结果，发现问题时退出等待 Agent 修复。
```bash
# 参考命令
./scripts/submit-acr.sh [cr-number] [max-loops] [timeout] [severity]
```
详见 [submit-acr.md](references/feature/submit-acr.md)

**功能说明：**
- 触发 AI 代码评审（start_ai_review）
- 轮询等待评审完成（每 10 秒检查一次）
- 过滤 severityScore >= 阈值的问题
- 有问题时输出详情并退出（退出码 2）

**严重度说明：**
| severityScore | 说明 |
|---------------|------|
| 1-4 | 低优先级（忽略） |
| 5-6 | 中优先级（需修复） |
| 7-10 | 高优先级（必须修复） |

### 5. 合入 CR

尝试打分 +2 并合入 CR，通过打分结果判断是否有合入权限。
```bash
# 参考命令
./scripts/merge-cr.sh [cr-number]
```
详见 [merge-cr.md](references/feature/merge-cr.md)

**功能说明：**
- 通过尝试打分 +2 检测是否有合入权限
- 打分成功：尝试合入 CR
- 打分失败：提示无权限，需联系管理员或找有权限的评审人
- 合入失败时输出失败原因

### 6. SSH 密钥配置

自动检测并配置 SSH 密钥，用于 iCode Git 操作认证。
```bash
# 参考命令
./scripts/ssh-setup.sh
```
详见 [ssh-setup.md](references/feature/ssh-setup.md)

**功能说明：**
- 检测本地是否存在 SSH 密钥（`~/.ssh/id_ed25519` 或 `~/.ssh/id_rsa`）
- 若不存在则自动生成新的 ed25519 密钥对
- 自动复制公钥到剪贴板（支持 macOS/Linux）
- 引导用户访问 https://console.cloud.baidu-int.com/devops/icode/account/keys 完成密钥绑定

## Git 操作

提供与 iCode 平台集成的 Git 操作命令。详见 [icode-git.md](references/git/icode-git.md)

```bash
icode-cli git <command> [options]
```

**常用命令：**

- `clone`: 克隆 iCode 代码库，自动配置认证
  ```bash
  # 参考命令
  icode-cli git clone --repo baidu/icode/test --path ./local-path
  ```
  详见 [clone.md](references/git/clone.md)

- `push`: 推送代码到指定分支
  ```bash
  # 参考命令
  icode-cli git push --branch feature-x
  ```
  详见 [push.md](references/git/push.md)

- `push_cr`: 提交代码到 Gerrit 进行代码评审
  ```bash
  # 参考命令
  icode-cli git push_cr --branch master
  ```
  详见 [push_cr.md](references/git/push_cr.md)

## API 操作

提供对 iCode 平台各种 API 的命令行访问。详见 [icode-api.md](references/icode-api.md)

```bash
icode-cli api <command> [options] [-o json]
```

**常用命令：**

- `get_repo_reviews`: 获取仓库CR列表
  ```bash
  # 参考命令
  icode-cli api get_repo_reviews --repo baidu/icode/test
  ```
  详见 [get_repo_reviews.md](references/api/get_repo_reviews.md)

- `get_my_reviews`: 获取我的评审列表
  ```bash
  # 参考命令
  icode-cli api get_my_reviews
  ```
  详见 [get_my_reviews.md](references/api/get_my_reviews.md)

- `get_repo_members`: 获取仓库成员列表
  ```bash
  # 参考命令
  icode-cli api get_repo_members --repo baidu/icode/test
  ```
  详见 [get_repo_members.md](references/api/get_repo_members.md)

- `get_review_info`: 获取CR详细信息
  ```bash
  # 参考命令
  icode-cli api get_review_info -n 12345
  ```
  详见 [get_review_info.md](references/api/get_review_info.md)

- `get_diff_file`: 获取commit变更文件
  ```bash
  # 参考命令
  icode-cli api get_diff_file --repo baidu/icode/test --commit abc123
  ```
  详见 [get_diff_file.md](references/api/get_diff_file.md)

- `get_diff_content`: 获取文件diff内容
  ```bash
  # 参考命令
  icode-cli api get_diff_content --repo baidu/icode/test --commit abc123 --file src/main.go
  ```
  详见 [get_diff_content.md](references/api/get_diff_content.md)

- `add_reviewers`: 添加评审人
  ```bash
  # 参考命令
  icode-cli api add_reviewers -n 12345 --reviewers zhangsan
  ```
  详见 [add_reviewers.md](references/api/add_reviewers.md)

- `set_review_score`: 设置评审分数
  ```bash
  # 参考命令
  icode-cli api set_review_score --repo baidu/icode/test -n 12345 --score 2
  ```
  详见 [set_review_score.md](references/api/set_review_score.md)

- `submit_review`: 合入CR
  ```bash
  # 参考命令
  icode-cli api submit_review --repo baidu/icode/test -n 12345
  ```
  详见 [submit_review.md](references/api/submit_review.md)

- `create_draft_comment`: 创建草稿评论
  ```bash
  # 参考命令
  icode-cli api create_draft_comment --repo baidu/icode/test --change-number 12345 --patch-set-id 1 --path src/main.go --message "评论内容"
  ```
  详见 [create_draft_comment.md](references/api/create_draft_comment.md)

- `publish_comments`: 发布草稿评论
  ```bash
  # 参考命令
  icode-cli api publish_comments --repo baidu/icode/test --change-number 12345 --patch-set-id 1
  ```
  详见 [publish_comments.md](references/api/publish_comments.md)

- `start_ai_review`: 触发AI代码评审
  ```bash
  # 参考命令
  icode-cli api start_ai_review -n 12345
  ```
  详见 [start_ai_review.md](references/api/start_ai_review.md)

- `get_ai_review`: 获取AI评审结果
  ```bash
  # 参考命令
  icode-cli api get_ai_review -i <task_id>
  ```
  详见 [get_ai_review.md](references/api/get_ai_review.md)

- `get_machine_check`: 获取机器检查结果
  ```bash
  # 参考命令
  icode-cli api get_machine_check -n 12345
  ```
  详见 [get_machine_check.md](references/api/get_machine_check.md)

- `check_repo_permission`: 检查代码库权限
  ```bash
  # 参考命令
  icode-cli api check_repo_permission --repo baidu/icode/test
  ```
  详见 [check_repo_permission.md](references/api/check_repo_permission.md)

- `get_repo_config`: 获取代码库配置
  ```bash
  # 参考命令
  icode-cli api get_repo_config --repo-names baidu/icode/test
  ```
  详见 [get_repo_config.md](references/api/get_repo_config.md)

- `get_submit_settings`: 获取提交规则配置
  ```bash
  # 参考命令
  icode-cli api get_submit_settings --repo baidu/icode/test
  ```
  详见 [get_submit_settings.md](references/api/get_submit_settings.md)

- `create_branch`: 创建新分支
  ```bash
  # 参考命令
  icode-cli api create_branch --repo baidu/icode/test --branch feature-x --from master
  ```
  详见 [create_branch.md](references/api/create_branch.md)

- `build_fetch_command`: 生成git fetch命令
  ```bash
  # 参考命令
  icode-cli api build_fetch_command --change-number 12345
  ```
  详见 [build_fetch_command.md](references/api/build_fetch_command.md)

## 典型工作流

```bash
# 1. 检查登录状态
icode-cli login

# 2. 开发完成后提交 CR
./scripts/submit-cr.sh

# 3. 修复机器检查问题（如有）
./scripts/fix-machine-check.sh

# 4. 运行 AI 代码评审
./scripts/submit-acr.sh

# 5. 添加评审人（如需要）
./scripts/add-reviewer.sh

# 6. 合入 CR
./scripts/merge-cr.sh
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 失败（无 CR / 超时 / 配置错误） |
| 2 | 需要 Agent 修复或人工介入 |
