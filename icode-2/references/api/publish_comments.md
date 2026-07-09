# publish_comments

发布指定评审的所有草稿评论。发布后草稿评论将对其他用户可见。

## 命令格式

```bash
icode-cli api publish_comments --repo <repo-name> --change-number <n> --patch-set-id <n> [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名 |
| `--change-number` | `-n` | 是 | - | 评审编号 |
| `--patch-set-id` | `-p` | 是 | - | PatchSet 编号 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## 使用示例

```bash
# 发布评审的草稿评论
icode-cli api publish_comments \
  --repo baidu/icode/test \
  --change-number 12345 \
  --patch-set-id 1
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "Comments published successfully",
  "data": null
}
```

## 典型工作流

```bash
# 1. 创建多个草稿评论
icode-cli api create_draft_comment --repo baidu/icode/test -n 12345 -p 1 \
  --path src/main.go -m "请检查空指针" --line 10

icode-cli api create_draft_comment --repo baidu/icode/test -n 12345 -p 1 \
  --path src/utils.go -m "建议使用更高效的算法" --line 25

# 2. 一次性发布所有草稿评论
icode-cli api publish_comments --repo baidu/icode/test -n 12345 -p 1
```

## 使用场景

1. **批量发布评论**：先创建多个草稿评论，然后一次性发布
2. **评审完成通知**：发布评论后通知代码作者
3. **自动化评审**：自动化工具完成评审后发布结果

## 注意事项

- 发布后所有草稿评论变为正式评论，其他用户可见
- 如果没有草稿评论，调用此命令也会成功
- 发布后无法撤回，但可以编辑已发布的评论

## 相关命令

- `icode-cli api create_draft_comment`: 创建草稿评论
- `icode-cli api get_review_comments`: 获取评审评论
- `icode-cli api set_review_score`: 设置评审分数
