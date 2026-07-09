# get_person_commit - 查询个人提交记录

查询用户在指定时间范围内的代码提交记录。

## 命令格式

```bash
icode-cli api get_person_commit [--target <用户名>] [--begin-date <开始日期>] [--end-date <结束日期>] [--page-no <页码>] [--page-size <每页数量>] [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--target` | `-t` | 否 | 当前用户 | 目标用户名 |
| `--begin-date` | `-b` | 否 | 今天 | 开始日期（YYYY-MM-DD） |
| `--end-date` | `-e` | 否 | 今天 | 结束日期（YYYY-MM-DD） |
| `--page-no` | `-p` | 否 | 1 | 页码 |
| `--page-size` | `-s` | 否 | 50 | 每页数量 |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 查询今天的提交记录
icode-cli api get_person_commit

# 查询指定用户的提交
icode-cli api get_person_commit --target zhangsan

# 查询指定时间范围的提交
icode-cli api get_person_commit --begin-date 2024-01-01 --end-date 2024-01-31

# 分页查询
icode-cli api get_person_commit -b 2024-01-01 -e 2024-01-31 -p 2 -s 20

# 表格格式输出
icode-cli api get_person_commit -b 2024-01-01 -e 2024-01-31 -o table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "page": {
      "pageNo": 1,
      "pageSize": 50,
      "totalCount": 100
    },
    "results": [
      {
        "commitId": "abc123def456",
        "author": "zhangsan",
        "commitTime": "2024-01-15 14:30:00",
        "addLines": 100,
        "deleteLines": 20,
        "subject": "feat: add new feature"
      }
    ]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `commitId` | string | 提交 ID |
| `author` | string | 作者用户名 |
| `commitTime` | string | 提交时间 |
| `addLines` | int | 新增行数 |
| `deleteLines` | int | 删除行数 |
| `subject` | string | 提交信息 |

## 使用场景

- 统计代码提交量
- 生成工作日报/周报
- 查看自己或他人的提交历史

## 注意事项

- 可以查询其他用户的公开提交记录
- 日期范围不宜过大，建议按月查询
