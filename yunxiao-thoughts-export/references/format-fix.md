# 云效 Markdown → 飞书 docx 的导入后排版修复

云效 Slate 转出的 Markdown 被飞书 `docs +update overwrite --doc-format markdown` 导入后，会产生四类可预测的排版残留。修复方式 = **本地字符串转换 → XML overwrite 写回**（先备份、dry-run、批量、验证）。

## 问题清单（用 docs +fetch 扫描确认）

| 问题 | 表现形式 | 根因 |
|---|---|---|
| Plain Text 残留 | 代码块/段落尾部出现字面量 `Plain Text`（常带零宽字符 `\uFEFF`/`\u200b` 或前导 `<br/>`） | 云效编辑器导出时把空段落渲染成占位文本 |
| br 堆叠 | 一个 `<p>` 内十几行 `<br/>` 分隔的短句 | 云效里同一段落的多行被保留为 br |
| 空表头 | `<thead>` 行所有 `<th>` 均无文本 | 源表格首行为空行，转换器过滤逻辑不完整时残留 |
| 空白 caption | `caption="&#xA;"` | 飞书导入空 caption 的占位 |

## 修复规则（Python 正则，本地转换后写回）

按顺序执行：

1. **清理零宽/BOM**：`\uFEFF`、`\u200b` → 删除
2. **Plain Text**：字面量 → 删除；`<br/>\s*</code>` → `</code>`（连续多个 br 同理）
3. **空白 caption**：` caption="&#xA;"` → 删除
4. **全空 thead**：thead 内所有 th 文本为空 → 整行删除（部分空的保留——那是内容问题不是排版问题）
5. **段落首尾孤立 br**：`<p>((?:(?!</p>).)*?)<br/></p>` → `<p>\1</p>`（尾部），`<p><br/>((?:(?!</p>).)*?)</p>` → `<p>\1</p>`（首部），`<p><br/><br/>` → `<p>`
6. **br 段落转换**（对仍含 br 的纯文本段落，按优先级）：
   - **全行编号**（每行匹配 `^\d+[.、．)）]?\s*\S`）→ `<ol><li>…</li></ol>`，**去数字前缀**
   - **全行 ≤80 字符** → `<ul><li>…</li></ul>`（同样去数字前缀）
   - 否则 → 每行拆成独立 `<p>`
   - 正则匹配范围：`<p>([^<>]*(?:<br/>[^<>]*)+)</p>`（只处理纯文本段落，不碰含块级标签的）
7. **空段落**：`<p>\s*</p>` → 删除

## 工作流（顺序执行）

1. **备份**：遍历 wiki 空间全部 docx 节点，`docs +fetch --api-version v2` 全量存 `backup_all.json`（含 title/revision_id/content）——可回滚
2. **dry-run**：本地跑转换，统计变更文档数、检查残留问题为 0（Plain Text 无、全空表头无）
3. **批量写回**：`cat fix.xml | lark-cli docs +update --api-version v2 --doc <obj_token> --command overwrite --doc-format xml --content - --as user`（XML 格式写回，逐篇判断 `"success" in out`，失败单独记录）
4. **验证**：
   - 重新 fetch 全文，确认无 Plain Text、主体空段落 ≤2、无尾部 br
   - **图片数量不变**（`<img src="…">` 计数；overwrite 会重新生成 file token，但数量必须一致）
   - 抽查含表格/代码块的文档确认结构完整

## 扫描陷阱（避免误报）

- **必须排除 table/pre 内部内容再统计段落问题**：空单元格、代码内 br 都会被当成"空段落/br 过多"误报（本 session 第一次扫描 33/36 篇"有问题"，排除后只有 23 篇真有问题，再修正计数逻辑后收敛到 19 篇 br 相关）
- **「连续纯文本」计数遇标题（h1-h4）重置**：跨标题的连续段落不算"连续"
- 用 `re.finditer(r'<(h\d|p)[^>]*>(.*?)</\1>', body, re.S)` 按 token 流计数，而不是把所有 `<p>` 混在一起
- 转换后校验 XML 合法性（标签闭合、`<br/>` 自闭合），避免 overwrite 写入畸形 XML 报错

## 实测数据

36 篇文档：29 篇有变更、0 失败、20 张图片全保留、无残留问题。典型修复效果：`<p>交互字段<br/>车辆所有人…</p>` → `<ul><li>交互字段</li>…</ul>`；编号步骤 `1.xxx<br/>2.xxx` → `<ol><li>xxx</li>…</ol>`。
