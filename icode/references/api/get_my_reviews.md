# get_my_reviews

获取自己或指定用户的评审列表。

## 命令格式

```bash
icode-cli api get_my_reviews [--user <username>] [--status <status>] [--type <type>] [--product-name <name>] [--start-from <n>] [--with-diff-info] [-o json|table|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--user` | `-u` | 否 | 当前用户 | 要查询的用户名 |
| `--status` | `-s` | 否 | OPEN | 评审状态：OPEN/NEW/MERGED/ABANDONED |
| `--type` | `-t` | 否 | owner | 角色类型：owner（我发起的）/reviewer（我评审的） |
| `--product-name` | `-p` | 否 | - | 产品名称（可选过滤） |
| `--start-from` | `-f` | 否 | 0 | 起始位置（分页用） |
| `--with-diff-info` | `-d` | 否 | false | 是否附带差异信息 |
| `--output` | `-o` | 否 | json | 输出格式：json、table、yaml |

## 状态说明

| 状态 | 说明 |
|------|------|
| `OPEN` | 待评审（包含 NEW） |
| `NEW` | 新建的评审 |
| `MERGED` | 已合入 |
| `ABANDONED` | 已废弃 |

## 使用示例

```bash
# 获取当前用户作为 owner 的 OPEN 状态评审（默认）
icode-cli api get_my_reviews

# 获取指定用户作为 reviewer 的已合入评审
icode-cli api get_my_reviews --user zhangsan --status MERGED --type reviewer

# 获取评审并附带差异信息
icode-cli api get_my_reviews --with-diff-info

# 以表格形式输出
icode-cli api get_my_reviews --output table

# 分页查询，从第 10 条开始
icode-cli api get_my_reviews --start-from 10
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": {
    "hasMore": true,
    "startfrom": 0,
    "changes": [
      {
        "project": "baidu/icode/test",
        "branch": "master",
        "subject": "fix: 修复登录问题",
        "updated": "2024-01-15 10:30:00",
        "owner": {
          "username": "zhangsan"
        },
        "current_revision": "abc123",
        "_number": 12345,
        "insertions": 10,
        "deletions": 5
      }
    ]
  }
}
```

### Table 格式

```
User: zhangsan, Role: owner, HasMore: true

Number  Project           Branch  Subject             Owner     Updated
------  -------           ------  -------             -----     -------
12345   baidu/icode/test  master  fix: 修复登录问题   zhangsan  2024-01-15 10:30:00
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `hasMore` | bool | 是否还有更多数据 |
| `startfrom` | int | 当前起始位置 |
| `changes` | array | 评审列表 |
| `changes[].project` | string | 代码库名称 |
| `changes[].branch` | string | 目标分支 |
| `changes[].subject` | string | 提交标题 |
| `changes[]._number` | int | 评审编号 |
| `changes[].owner.username` | string | 提交者用户名 |
| `changes[].updated` | string | 最后更新时间 |

## 使用场景

1. **查看待处理评审**：快速查看自己需要处理的评审
2. **追踪评审状态**：了解自己发起的评审进度
3. **评审人视角**：查看需要自己评审的代码

## 相关命令

- `icode-cli api get_repo_reviews`: 获取仓库的评审列表
- `icode-cli api get_review_info`: 获取评审详情
- `icode-cli api set_review_score`: 设置评审分数
