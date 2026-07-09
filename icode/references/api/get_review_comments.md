# get_review_comments - 获取评审评论

获取代码评审的所有评论信息。

## 命令格式

```bash
icode-cli api get_review_comments --change-number <评审编号> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取评审评论
icode-cli api get_review_comments -n 12345

# 表格格式输出
icode-cli api get_review_comments --change-number 12345 --output table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "src/main.go": [
      {
        "id": "comment_123",
        "path": "src/main.go",
        "author": {
          "name": "张三"
        },
        "line": 42,
        "unresolved": true,
        "message": "这里需要添加错误处理"
      }
    ],
    "src/util.go": [
      {
        "id": "comment_124",
        "path": "src/util.go",
        "author": {
          "name": "李四"
        },
        "line": 15,
        "unresolved": false,
        "message": "建议使用常量替代魔数"
      }
    ]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 评论 ID |
| `path` | string | 文件路径 |
| `author.name` | string | 评论作者 |
| `line` | int | 评论所在行号 |
| `unresolved` | bool | 是否未解决 |
| `message` | string | 评论内容 |

## 评论状态

| unresolved | 含义 |
|------------|------|
| true | 评论未解决，需要处理 |
| false | 评论已解决 |

## 注意事项

- 需要有该评审的访问权限
- 评论按文件分组返回
- 未解决的评论可能阻塞评审合并
