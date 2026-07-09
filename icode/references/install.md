# 工具安装指南

iCode Skill 依赖以下工具，请按需安装。

## icode-cli

iCode 命令行工具，提供 Git 操作、API 调用等功能。

### 版本要求

- 最低版本：>= 0.1.9

### 检测方式

```bash
# 检查是否已安装
which icode-cli

# 或检查用户目录
ls ~/.icode/bin/icode-cli

# 查看版本
icode-cli --version
```

### 安装方式

#### Linux / macOS

```bash
# 安装开发版（推荐，包含最新功能）
curl -sSL http://icode-cli.bj.bcebos.com/install.sh | bash -s -- --no-skills

# 安装稳定版（尚未发布，暂时不能使用）
curl -fsSL http://icode-cli.bj.bcebos.com/install.sh | bash -s -- --force
```

#### Windows

请使用 Git Bash 或 WSL 运行上述安装命令。

### 安装位置

默认安装到 `~/.icode/bin/icode-cli`，安装脚本会自动配置 PATH。

如果 PATH 未生效，可手动添加：

```bash
# bash
echo 'export PATH="$HOME/.icode/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# zsh
echo 'export PATH="$HOME/.icode/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 验证安装

```bash
icode-cli --version
# 输出: icode-cli version 0.1.9

icode-cli login
# 检查登录状态
```

---

## Git

分布式版本控制系统。

### 版本要求

- 最低版本：>= 2.0

### 检测方式

```bash
git --version
# 输出: git version 2.x.x
```

### 安装方式

#### macOS

```bash
# 使用 Homebrew
brew install git

# 或使用 Xcode Command Line Tools
xcode-select --install
```

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install git
```

#### CentOS / RHEL

```bash
sudo yum install git
```

#### Windows

1. 下载 [Git for Windows](https://git-scm.com/download/win)
2. 运行安装程序，按默认选项安装
3. 安装完成后可使用 Git Bash

### 配置 Git

```bash
# 配置用户名和邮箱
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@baidu.com"

# 验证配置
git config --list
```

---

## 环境验证

安装完成后，运行以下命令验证环境：

```bash
# 检查 icode-cli
icode-cli --version

# 检查 git
git --version

# 检查登录状态
icode-cli login
```

所有检查通过后，即可开始使用 iCode Skill。
