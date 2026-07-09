# check_repo_permission

检查当前用户是否有指定代码库的操作权限。

## 命令格式

```bash
icode-cli api check_repo_permission --repo <repo-name> [--operation <operation>] [-o json|table|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--operation` | `-p` | 否 | read | 操作类型 |
| `--output` | `-o` | 否 | json | 输出格式：json、table、yaml |

## 操作类型

| 值 | 说明 |
|------|------|
| `read` | 读取权限（默认） |
| `write` | 写入权限 |

## 使用示例

```bash
# 检查是否有代码库的读权限
icode-cli api check_repo_permission --repo baidu/icode/test

# 检查指定操作权限
icode-cli api check_repo_permission --repo baidu/icode/test --operation write

# 以表格形式输出
icode-cli api check_repo_permission --repo baidu/icode/test --output table
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": true
}
```

### Table 格式

```
Repository: baidu/icode/test
Operation: read
Has Permission: Yes
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态码，OK 表示成功 |
| `message` | string | 状态消息 |
| `data` | bool | 是否有权限，true 表示有权限 |

## 使用场景

1. **权限检查**：操作前检查是否有相应权限
2. **条件执行**：根据权限决定后续操作
3. **错误预防**：避免因权限不足导致的操作失败

## 典型用法

```bash
# 在脚本中检查权限后再执行操作
if icode-cli api check_repo_permission --repo baidu/icode/test -o json | jq -e '.data == true' > /dev/null; then
  echo "有权限，继续执行..."
  icode-cli api get_repo_config --repo-names baidu/icode/test
else
  echo "无权限，请申请访问"
fi
```

## 相关命令

- `icode-cli api get_repo_config`: 获取代码库配置
- `icode-cli api get_submit_settings`: 获取提交规则配置
- `icode-cli api get_repo_members`: 获取代码库成员
