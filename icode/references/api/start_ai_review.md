# start_ai_review - 发起 AI 代码评审

发起一个 AI 智能代码评审任务。

## 命令格式

```bash
icode-cli api start_ai_review --change-number <评审编号> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--output` | `-o` | 否 | text | 输出格式：json/text |

## 使用示例

```bash
# 发起 AI 评审
icode-cli api start_ai_review -n 12345

# JSON 格式输出（获取会话 ID）
icode-cli api start_ai_review -n 12345 --output json
```

## 返回数据

### 文本格式

```
Status: OK
Message: 操作成功
Conversation ID: abc123def456

Use 'get_ai_review' with this conversation ID to query results
```

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "conversationId": "abc123def456"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 操作状态 |
| `message` | string | 操作消息 |
| `conversationId` | string | 会话 ID，用于查询评审结果 |

## 使用流程

1. 使用 `start_ai_review` 发起 AI 评审，获取 `conversationId`
2. 使用 `get_ai_review` 查询评审结果

```bash
# 1. 发起评审
icode-cli api start_ai_review -n 12345 -o json
# 返回: {"conversationId": "abc123"}

# 2. 查询结果
icode-cli api get_ai_review -i abc123
```

## 注意事项

- **频率限制**：同一用户 60 秒内只能发起一次 AI 评审
- AI 评审是异步执行的，需要使用 `get_ai_review` 查询结果
- 请保存返回的 `conversationId`，用于后续查询
- 需要有该评审的访问权限
