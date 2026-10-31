---
name: feishu-doc-bot-authoring
description: "Feishu docs with lark-cli bot: skeleton, append, cleanup."
---

# 飞书文档 Bot 身份创作工作流

lark-doc skill 覆盖文档操作的常规流程；本 skill 补充**实际跑通**的 bot 身份（`--as bot`）富文档创作全流程，以及 lark-doc 未覆盖的占位块清理与权限授予陷阱。

## 触发条件
- `lark-cli auth status --json` 显示 user 身份过期/缺失（`tokenStatus: expired`），仍需创建/编辑文档
- 用「骨架 + 分段填充」方式创建富文档（8+ 章节、多表格/画板），完成后需清理骨架占位块
- bot 身份创建的文档需要给用户本人开权限

## 关键事实
- user token 过期**不影响** bot 身份操作；bot 创建的文档落在应用绑定租户（本机 jknokh6yvw.feishu.cn，与用户日常浏览的 wanlianyida.feishu.cn 不同域名）
- `docs +create` 返回中 `permission_grant.status=failed`（auto-grant，缺 scope）是**正常现象**，文档已创建成功，勿当错误处理

## 工作流（跑通版）

### 1. 建骨架
内容写 XML 文件，用 `--content @file` 传参（避免 shell 转义）：
- 开头 `<callout>` 放文档定位/结论
- 每章 `<h1>` + 一句占位 `<p>（占位摘要：…，待填充）</p>`

```bash
lark-cli docs +create --api-version v2 --as bot --title "标题" --content @skeleton.xml --format json
```

### 2. 分段 append 填充
每段一个 XML 文件（≤ ~5KB），分多次写入：
```bash
lark-cli docs +update --api-version v2 --as bot --doc "<token>" --command append --content @sec1.xml --format json
```
- 架构图/时序图直接内嵌 `<whiteboard type="mermaid">…</whiteboard>`，随 append 一起写入，无需单独建画板
- 富 block 密度自检：目标 ≥40% 非纯文本块、每 h1 章节 ≥1 个非文本块、开头 callout

### 3. 清理骨架占位块（关键步骤）
```bash
lark-cli docs +fetch --api-version v2 --as bot --doc "<token>" --detail with-ids --format json
```
- 用正则提取块 id：`<(\w+)[^>]*id="([^"]+)"[^>]*>(.*?)</\1>`（re.S），筛出文本含「占位/待填充」的 h1/p
- 批量删除（逗号分隔，一次可删 16+ 块）：
```bash
lark-cli docs +update --api-version v2 --as bot --doc "<token>" --command block_delete --block-id "id1,id2,..."
```

### 4. 验证
再次 fetch，统计块类型与 h1 章节，确认无「待填充」残留、结构完整。

## 权限授予（陷阱）
- **bot 无法 API 代授协作者**：`drive +member-add` 报 `app_scope_not_applied`（缺 `docs:permission.member:create`、`drive:drive` 等 scope）。处理：给用户链接，让其在文档右上角「分享」手动添加协作者；或到报错返回的 `console_url` 申请 scope 后再试
- `drive +member-add` 是 high-risk-write：先 `--dry-run` 预览 → 用户明确同意 → 才加 `--yes`（exit 10 门禁，不可静默重试）
- 交付时告知用户：文档由 bot 应用创建，组织内默认可链接查看，编辑权限需自行添加

## 参考实例
通用风控中台架构文档：8 章节、2 mermaid 画板、15 表格、11 callout、约 2 万字符；16 个占位块一次批量删除成功。
