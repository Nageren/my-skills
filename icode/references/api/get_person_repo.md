# get_person_repo - 查询个人代码库列表

查询用户有权限访问的代码库列表。

## 命令格式

```bash
icode-cli api get_person_repo [--page-no <页码>] [--page-size <每页数量>] [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--page-no` | `-p` | 否 | 1 | 页码，从 1 开始 |
| `--page-size` | `-s` | 否 | 50 | 每页数量 |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取代码库列表（默认格式）
icode-cli api get_person_repo

# 使用分页
icode-cli api get_person_repo --page-no 2 --page-size 20

# 表格格式输出
icode-cli api get_person_repo --output table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": [
    {
      "name": "test-repo",
      "fullName": "baidu/icode/test-repo",
      "language": "Go",
      "description": "测试代码库"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 代码库名称（最后一级） |
| `fullName` | string | 完整路径（三层目录） |
| `language` | string | 主要编程语言 |
| `description` | string | 代码库描述 |

## 注意事项

- 只能查询当前认证用户有权限的代码库
- 大量代码库时建议使用分页参数
