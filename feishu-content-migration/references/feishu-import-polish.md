# 飞书侧批量导入 + 排版修复/增强（实战经验，实测 36 篇文档）

云效/外部知识库导出 Markdown 后，导入飞书 wiki 并优化排版的完整经验。

## 一、批量导入飞书 Wiki（lark-cli）

### 建空间与节点
```bash
lark-cli wiki +space-create --name "风控" --description "..." --as user --json   # 返回 space_id
lark-cli wiki +node-create --space-id <SPACE_ID> --title "文件夹名" --as user    # 顶层文件夹
lark-cli wiki +node-create --space-id <SPACE_ID> --parent-node-token <PARENT> --title "文档名" --as user
```
- 飞书 wiki 的"文件夹"也是 docx 节点（有 has_child），用 `--parent-node-token` 挂子节点
- 幂等导入：维护 `云效node_id → 飞书node_token` 映射文件，已创建的跳过（脚本崩溃可续跑）
- 注意 `+node-create` 输出前有 `Creating...` 提示行，解析 JSON 要 `out.find('{')` 截取

### 写入内容（关键坑）
```bash
# ✅ 最可靠：stdin 管道（大文件/中文/特殊字符都安全）
cat content.md | lark-cli docs +update --api-version v2 --doc <OBJ_TOKEN> \
  --command overwrite --doc-format markdown --content - --as user
```
- ❌ `--content-file` 参数**不存在**
- ❌ `--content @/abs/path.md` 必须相对路径，绝对路径报 `invalid file path`
- `--doc` 用 obj_token（docx token），不要传 wiki node_token

### 获取文档 obj_token
```bash
lark-cli wiki +node-get --node-token <NODE_TOKEN> --as user --json
# obj_token 在 data 顶层（NOT data.node.obj_token）
```

### 删除节点/空间
```bash
# ✅ 用 URL 形式（自动推断 obj_type）+ 传 --space-id 跳过 get_node 解析
lark-cli wiki +node-delete --node-token "https://<tenant>.feishu.cn/wiki/<TOKEN>" \
  --space-id <SPACE_ID> --yes --as user
# ❌ 裸 token + --obj-type docx 会报 not_found (131005)
lark-cli wiki +delete-space --space-id <SPACE_ID> --yes --as user   # 空间级删除（异步，会轮询）
```
- 创建重复节点后清理很麻烦 → 空间没内容时**直接删整个空间重建**最干净
- 测试文档可用 `lark-cli drive +delete --file-token <TOKEN> --type docx --yes`

### 图片自动转存（惊喜发现）
飞书 `docs +update overwrite` 导入 Markdown 时，**网络图片 URL 会被自动抓取转存**为飞书内部 file token（fetch 回来是 `<img src="FILE_TOKEN" href="...internal-api-drive-stream.feishu.cn...">`）。无需手动上传。验证方式：fetch 后正则数 `<img[^>]*src=`，与源 md 图片数对比。

### 验证结构完整性
遍历 wiki 树对比源：节点数、文件夹数、文档标题 set 差集（缺失/多余）。写脚本递归 `wiki +node-list --parent-node-token`。

## 二、排版扫描（排除表格/代码块）

直接对全文统计会误报（表格单元格、代码块内换行全是"连续段落"）。正确做法：**先把 `<table>...</table>` 和 `<pre>...</pre>` 替换为占位符**，再统计主体段落：
- 空段落 `<p>\s*</p>`
- 连续纯文本段数（遇 `<h\d>` 重置计数）
- 段落内 `<br/>` 数量
- Plain Text 残留（全文）
- 空表头 `<th><p></p></th>`

## 三、排版修复（写回用 XML）

修复后写回用 `--command overwrite --doc-format xml`（同样 stdin 管道）。**写回前先备份**：fetch 全部文档存 `backup_all.json`（obj_token → title/revision_id/content），可回滚。

### 1. Plain Text 残留
云效 Slate 代码块末尾常带 `Plain Text` 文本 + 零宽字符（`\uFEFF`/`\u200b`）+ `caption="&#xA;"`。清理：
- 删 `Plain Text` 字面量、零宽字符
- 正则 `(?:<br/>\s*)+</code>` → `</code>`（代码块尾部多余换行）
- ` caption="&#xA;"` → 删除

### 2. br 转列表/段落（按行特征智能转换）
段落内 `<br/>` 分隔的多行按规则转换（先删段落首尾孤立 br）：
1. **所有行以数字开头** → `<ol><li>...`（去掉数字前缀）
2. **所有行 ≤ 80 字符** → `<ul><li>...`（去掉数字前缀）
3. **否则** → 每行拆成独立 `<p>`

### 3. 代码块语言检测（语法高亮）
```python
def detect_lang(t):
    first = '\n'.join(t.split('\n')[:5]).lower()
    if re.search(r'\b(select|insert|update|delete|create table|alter table)\b', t, re.I) \
       and re.search(r'\b(from|into|where|values)\b', t, re.I): return 'sql'
    if re.search(r'\b(public|private|class|interface|import|package)\b', t[:500]) \
       or '@AllArgsConstructor' in t: return 'java'
    if re.match(r'^\s*[{\[]', t) and re.search(r'"[^"]+"\s*:', t): return 'json'
    if re.match(r'^[a-zA-Z_-]+:', t.split('\n')[0]): return 'yaml'
    return 'text'
```
写回 `<pre lang="sql">` 等属性，飞书渲染端显示对应语法高亮（实测有效）。

### 4. ⚠️ 飞书 API 忽略的样式属性（重要发现，实测验证）
用 `docs +update` XML 写入以下属性**成功但不生效**（fetch 回来被服务端丢弃）：
- `<th background-color="light-gray">` → 被忽略，表头无自定义底色
- `<img width="800" height="177">` → 被忽略，图片显示尺寸无法用 XML 控制

飞书渲染端默认行为兜底：**表头自动灰底加粗**、**宽图自动等比缩放适配页面宽度**。所以这两项无需在 XML 层处理；用户要求表头底色/图片尺寸时，说明该能力在 API 层不可行，直接告知渲染端默认效果即可。
- `name="test.jpg"` 是飞书服务端自动填充的默认文件名（无害），别浪费时间清理

## 四、知识空间 URL
`https://<tenant>.feishu.cn/wiki/space/<space_id>`（tenant 是 lark-cli 绑定的租户域名，如 jknokh6yvw.feishu.cn）。
