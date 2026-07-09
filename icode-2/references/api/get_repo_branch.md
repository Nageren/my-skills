# get_repo_branch - 查询代码库分支列表

查询指定代码库的所有分支信息。

## 命令格式

```bash
icode-cli api get_repo_branch --repo <代码库名称> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取分支列表
icode-cli api get_repo_branch --repo baidu/icode/test

# 表格格式输出
icode-cli api get_repo_branch -r baidu/icode/test -o table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": [
    {
      "name": "master",
      "createTime": "2024-01-01 10:00:00",
      "createUser": "zhangsan"
    },
    {
      "name": "develop",
      "createTime": "2024-01-15 14:30:00",
      "createUser": "lisi"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 分支名称 |
| `createTime` | string | 创建时间 |
| `createUser` | string | 创建者用户名 |

## 注意事项

- 需要有代码库的访问权限
- 代码库名称必须是完整的三层目录形式（如 `baidu/icode/test`）
