# create_draft_comment

为指定评审创建草稿评论。草稿评论创建后不立即可见，需调用 `publish_comments` 发布后才对其他用户可见。

## 命令格式

```bash
icode-cli api create_draft_comment --repo <repo-name> --change-number <n> --patch-set-id <n> --path <file-path> --message <message> [--line <n>] [--side <side>] [--unresolved] [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名 |
| `--change-number` | `-n` | 是 | - | 评审编号 |
| `--patch-set-id` | `-p` | 是 | - | PatchSet 编号 |
| `--path` | - | 是 | - | 文件路径 |
| `--message` | `-m` | 是 | - | 评论内容 |
| `--line` | `-l` | 否 | - | 行号（可选） |
| `--side` | - | 否 | - | diff 侧：PARENT/REVISION |
| `--unresolved` | - | 否 | true | 是否标记为待解决 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## Side 说明

| 值 | 说明 |
|------|------|
| `PARENT` | 基准版本（修改前） |
| `REVISION` | 新版本（修改后） |

## 使用示例

```bash
# 创建简单草稿评论
icode-cli api create_draft_comment \
  --repo baidu/icode/test \
  --change-number 12345 \
  --patch-set-id 1 \
  --path src/main.go \
  --message "请修改此处逻辑"

# 创建带行号的草稿评论
icode-cli api create_draft_comment \
  --repo baidu/icode/test \
  --change-number 12345 \
  --patch-set-id 1 \
  --path src/main.go \
  --message "建议优化这里的性能" \
  --line 42 \
  --side REVISION

# 创建已解决状态的评论
icode-cli api create_draft_comment \
  --repo baidu/icode/test \
  --change-number 12345 \
  --patch-set-id 1 \
  --path src/main.go \
  --message "LGTM" \
  --unresolved=false
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": {
    "id": "comment-123",
    "path": "src/main.go",
    "line": 42,
    "message": "建议优化这里的性能",
    "unresolved": true,
    "updated": "2024-01-15 10:30:00"
  }
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 评论 ID |
| `path` | string | 文件路径 |
| `line` | int | 行号 |
| `message` | string | 评论内容 |
| `unresolved` | bool | 是否待解决 |
| `updated` | string | 更新时间 |

## 使用场景

1. **代码评审**：对代码的具体位置添加评论
2. **批量评论**：先创建多个草稿评论，然后一次性发布
3. **AI 评审集成**：自动化工具添加评审意见

## 注意事项

- 草稿评论只有创建者可见
- 需要调用 `publish_comments` 后其他人才能看到
- 可以在发布前修改或删除草稿

## 相关命令

- `icode-cli api publish_comments`: 发布草稿评论
- `icode-cli api get_review_comments`: 获取评审评论
- `icode-cli api get_review_info`: 获取评审详情
