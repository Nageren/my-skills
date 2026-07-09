# trigger_ai_cr - 触发 AI 代码评审

触发一次 AI 智能代码评审任务，返回会话 ID 用于后续查询结果。

## 命令格式

```bash
icode-cli api start_ai_review --repo <代码库名称> --change-number <CR编号> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--change-number` | `-n` | 是 | - | CR 编号 |
| `--output` | `-o` | 否 | text | 输出格式：json/text |

## 使用示例

```bash
# 触发 AI 评审
icode-cli api start_ai_review --repo baidu/icode/test --change-number 120247220

# JSON 格式输出（获取会话 ID）
icode-cli api start_ai_review -r baidu/icode/test -n 120247220 -o json
```

## 返回数据结构

```json
{
  "status": "OK",
  "message": "操作成功！",
  "data": {
    "conversationId": "abc123def456"
  }
}
```

## 关键字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 操作状态：OK/FAIL |
| `message` | string | 操作消息 |
| `data.conversationId` | string | 会话 ID，用于查询评审结果 |

## 获取会话 ID 示例

```bash
# 触发并提取会话 ID
RESULT=$(icode-cli api start_ai_review -r baidu/icode/test -n 120247220 -o json)
CONVERSATION_ID=$(echo "$RESULT" | icode-cli jq -r '.data.conversationId')
echo "会话 ID: $CONVERSATION_ID"
```

## 注意事项

- **频率限制**：同一用户 60 秒内只能发起一次 AI 评审
- AI 评审是异步执行的，需要使用 `get_ai_review` 查询结果
- 请保存返回的 `conversationId`，用于后续查询
- 需要有该 CR 的访问权限
