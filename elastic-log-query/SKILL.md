---
name: elastic-log-query
description: 通过 Cursor 已接入的 elastic-agent-builder MCP 在 Elasticsearch/Kibana 查应用日志。用户给出 traceId、服务名、时间范围或 KQL/ES|QL 时使用。
---

# Elastic 日志查询（官方 MCP）

## 前置

- Cursor MCP 服务名：`elastic-agent-builder`（Kibana Agent Builder MCP）
- 未连接时提示用户：Settings → MCP → 启用并重载；检查 `~/.cursor/mcp.json` 中 Kibana URL 与 ApiKey

## 查询习惯（pay-service-cashier）

- 服务/容器：`*cashier*`、`pay-service-cashier`
- Trace：日志行 `[TRACE-ID:{...}]` 或字段 `traceId` / `trace_id`（以集群 mapping 为准）
- 级别：`|= "ERROR"`、`|= "CASHIER_"`、`|= "参数错误"`

## 工作流

1. 用 MCP 工具列表确认可用工具（常见为 ES|QL、Agent Builder 工具；以实际 `GetDynamicTools` 为准）
2. 优先 **按 traceId + 时间窗** 缩小范围（例如 ±30 分钟）
3. 再按 **logger 类名** 或 **orderNo** 过滤
4. 结果按时间排序，归纳根因与调用链

## 与 Kibana Discover 对齐

用户在 Kibana 能跑通的查询，尽量原样改写成 MCP/ES|QL；索引模式向用户确认一次后写入对话上下文（如 `filebeat-*`、`logs-*`）。

## 安全

- 不在仓库提交 ApiKey
- 只读日志索引；生产环境 API Key 限制 `logs-*` 等必要 index
