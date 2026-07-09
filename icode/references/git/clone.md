# clone - 克隆代码库

从 iCode 平台克隆代码库。

## 命令格式

```bash
icode-cli git clone --repo <代码库名称> [--path <本地路径>] [--verbose]
```

如果 `icode-cli` 不在全局 PATH 中，可以使用：

```bash
~/.icode/bin/icode-cli git clone --repo <代码库名称>
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--path` | `-p` | 否 | 代码库名称 | 本地克隆路径 |
| `--verbose` | `-v` | 否 | false | 显示详细输出 |

## 使用示例

```bash
# 克隆代码库（路径默认为代码库名称）
icode-cli git clone --repo baidu/icode/agent-sandbox

# 克隆到指定路径
icode-cli git clone --repo baidu/icode/agent-sandbox --path ./my-agent

# 显示详细输出
icode-cli git clone --repo baidu/icode/agent-sandbox --verbose
```

## 执行流程

克隆命令会自动执行以下操作：

1. **SSH 配置**：执行 SSH 配置脚本（可选，失败不影响克隆）
2. **HTTPS 克隆**：使用 HTTPS 协议下载代码
3. **配置用户信息**：自动设置 `user.name` 和 `user.email`
4. **安装 Hook**：安装 Gerrit 的 `commit-msg` hook

## 输出示例

```
✓ Repository cloned successfully!
  Location: agent-sandbox
  Remote: origin (HTTPS)

Next steps:
  cd agent-sandbox
  # Make your changes
  git add .
  git commit -m 'Your message'
  icode-cli git push_cr --branch master
```

## 注意事项

- 代码库名称必须是完整的三层目录形式（如 `baidu/icode/test`）
- 如果目标路径已存在，克隆会失败
- 需要有该代码库的访问权限
- `commit-msg` hook 用于自动生成 Gerrit Change-Id
