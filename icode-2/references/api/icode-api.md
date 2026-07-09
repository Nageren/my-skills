# iCode API 命令集

通过 `icode-cli api` 命令组访问 iCode 平台的各种 API。

## 命令概览

### 代码库相关

| 命令 | 功能 | 详细文档 |
|------|------|----------|
| `get_person_repo` | 查询个人代码库列表 | [get_person_repo.md](get_person_repo.md) |
| `get_repo_branch` | 查询代码库分支列表 | [get_repo_branch.md](get_repo_branch.md) |
| `get_person_commit` | 查询个人提交记录 | [get_person_commit.md](get_person_commit.md) |
| `get_repo_config` | 获取代码库配置 | [get_repo_config.md](get_repo_config.md) |
| `get_repo_members` | 获取代码库成员列表 | [get_repo_members.md](get_repo_members.md) |
| `get_submit_settings` | 获取提交规则配置 | [get_submit_settings.md](get_submit_settings.md) |
| `check_repo_permission` | 检查代码库权限 | [check_repo_permission.md](check_repo_permission.md) |
| `create_branch` | 创建新分支 | [create_branch.md](create_branch.md) |

### 评审查询

| 命令 | 功能 | 详细文档 |
|------|------|----------|
| `get_repo_reviews` | 查询代码库评审列表 | [get_repo_reviews.md](get_repo_reviews.md) |
| `get_my_reviews` | 获取我的评审列表 | [get_my_reviews.md](get_my_reviews.md) |
| `get_review_info` | 获取评审详细信息 | [get_review_info.md](get_review_info.md) |
| `get_review_comments` | 获取评审评论 | [get_review_comments.md](get_review_comments.md) |
| `get_machine_check` | 获取机器检查结果 | [get_machine_check.md](get_machine_check.md) |
| `get_diff_file` | 获取 commit 之间的变更文件 | [get_diff_file.md](get_diff_file.md) |
| `get_diff_content` | 获取文件的 diff 内容 | [get_diff_content.md](get_diff_content.md) |
| `build_fetch_command` | 生成 git fetch 命令 | [build_fetch_command.md](build_fetch_command.md) |

### 评审操作

| 命令 | 功能 | 详细文档 |
|------|------|----------|
| `set_review_score` | 设置评审分数 | [set_review_score.md](set_review_score.md) |
| `add_reviewers` | 添加评审人 | [add_reviewers.md](add_reviewers.md) |
| `submit_review` | 提交/合并评审 | [submit_review.md](submit_review.md) |
| `create_draft_comment` | 创建草稿评论 | [create_draft_comment.md](create_draft_comment.md) |
| `publish_comments` | 发布草稿评论 | [publish_comments.md](publish_comments.md) |

### AI 智能评审

| 命令 | 功能 | 详细文档 |
|------|------|----------|
| `start_ai_review` | 触发 AI 智能评审 | [start_ai_review.md](start_ai_review.md) |
| `get_ai_review` | 获取 AI 评审结果 | [get_ai_review.md](get_ai_review.md) |

## 通用参数

所有命令支持以下通用参数：

| 参数 | 说明 |
|------|------|
| `--output`, `-o` | 输出格式：json（默认）、yaml、table |
| `--verbose`, `-v` | 显示详细日志 |

## 快速示例

```bash
# 查看我的代码库
icode-cli api get_person_repo --output table

# 查看评审详情
icode-cli api get_review_info -n 12345

# 批准评审
icode-cli api set_review_score --repo baidu/icode/test -n 12345 --score 2

# 触发 AI 评审
icode-cli api start_ai_review -n 12345

# 查询 AI 评审结果
icode-cli api get_ai_review -i <conversation-id>
```

## 错误处理

常见错误码：

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `ErrAuthMissing` | 未认证 | 执行 `icode-cli login` 查看登录指引 |
| `ErrMissingParam` | 缺少必填参数 | 检查命令参数 |
| `ErrAPIRequest` | API 请求失败 | 检查网络连接 |
