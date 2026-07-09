# iCode Git 操作

提供与 iCode 平台集成的 Git 操作命令，包括代码克隆、推送和代码评审（CR）提交。

## 命令概览

| 命令 | 说明 | 文档 |
|------|------|------|
| `clone` | 克隆代码库 | [clone.md](clone.md) |
| `push` | 直接推送到远程分支 | [push.md](push.md) |
| `push_cr` | 推送到 Gerrit 进行代码评审 | [push_cr.md](push_cr.md) |

## 快速开始

### 1. 克隆代码库

```bash
icode-cli git clone --repo baidu/icode/test
```

### 2. 提交代码评审

```bash
cd test
# 修改代码...
git add .
git commit -m "feat: add new feature"

# 推送到 Gerrit 进行代码评审
icode-cli git push_cr --branch master
```

### 3. 直接推送

```bash
# 推送到远程分支（不经过代码评审）
icode-cli git push --branch develop
```

## 特性

- **HTTPS 克隆**：自动使用 HTTPS 协议克隆代码
- **Git 配置**：自动配置 user.name 和 user.email
- **Gerrit Hook**：自动安装 commit-msg hook，确保提交包含 Change-Id
- **智能推送**：自动识别远程仓库并配置 HTTPS remote

## 工作流示例

### 完整的代码评审流程

```bash
# 1. 克隆仓库
icode-cli git clone --repo baidu/icode/my-project

# 2. 进入目录并创建特性分支
cd my-project
git checkout -b feature/new-feature

# 3. 开发并提交
# ... 编写代码 ...
git add .
git commit -m "feat: implement new feature"

# 4. 推送到 Gerrit 进行代码评审
icode-cli git push_cr --branch master

# 5. 评审通过后，代码会被合并到 master 分支
```
