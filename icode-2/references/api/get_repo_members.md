# get_repo_members

获取代码库成员列表，返回详细的成员信息（包含用户名、中文名、邮箱、角色等）。

## 命令格式

```bash
icode-cli api get_repo_members --repo <repo-name> [--role <role>] [-o json|table|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--role` | - | 否 | - | 成员角色过滤，不传则返回所有成员，见下方角色说明 |
| `--output` | `-o` | 否 | json | 输出格式：json、table、yaml |

## 角色说明

| 角色 | 权限等级 | 说明 |
|------|----------|------|
| `ICODE_ADMIN` | 13 | 超级管理员 |
| `CHIEF` | 12 | 负责人 |
| `ADMIN` | 10 | 管理员 |
| `OWNER` | 9 | 写权限人员 |
| `MEMBER` | 8 | 读权限人员 |
| `DELIVERER` | 3 | 交付权限人员 |

> **注意**：`role` 参数为可选，不传时返回所有成员。

## 使用示例

```bash
# 获取代码库所有成员
icode-cli api get_repo_members --repo baidu/icode/test

# 获取代码库管理员
icode-cli api get_repo_members --repo baidu/icode/test --role ADMIN

# 获取代码库负责人
icode-cli api get_repo_members --repo baidu/icode/test --role CHIEF

# 以表格形式输出
icode-cli api get_repo_members --repo baidu/icode/test --output table
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": 200,
  "message": "OK",
  "data": [
    {
      "userName": "zhangsan",
      "chineseName": "张三",
      "email": "zhangsan@baidu.com",
      "role": "ADMIN",
      "roleDescription": "管理员"
    },
    {
      "userName": "lisi",
      "chineseName": "李四",
      "email": "lisi@baidu.com",
      "role": "OWNER",
      "roleDescription": "写权限人员"
    }
  ]
}
```

### Table 格式

```
Repository: baidu/icode/test
Role Filter: All
Total: 2

Username    ChineseName  Email                  Role   RoleDescription
--------    -----------  -----                  ----   ---------------
zhangsan    张三          zhangsan@baidu.com     ADMIN  管理员
lisi        李四          lisi@baidu.com         OWNER  写权限人员
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | int/string | 状态码，200 表示成功 |
| `message` | string | 状态消息 |
| `data` | array | 成员列表 |
| `data[].userName` | string | 用户名 |
| `data[].chineseName` | string | 中文名 |
| `data[].email` | string | 邮箱 |
| `data[].role` | string | 角色枚举值 |
| `data[].roleDescription` | string | 角色中文描述 |

## 错误处理

| 错误信息 | 说明 | 解决方案 |
|----------|------|----------|
| `代码库不存在: xxx` | 代码库不存在 | 检查代码库名称是否正确 |
| `没有操作权限！` | 无权查看成员列表 | 确认是否有该代码库的访问权限 |

## 使用场景

1. **查找评审人**：获取代码库成员作为评审人候选
2. **权限审计**：查看代码库各角色的人员配置
3. **自动化流程**：在脚本中获取管理员或负责人进行通知

## 相关命令

- `icode-cli api get_person_repo`: 查询个人代码库列表
- `icode-cli api get_repo_branch`: 查询代码库分支列表
- `icode-cli api add_reviewers`: 添加评审人
