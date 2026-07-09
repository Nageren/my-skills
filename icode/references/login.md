# login - 登录认证

检查当前用户的认证状态，或进行登录。

## 命令格式

```bash
# 交互式登录（默认使用 UGate）
icode-cli login

# 非交互式登录
icode-cli login --token "eyJ..."

# 指定认证方式
icode-cli login --method ugate --token "eyJ..."
icode-cli login --method comate --token "Bearer-xxx"
```

## 参数说明

| 参数 | 短参数 | 默认值 | 说明 |
|------|--------|--------|------|
| `--method` | `-m` | `ugate` | 认证方式（ugate/comate） |
| `--token` | `-t` | - | Token（非交互式模式） |

## 使用示例

```bash
# 检查登录状态（已登录则直接返回，未登录则提示输入 token）
icode-cli login

# 使用 UGate token 直接登录
icode-cli login --token "eyJhbGciOiJIUzI1NiIsInR..."

# 使用 Comate token 登录
icode-cli login --method comate --token "Bearer-abc123"
```

## 返回信息

### 已登录状态

```
Already logged in as: zhangsan (ugate)
```

### 登录成功

```
Logged in as: zhangsan (ugate)
```

## 在脚本中使用

```bash
# 获取当前用户名
USERNAME=$(icode-cli login 2>&1 | grep "logged in as" | sed 's/.*as: \([^ ]*\).*/\1/')

# 检查是否登录成功
if icode-cli login 2>&1 | grep -q "logged in as"; then
    echo "已登录"
else
    echo "未登录"
    exit 1
fi
```

## 认证方式

| 认证方式 | Token 获取 | Token 存储 | 优先级 |
|---------|-----------|-----------|--------|
| ugate（默认） | https://uuap.baidu.com/agent/token | `~/.config/uuap/` | order=10 |
| comate | Comate IDE 自动保存 | `~/.comate/login` | order=20 |

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 已登录或登录成功 |
| 1 | 登录失败 |

---

# logout - 登出

登出并清除认证信息。

## 命令格式

```bash
icode-cli logout
```

## 使用示例

```bash
icode-cli logout
```

## 返回信息

```
Logging out zhangsan (ugate)...
Logged out successfully
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 登出成功 |
