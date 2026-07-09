# get_machine_check - 获取机器检查结果

获取代码评审的自动化机器检查结果，包括代码规范检查、静态分析等。

## 命令格式

```bash
icode-cli api get_machine_check --change-number <评审编号> [--output <格式>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--output` | `-o` | 否 | json | 输出格式：json/yaml/table |

## 使用示例

```bash
# 获取机器检查结果
icode-cli api get_machine_check -n 12345

# 表格格式输出
icode-cli api get_machine_check --change-number 12345 --output table
```

## 返回数据

### JSON 格式

```json
{
  "status": "OK",
  "message": "操作成功",
  "data": {
    "checks": [
      {
        "name": "lint-check",
        "status": "PASSED",
        "message": "代码规范检查通过"
      },
      {
        "name": "unit-test",
        "status": "FAILED",
        "message": "2 个测试用例失败"
      }
    ]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 检查项名称 |
| `status` | string | 检查状态：PASSED/FAILED/RUNNING |
| `message` | string | 检查结果说明 |

## 检查状态说明

| 状态 | 含义 |
|------|------|
| `PASSED` | 检查通过 |
| `FAILED` | 检查失败 |
| `RUNNING` | 检查进行中 |

## 注意事项

- 需要有该评审的访问权限
- 机器检查结果会影响评审是否可以合并
- 部分检查可能需要等待一段时间才能完成
