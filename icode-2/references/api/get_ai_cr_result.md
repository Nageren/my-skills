# get_ai_cr_result - 获取 AI 评审结果

获取 AI 智能代码评审的执行结果，包括评审状态和具体评论。

## 命令格式

```bash
icode-cli api get_ai_review --conversation-id <会话ID> --repo <代码库名称> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--conversation-id` | `-i` | 是 | - | 会话 ID（从 start_ai_review 获取） |
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--output` | `-o` | 否 | text | 输出格式：json/text |

## 使用示例

```bash
# 获取 AI 评审结果
icode-cli api get_ai_review --conversation-id abc123def456 --repo baidu/icode/test

# JSON 格式输出
icode-cli api get_ai_review -i abc123def456 -r baidu/icode/test -o json
```

## 返回数据结构

```json
{
  "status": "OK",
  "message": "操作成功！",
  "data": {
    "conversationId": "abc123def456",
    "crStatus": "SUSS",
    "results": [
      {
        "id": 1,
        "sessionId": "abc123def456",
        "messageType": "OTHER",
        "processedContent": {
          "text": "代码整体质量良好，有 2 处建议改进"
        },
        "status": "PROCESSED"
      },
      {
        "id": 2,
        "sessionId": "abc123def456",
        "messageType": "INTERLINEAR_COMMENT",
        "processedContent": {
          "id": 1,
          "fileName": "src/main.go",
          "patchSetId": 1,
          "startLine": 42,
          "endLine": 42,
          "severityScore": 7,
          "message": "建议添加错误处理逻辑，避免空指针异常",
          "updated": "2024-01-15 10:30:00"
        },
        "status": "PROCESSED"
      }
    ]
  }
}
```

## 关键字段说明

### crStatus (评审状态)

| 状态 | 含义 | 说明 |
|------|------|------|
| `EXECUTING` | 执行中 | AI 评审正在进行 |
| `TIMEOUT` | 超时 | AI 评审执行超时 |
| `FAIL` | 失败 | AI 评审执行失败 |
| `SUSS` | 成功 | AI 评审完成 |

### messageType (消息类型)

| 类型 | 含义 | 说明 |
|------|------|------|
| `OTHER` | 文本消息 | 通用文本类型（总结、说明等） |
| `INTERLINEAR_COMMENT` | 行内评论 | 具体代码位置的评审意见 |

### processedContent (处理后的内容)

#### OTHER 类型

```json
{
  "text": "代码整体质量良好..."
}
```

#### INTERLINEAR_COMMENT 类型

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 评论 ID |
| `fileName` | string | 文件路径 |
| `patchSetId` | int | 补丁集 ID |
| `startLine` | int | 起始行号 |
| `endLine` | int | 结束行号 |
| `severityScore` | int | 严重程度评分 (1-10) |
| `message` | string | 评审意见内容 |
| `updated` | string | 更新时间 |

## severityScore 严重程度说明

| 分数范围 | 严重程度 | 说明 |
|----------|----------|------|
| 1-3 | 低 | 代码风格、命名建议等 |
| 4-6 | 中 | 代码优化、性能改进建议 |
| 7-10 | 高 | 潜在 bug、安全问题等 |

## 提取需要修复的问题示例

```bash
# 获取 AI 评审结果
RESULT=$(icode-cli api get_ai_review -i abc123def456 -r baidu/icode/test -o json)

# 检查状态
CR_STATUS=$(echo "$RESULT" | icode-cli jq -r '.data.crStatus')

if [ "$CR_STATUS" = "SUSS" ]; then
    # 提取 severityScore >= 5 的行内评论
    ISSUES=$(echo "$RESULT" | icode-cli jq '
        .data.results[] |
        select(.messageType == "INTERLINEAR_COMMENT") |
        .processedContent |
        select(.severityScore >= 5)
    ')

    # 统计问题数量
    ISSUE_COUNT=$(echo "$RESULT" | icode-cli jq '
        [.data.results[] |
         select(.messageType == "INTERLINEAR_COMMENT") |
         .processedContent |
         select(.severityScore >= 5)] | length
    ')

    echo "发现 $ISSUE_COUNT 个需要修复的问题"
fi
```

## 轮询等待完成示例

```bash
CONVERSATION_ID="abc123def456"
REPO_NAME="baidu/icode/test"
MAX_WAIT=1200  # 20 分钟
POLL_INTERVAL=10

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    RESULT=$(icode-cli api get_ai_review -i "$CONVERSATION_ID" -r "$REPO_NAME" -o json)
    STATUS=$(echo "$RESULT" | icode-cli jq -r '.data.crStatus')

    case "$STATUS" in
        "SUSS")
            echo "AI 评审完成"
            break
            ;;
        "FAIL"|"TIMEOUT")
            echo "AI 评审失败: $STATUS"
            exit 1
            ;;
        "EXECUTING")
            echo "AI 评审执行中，等待 ${POLL_INTERVAL} 秒..."
            sleep $POLL_INTERVAL
            elapsed=$((elapsed + POLL_INTERVAL))
            ;;
    esac
done

if [ $elapsed -ge $MAX_WAIT ]; then
    echo "轮询超时"
    exit 1
fi
```

## 注意事项

- **查询者限制**：只有发起 AI 评审的用户才能查询结果
- 如果状态为 `EXECUTING`，需要稍后再次查询
- `processedContent` 的结构根据 `messageType` 不同而不同
- 使用 `severityScore` 字段来判断问题的严重程度
- 建议设置合理的轮询间隔（10 秒）和超时时间（20 分钟）
