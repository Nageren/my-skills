# get_repo_reviews - 查询代码库评审列表

查询指定代码库的评审（CR）列表。

## 命令格式

```bash
icode-cli api get_repo_reviews --repo <代码库名称> [--status <状态>] [--start-from <起始位置>] [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--status` | `-s` | 否 | NEW | 评审状态：NEW/MERGED/ABANDONED |
| `--start-from` | `-f` | 否 | 0 | 分页起始位置 |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取待处理的评审（NEW 状态）
icode-cli api get_repo_reviews --repo baidu/icode/test

# 获取已合并的评审
icode-cli api get_repo_reviews --repo baidu/icode/test --status MERGED

# 获取已放弃的评审
icode-cli api get_repo_reviews -r baidu/icode/test -s ABANDONED

# 分页查询
icode-cli api get_repo_reviews -r baidu/icode/test --start-from 10

# 表格格式输出
icode-cli api get_repo_reviews -r baidu/icode/test -o table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "changes": [
      {
        "number": 12345,
        "subject": "feat: add new feature",
        "owner": {
          "username": "zhangsan"
        },
        "project": "baidu/icode/test",
        "branch": "master",
        "updated": "2024-01-15 14:30:00"
      }
    ],
    "hasMore": true,
    "startFrom": 0
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `number` | int | 评审编号（Change Number） |
| `subject` | string | 评审主题 |
| `owner.username` | string | 提交者用户名 |
| `project` | string | 所属项目 |
| `branch` | string | 目标分支 |
| `updated` | string | 最后更新时间 |
| `hasMore` | bool | 是否有更多数据 |
| `startFrom` | int | 当前起始位置 |

## 评审状态说明

| 状态 | 含义 |
|------|------|
| `NEW` | 待处理的评审，等待审核或合并 |
| `MERGED` | 已合并的评审 |
| `ABANDONED` | 已放弃的评审 |

## 注意事项

- 需要有代码库的访问权限
- 返回结果按更新时间倒序排列
- 使用 `hasMore` 字段判断是否有更多数据
