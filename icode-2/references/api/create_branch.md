# create_branch

基于已有分支创建新分支。

## 命令格式

```bash
icode-cli api create_branch --repo <repo-name> --branch <branch-name> --from <source-branch> [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--branch` | `-b` | 是 | - | 要创建的新分支名 |
| `--from` | `-f` | 是 | - | 基于哪个来源分支创建 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## 使用示例

```bash
# 基于 master 分支创建 feature-x 分支
icode-cli api create_branch \
  --repo baidu/icode/test \
  --branch feature-x \
  --from master

# 基于 release 分支创建 hotfix 分支
icode-cli api create_branch \
  --repo baidu/icode/test \
  --branch hotfix-123 \
  --from release/v1.0
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "Branch created successfully",
  "data": null
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 状态码，OK 表示成功 |
| `message` | string | 状态消息 |

## 使用场景

1. **功能开发**：从主分支创建功能分支
2. **版本发布**：创建发布分支
3. **热修复**：从发布分支创建热修复分支
4. **自动化流程**：CI/CD 中自动创建分支

## 权限要求

- 需要对代码库有写权限
- 需要 TOKEN 认证

## 错误处理

| 错误信息 | 说明 | 解决方案 |
|----------|------|----------|
| `Branch already exists` | 分支已存在 | 使用其他分支名或删除已有分支 |
| `Source branch not found` | 来源分支不存在 | 检查来源分支名称是否正确 |
| `Permission denied` | 无权限 | 确认是否有代码库的写权限 |

## 相关命令

- `icode-cli api get_repo_branch`: 获取分支列表
- `icode-cli git push`: 推送代码
- `icode-cli git push_cr`: 提交代码评审
