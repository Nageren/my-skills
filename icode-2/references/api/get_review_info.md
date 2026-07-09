# get_review_info - 获取评审详细信息

获取指定评审的详细信息。

## 命令格式

```bash
icode-cli api get_review_info --change-number <评审编号> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取评审详情
icode-cli api get_review_info -n 12345

# 表格格式输出
icode-cli api get_review_info --change-number 12345 --output table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "changeId": "I1234567890abcdef",
    "subject": "feat: add new feature",
    "status": "NEW",
    "branch": "master",
    "project": "baidu/icode/test",
    "owner": {
      "name": "张三",
      "email": "zhangsan@baidu.com"
    },
    "mergeable": true,
    "created": "2024-01-15 10:00:00",
    "updated": "2024-01-15 14:30:00",
    "revisionId": "abc123"
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `changeId` | string | Change ID（Gerrit 格式） |
| `subject` | string | 评审主题 |
| `status` | string | 评审状态：NEW/MERGED/ABANDONED |
| `branch` | string | 目标分支 |
| `project` | string | 所属项目 |
| `owner.name` | string | 提交者姓名 |
| `owner.email` | string | 提交者邮箱 |
| `mergeable` | bool | 是否可合并 |
| `created` | string | 创建时间 |
| `updated` | string | 更新时间 |
| `revisionId` | string | 当前版本 ID |

## 评审状态说明

| 状态 | 含义 |
|------|------|
| `NEW` | 待处理的评审 |
| `MERGED` | 已合并 |
| `ABANDONED` | 已放弃 |

## 注意事项

- 需要有该评审的访问权限
- `mergeable` 为 true 表示评审可以合并
