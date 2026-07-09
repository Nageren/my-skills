# get_diff_content

获取文件在两个 commit 之间的 diff 内容。

## 命令格式

```bash
icode-cli api get_diff_content --repo <repo-name> --commit <commit-id> --file <file-path> [--base <base-commit>] [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--commit` | `-c` | 是 | - | 目标 commit ID |
| `--file` | `-f` | 是 | - | 文件路径 |
| `--base` | `-b` | 否 | commit^ | 基准 commit ID，默认为目标 commit 的父提交 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## 使用示例

```bash
# 获取某个文件相对于父 commit 的 diff
icode-cli api get_diff_content --repo baidu/icode/test --commit abc123 --file src/main.go

# 获取两个指定 commit 之间某文件的 diff
icode-cli api get_diff_content --repo baidu/icode/test --commit abc123 --base def456 --file src/main.go
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": {
    "metaA": {
      "name": "src/main.go",
      "lines": 100
    },
    "metaB": {
      "name": "src/main.go",
      "lines": 110
    },
    "changeType": "MODIFIED",
    "content": [
      {
        "ab": ["package main", "", "import ("],
        "common": 3
      },
      {
        "a": ["    \"fmt\""],
        "b": ["    \"fmt\"", "    \"log\""],
        "editA": [0, 1],
        "editB": [0, 2]
      }
    ],
    "diff_header": [
      "diff --git a/src/main.go b/src/main.go",
      "index abc123..def456 100644"
    ]
  }
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态码，OK 表示成功 |
| `data.metaA` | object | 基准版本文件元信息 |
| `data.metaB` | object | 目标版本文件元信息 |
| `data.changeType` | string | 变更类型：MODIFIED、ADDED、DELETED、RENAMED |
| `data.content` | array | diff 内容块列表 |
| `data.content[].ab` | array | 未变更的行（两边相同） |
| `data.content[].a` | array | 基准版本的行（被删除或修改） |
| `data.content[].b` | array | 目标版本的行（新增或修改后） |
| `data.diff_header` | array | diff 头信息 |

## 使用场景

1. **代码差异分析**：查看具体代码变更内容
2. **代码评审**：详细检查修改的代码
3. **变更追踪**：了解某个文件的具体修改

## 相关命令

- `icode-cli api get_diff_file`: 获取变更文件列表
- `icode-cli api get_review_comments`: 获取评审评论
