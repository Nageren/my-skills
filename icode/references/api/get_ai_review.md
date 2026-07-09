# get_ai_review - 获取 AI 评审结果

获取 AI 智能代码评审的结果。

## 命令格式

```bash
icode-cli api get_ai_review --conversation-id <会话ID> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--conversation-id` | `-i` | 是 | - | 会话 ID（从 start_ai_review 获取） |
| `--output` | `-o` | 否 | text | 输出格式：json/text |

## 使用示例

```bash
# 获取 AI 评审结果
icode-cli api get_ai_review -i abc123def456

# JSON 格式输出
icode-cli api get_ai_review --conversation-id abc123def456 --output json
```

## 返回数据

### 文本格式

```
Status: OK
Message: 操作成功

Results:
{
  "reviewStatus": "COMPLETED",
  "comments": [
    {
      "file": "src/main.go",
      "line": 42,
      "message": "建议添加错误处理逻辑",
      "severity": "WARNING"
    }
  ],
  "summary": "代码整体质量良好，有 2 处建议改进"
}
```

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "reviewStatus": "COMPLETED",
    "comments": [
      {
        "file": "src/main.go",
        "line": 42,
        "message": "建议添加错误处理逻辑",
        "severity": "WARNING"
      }
    ],
    "summary": "代码整体质量良好，有 2 处建议改进"
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `reviewStatus` | string | 评审状态：PENDING/RUNNING/COMPLETED/FAILED |
| `comments` | array | AI 评审意见列表 |
| `comments[].file` | string | 文件路径 |
| `comments[].line` | int | 代码行号 |
| `comments[].message` | string | 评审意见内容 |
| `comments[].severity` | string | 严重程度：INFO/WARNING/ERROR |
| `summary` | string | 评审总结 |

## 评审状态说明

| 状态 | 含义 |
|------|------|
| `PENDING` | 等待处理 |
| `RUNNING` | 评审进行中 |
| `COMPLETED` | 评审完成 |
| `FAILED` | 评审失败 |

## 注意事项

- **查询者限制**：只有发起 AI 评审的用户才能查询结果
- 如果状态为 `RUNNING`，需要稍后再次查询
- 会话 ID 来自 `start_ai_review` 命令的返回值
