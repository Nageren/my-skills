# push - 直接推送到远程分支

将当前分支直接推送到远程仓库。

## 命令格式

```bash
icode-cli git push [--repo-path <仓库路径>] [--branch <分支名>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo-path` | `-r` | 否 | 当前目录 | Git 仓库路径 |
| `--branch` | `-b` | 否 | 当前分支 | 目标分支名称 |

## 使用示例

```bash
# 推送当前分支到远程
icode-cli git push

# 推送到指定分支
icode-cli git push --branch develop

# 从指定仓库路径推送
icode-cli git push --repo-path ./my-project --branch main
```

## 执行流程

1. **检查仓库**：确认当前目录是 Git 仓库
2. **检查凭证**：检查 Git 凭证配置
3. **获取远程**：从 origin 获取远程 URL
4. **配置 HTTPS**：确保 HTTPS 远程可用
5. **推送代码**：执行 `git push`

## 输出示例

```
✓ Push successful!

Output:
To https://icode.baidu.com/baidu/icode/test
   abc123..def456  develop -> develop
```

## push vs push_cr

| 命令 | 用途 | 推送目标 |
|------|------|----------|
| `push` | 直接推送到远程分支 | `origin/branch` |
| `push_cr` | 提交代码评审 | `refs/for/branch` |

- **push**：适用于有直接推送权限的分支（如个人分支）
- **push_cr**：适用于需要代码评审的分支（如 master）

## 注意事项

- 必须在 Git 仓库内执行，或使用 `--repo-path` 指定仓库路径
- 需要有目标分支的推送权限
- 如果远程分支有新的提交，可能需要先拉取合并
- 某些分支可能配置了保护规则，不允许直接推送
