# get_diff_file

获取两个 commit 之间的变更文件列表。

## 命令格式

```bash
icode-cli api get_diff_file --repo <repo-name> --commit <commit-id> [--base <base-commit>] [-o json|table|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--commit` | `-c` | 是 | - | 目标 commit ID |
| `--base` | `-b` | 否 | commit^ | 基准 commit ID，默认为目标 commit 的父提交 |
| `--output` | `-o` | 否 | json | 输出格式：json、table、yaml |

## 使用示例

```bash
# 获取某个 commit 相对于其父 commit 的变更文件
icode-cli api get_diff_file --repo baidu/icode/test --commit abc123

# 获取两个指定 commit 之间的变更文件
icode-cli api get_diff_file --repo baidu/icode/test --commit abc123 --base def456

# 以表格形式输出
icode-cli api get_diff_file --repo baidu/icode/test --commit abc123 --output table
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": {
    "src/main.go": {
      "status": "M",
      "linesInserted": 10,
      "sizeDelta": 256
    },
    "src/utils.go": {
      "status": "A",
      "linesInserted": 50,
      "sizeDelta": 1024
    }
  }
}
```

### Table 格式

```
Total: 2 files

File          Status  LinesInserted  SizeDelta
----          ------  -------------  ---------
src/main.go   M       10             256
src/utils.go  A       50             1024
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态码，OK 表示成功 |
| `message` | string | 状态消息 |
| `data` | object | 文件变更映射，key 为文件路径 |
| `data[file].status` | string | 文件状态：A(新增)、M(修改)、D(删除)、R(重命名) |
| `data[file].linesInserted` | int | 新增行数 |
| `data[file].sizeDelta` | int | 大小变化（字节） |

## 使用场景

1. **查看提交变更范围**：快速了解某次提交修改了哪些文件
2. **代码评审准备**：在评审前了解变更文件列表
3. **自动化脚本**：根据变更文件触发对应的检查或构建

## 相关命令

- `icode-cli api get_diff_content`: 获取具体文件的 diff 内容
- `icode-cli api get_person_commit`: 查询个人提交记录
- `icode-cli api get_review_info`: 获取评审详情
