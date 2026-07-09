# get_repo_config

获取代码库的配置信息（语言、工作流、保密类型等）。

## 命令格式

```bash
icode-cli api get_repo_config --repo-names <repo-names> [--check-permission] [-o json|table|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo-names` | `-r` | 是 | - | 代码库名称，逗号分隔，最多 20 个 |
| `--check-permission` | - | 否 | false | 查询前检查读权限 |
| `--output` | `-o` | 否 | json | 输出格式：json、table、yaml |

## 使用示例

```bash
# 获取单个代码库的配置
icode-cli api get_repo_config --repo-names baidu/icode/test

# 获取多个代码库的配置（逗号分隔，最多 20 个）
icode-cli api get_repo_config --repo-names baidu/icode/test,baidu/icode/test1

# 先检查权限再查询
icode-cli api get_repo_config --repo-names baidu/icode/test --check-permission

# 以表格形式输出
icode-cli api get_repo_config --repo-names baidu/icode/test --output table
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": [
    {
      "fullname": "baidu/icode/test",
      "language": "Go",
      "pdbProductId": 12345,
      "accountId": "100001",
      "repoWorkflowType": "WORKFLOW_CR",
      "secret": "public",
      "secLevel": "L1",
      "templateName": "default"
    }
  ]
}
```

### Table 格式

```
Total: 1 repositories

FullName          Language  WorkflowType  Secret
--------          --------  ------------  ------
baidu/icode/test  Go        WORKFLOW_CR   public
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `fullname` | string | 代码库全名 |
| `language` | string | 主要编程语言 |
| `pdbProductId` | int | PDB 产品 ID |
| `accountId` | string | 账户 ID |
| `repoWorkflowType` | string | 工作流类型（如 WORKFLOW_CR） |
| `secret` | string | 保密类型（public/private/secret） |
| `secLevel` | string | 安全等级 |
| `templateName` | string | 模板名称 |

## 使用场景

1. **了解代码库配置**：查看代码库的基本配置信息
2. **批量查询**：一次查询多个代码库的配置
3. **自动化脚本**：根据配置决定后续操作

## 相关命令

- `icode-cli api get_submit_settings`: 获取提交规则配置
- `icode-cli api check_repo_permission`: 检查代码库权限
- `icode-cli api get_person_repo`: 查询个人代码库列表
