# build_fetch_command

根据评审编号生成下载评审代码的 git fetch 命令。内部调用 `get_review_info` 获取评审详情，自动完成取模运算和路径拼接。

## 命令格式

```bash
icode-cli api build_fetch_command --change-number <n> [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## 使用示例

```bash
# 生成 git fetch 命令
icode-cli api build_fetch_command --change-number 12345
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "git fetch command generated",
  "data": {
    "fetch_command": "git fetch ssh://zhangsan@icode.baidu.com:8235/baidu/icode/test refs/changes/45/12345/1 && git checkout FETCH_HEAD",
    "project": "baidu/icode/test",
    "change_number": 12345,
    "current_revision": "1",
    "ref_path": "refs/changes/45/12345/1"
  }
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `fetch_command` | string | 完整的 git fetch 命令 |
| `project` | string | 代码库名称 |
| `change_number` | int | 评审编号 |
| `current_revision` | string | 当前 PatchSet 版本 |
| `ref_path` | string | Git ref 路径 |

## ref_path 计算规则

Git ref 路径格式为：`refs/changes/{last_two}/{change_number}/{revision}`

- `last_two`: 评审编号对 100 取模，补零到两位（如 12345 -> 45）
- `change_number`: 评审编号
- `revision`: 当前 PatchSet 版本号

## 使用场景

1. **下载评审代码**：快速获取评审代码到本地
2. **代码对比**：checkout 到评审代码版本进行对比
3. **本地测试**：在本地测试评审中的代码
4. **自动化脚本**：在脚本中自动获取评审代码

## 典型用法

```bash
# 获取命令并执行
eval $(icode-cli api build_fetch_command -n 12345 -o json | jq -r '.data.fetch_command')

# 或者分步执行
result=$(icode-cli api build_fetch_command -n 12345)
fetch_cmd=$(echo "$result" | jq -r '.data.fetch_command')
eval "$fetch_cmd"
```

## 注意事项

- 需要先配置 SSH 密钥才能执行生成的 fetch 命令
- 生成的命令会 checkout 到 FETCH_HEAD，这是一个临时引用
- 如果需要在此基础上开发，建议创建新分支

## 相关命令

- `icode-cli api get_review_info`: 获取评审详情
- `icode-cli git clone`: 克隆代码库
