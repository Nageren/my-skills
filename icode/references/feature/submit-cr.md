# submit-cr - 提交 CR

自动判断当前提交是新建 CR 还是追加到已有 CR，并执行相应的提交流程。

## 执行流程

```
开始
  │
  ▼
查询本地信息：
  - commit hash (git rev-parse HEAD)
  - commit message (git log -1 --format="%s")
  - iCafe 卡片号 (从 message 解析，如 ComateStack-5353)
  │
  ▼
获取仓库名称和当前用户
  │
  ▼
查询远程 NEW 状态的 CR 列表 (api get_repo_reviews)
  │
  ▼
过滤当前用户的 CR，执行匹配判断：
  │
  ├─【匹配方式一】current_revision == 本地 commit hash
  │    │
  │    ▼
  │  找到匹配 → 【同一个 CR - Amend 模式】
  │
  ├─【匹配方式二】远程 CR 的 subject 以相同 iCafe 卡片号开头
  │    │
  │    ▼
  │  找到匹配 → 【同一个 CR - Amend 模式】
  │
  └─ 两种方式均未匹配 → 【新 CR 模式】

【同一个 CR - Amend 模式】
  1. git add -A (添加所有修改)
  2. git commit --amend --no-edit
  3. icode-cli git push_cr

【新 CR 模式】
  1. 使用 icafe-assistant skill 获取 iCafe 卡片 ID
  2. git add -A (添加所有修改)
  3. git commit -m "<iCafe卡片号> <commit message>"
  4. icode-cli git push_cr
```

## 快速使用

```bash
# 默认 master 分支
./submit-cr.sh

# 指定 develop 分支
./submit-cr.sh develop
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 目标分支（`$1`） | master | CR 的目标分支 |

## 判断逻辑详解

### 如何判断是否为同一个 CR

有两种匹配方式，满足任一条件即视为同一个 CR：

**方式一：Commit Hash 匹配**

1. 获取本地当前 commit: `git rev-parse HEAD`
2. 调用 `icode-cli api get_repo_reviews --repo <repo> --status NEW`
3. 在返回的 CR 列表中查找：
   - `owner.username` == 当前用户
   - `current_revision` == 本地 commit hash
4. 如果找到匹配项，说明当前 commit 已经有对应的远程 CR

**方式二：iCafe 卡片号匹配**

1. 解析本地 commit message 中的 iCafe 卡片号（如 `ComateStack-5353`）
2. 调用 `icode-cli api get_repo_reviews --repo <repo> --status NEW`
3. 在返回的 CR 列表中查找：
   - `owner.username` == 当前用户
   - `subject` 中包含相同的 iCafe 卡片号
4. 如果找到匹配项，说明本地修改属于已有的 CR

### iCafe 卡片号解析规则

iCafe 卡片号格式为 `<项目前缀>-<数字>`，位于 commit message 开头：

```
ComateStack-5353 support agentic
│              │
└──────────────┴── iCafe 卡片号

ISSUE-123 fix login bug
│       │
└───────┴── iCafe 卡片号
```

## 注意事项

1. **Amend 模式会修改 commit history**：确保该 commit 尚未被其他人基于开发
2. **Change-Id 保持不变**：amend 后 Change-Id 不变，Gerrit 会识别为同一个 CR 的新版本
3. **分支选择**：Amend 模式使用原 CR 的目标分支；新 CR 默认使用 master
4. **iCafe 绑定**：新 CR 需要绑定 iCafe 卡片，通过 `icafe-cli-assistant` skill 获取卡片 ID

## 相关 Skill

| Skill | 说明 |
|-------|------|
| `icafe-cli-assistant` | 获取 iCafe 卡片 ID，用于绑定 CR |

## 相关命令

| 命令 | 说明 |
|------|------|
| `icode-cli git push_cr` | 推送代码评审 |
| `icode-cli api get_repo_reviews` | 获取仓库 CR 列表 |
| `icode-cli api get_review_info` | 获取 CR 详情 |
| `icode-cli login` | 检查登录状态 |
