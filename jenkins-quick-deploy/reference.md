# GTSP Jenkins 部署参考

## Jenkins 任务

| 任务 | 用途 | 环境 |
|------|------|------|
| `gtsp-k8s-slave` | GTSP/支付服务 K8s 部署 | develop |

Jenkins 地址：`https://jenkins.10000da.vip/`

## 支付域应用（app 参数）

| app | 说明 |
|-----|------|
| `pay-service-cashier` | 收银台服务 |
| `pay-service-trade` | 交易服务 |
| `pay-service-route` | 路由服务 |
| `pay-service-boss` | Boss 后台 |
| `pay-platform-account` | 账户平台 |
| `pay-web-wallet` | 钱包 Web |
| `pay-channel-allinpay` | 通联渠道 |
| `pay-channel-pingan` | 平安渠道 |
| `pay-channel-yeepay` | 易宝渠道 |
| `pay-channel-logistics` | 物流渠道 |
| `pay-channel-cmb` | 招行渠道 |
| `pay-channel-jsbank` | 江苏银行渠道 |

## GTSP 常用应用

| app | 说明 |
|-----|------|
| `gtsp-account-service` | 账户服务 |
| `gtsp-iam-service` | IAM |
| `gtsp-orch-customer` | 客户编排 |
| `gtsp-knowledge-service` | 知识库 |
| `gtsp-service-mock` | Mock 服务 |

完整列表以 Jenkins `gtsp-k8s-slave` 任务 `app` 下拉选项为准。

## 分支约定

| 应用 | 流水线分支 |
|------|-----------|
| `pay-service-cashier` | `settlement` |

其他应用分支以 Jenkins Pipeline 脚本为准；部署前务必 `git branch --show-current` 核对。

## MCP 配置示例

`~/.cursor/mcp.json` 中 `jenkins-mcp` 节点：

```json
{
  "jenkins-mcp": {
    "command": "uvx",
    "args": ["jenkins-mcp"],
    "env": {
      "JENKINS_URL": "https://jenkins.10000da.vip/",
      "JENKINS_USERNAME": "<username>",
      "JENKINS_PASSWORD": "<password>",
      "JENKINS_USE_API_TOKEN": "false"
    }
  }
}
```
