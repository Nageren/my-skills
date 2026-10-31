---
name: yunxiao-thoughts-export
description: "导出云效知识库（Thoughts）内容或迁移到飞书时使用。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 云效 Thoughts 知识库导出 / 迁移到飞书

云效知识库（Thoughts）无公开 API 文档，页面需阿里云账号登录。已验证的可行路径：**用本机 Chrome（用户已登录）+ AppleScript 执行页面 JS**，混合使用页面 DOM 提取和同源 API 调用。

## 触发条件

- 用户给出 `thoughts.aliyun.com/workspaces/<id>/...` 链接（overview / folders / docs），要求导出、备份、迁移到飞书/其他平台
- 匿名访问返回 302 → login，`curl` 直连拿不到内容

## 核心流程（4 步）

### 1. 获取登录态（本机 Chrome）

1. 确认 Chrome 在运行：`pgrep -fl "Google Chrome"`。用户已登录云效时，AppleScript 可直接操作其标签页。
2. 要求用户开启：Chrome 菜单「查看」→「开发者」→「允许 Apple 事件中的 JavaScript」（否则 `execute active tab javascript` 报错 12）。开启后通常需重启 Chrome。
3. 用 `osascript` 打开目标页面并读取 `document.title` 验证登录态（标题含「云效 Thoughts · 企业级知识库」即已登录）。

### 2. 执行页面 JS 的三个硬性技巧

- **从文件读取 JS**：多行 JS 直接内嵌 AppleScript 会报 `syntax error: 预期是行的结尾`。把 JS 写入文件，用模板 `references/run_js.applescript` 执行（参数传 JS 文件路径）。
- **同步 XHR 而非 fetch**：`fetch` 返回 Promise，AppleScript 不等异步完成（输出为空）。用 `XMLHttpRequest` + `open(..., false)` 同步获取。
- **导航后轮询**：用 `window.location.href = url` 跳转（AppleScript 的 `set URL` 偶尔不生效），然后每 2 秒探测 `document.querySelector("div[data-slate-editor=true]")` 直到出现，再等 2 秒让内容渲染完。

### 3. 节点树 API（比 DOM 翻页可靠得多）

页面上下文内同源 fetch 自动携带登录态：

```
GET https://thoughts.aliyun.com/api/workspaces/<WS>/nodes?pageSize=1000          # 顶层（返回 folder）
GET .../nodes?pageSize=1000&_parentId=<FOLDER_ID>                                # 子节点（BFS 递归）
```

- 顶层接口只返回 folder；必须按 `_parentId` 递归才能拿全 document 节点
- 节点字段：`_id`（云效 doc/folder id）、`type`（folder|document）、`title`、`_parentId`、`_workspaceId`
- 文档元数据接口 `.../nodes/<id>` 返回 title/summary/creator，但**不含正文**

### 4. 正文提取（Slate 编辑器 DOM → Markdown）

页面正文渲染在 `div[data-slate-editor=true]`（Slate），block 由 `data-type` 标记：
`title` / `header-one` / `header-two` / `header-three` / `paragraph` / `image`；代码块是 `pre`（注意 `[data-type=code]` 会误匹配工具栏 SVG 图标）；表格是标准 `<table>`。

用 `references/slate2md.js` 转换器：逐 block 输出 Markdown（标题→#、表格→管道表、pre→代码块、img→`![image](url)`）。验证过：表格空 thead 行需过滤；`getText()` 需跳过 trigger-box/btn-box/tool-more/copy/hover-area 等 UI 容器。

## 图片处理（关键坑）

- 图片 `<img src>` 的签名 URL **被前端安全截断**（`Signature=eyJhbG...xxx` 中间是 `...`），直接取 src 无法下载；canvas `toDataURL` 会因 CORS taint 报 SecurityError
- **解法**：`https://tcs-devops.aliyuncs.com/thumbnail/<storage_id>/w/2000/h/2000` 无需签名可直接访问（200 image/png）；从 src 正则提取 `storage/([0-9a-f]+)` 重建 thumbnail URL
- ⚠️ 飞书导入 Markdown 时（`docs +update overwrite --doc-format markdown`）**会自动下载 URL 图片并转存为飞书 file token**——含图文档无需手动上传，验证 fetch 结果中 `<img src="file_token">` + `internal-api-drive-stream` authcode 链接即证明转存成功

## 飞书 Wiki 批量导入（lark-cli）

1. 授权：`lark-cli auth login --no-wait --json --domain all` 拿 device_code + verification_url；**ASCII 二维码直接贴终端**（`lark-cli auth qrcode <url> --ascii`）最可靠——链接容易在 TUI 里被用户漏看；后台跑 `auth login --device-code <code>` 轮询
2. 建空间：`lark-cli wiki +space-create --name X --description Y --as user`
3. 按目录树递归：文件夹/文档都用 `wiki +node-create --space-id <SID> --title T [--parent-node-token P] --as user`（飞书 wiki 的"文件夹"就是有子节点的 docx）；返回 `node_token` + `obj_token`
4. 写内容：`cat file.md | lark-cli docs +update --api-version v2 --doc <obj_token> --command overwrite --doc-format markdown --content - --as user`（**stdin 方式**；`--content @file` 只接受相对路径）
5. 幂等续跑：把「云效 node_id → 飞书 node_token」映射存 JSON，重跑时跳过已建节点

## 导入后排版修复（云效 md → 飞书 docx 的残留问题）

云效 Slate 转 Markdown 再被飞书导入后，会产生四类可预测的排版残留：**Plain Text 字样**（代码块/段落尾部）、**段落内 br 堆叠**（一个 `<p>` 里十几行短句）、**全空表头行**、**空白 caption**。修复=本地字符串转换 + XML overwrite 写回（先备份 → dry-run → 批量 → 验证图片数量不变），完整规则与扫描陷阱见 `references/format-fix.md`。

关键规则：编号行→`<ol>`（去数字前缀）、短行(≤80字符)→`<ul>`、长行→拆独立段落；扫描统计必须排除 table/pre 内部内容（否则空单元格/代码 br 大量误报）；overwrite 写回会重新生成图片 file token 但**数量不变**，用 `<img src>` 计数验证无丢图。

## 已验证的坑（lark-cli）

- `wiki +node-delete --node-token <裸token>` 报 not_found(131005)——**传 URL 形式** `https://<domain>.feishu.cn/wiki/<node_token>` 可自动推断 obj_type 并删除成功；或显式 `--obj-type docx`
- 空间/节点创建出错想重来：直接 `wiki +delete-space --yes` 删整个空间重建，比逐个清理残留节点干净
- `wiki nodes` API 只有 copy/create/list（无 delete）；删除走 shortcut 或 drive
- 每个 lark-cli 命令的 `--help` 会提示用 `lark-cli skills read <skill>` 获取版本匹配的文档，不要 grep 本地 SKILL.md

## 排版增强（代码高亮 + 表头/图片的服务器行为）

在排版修复之后可再做一轮增强，**已验证可落地**：

- **代码高亮**：给 `<pre>` 加 `lang` 属性（`<pre lang="sql"><code>…</code></pre>`）→ 飞书渲染端显示语法高亮，属性**持久保存**（fetch 回来仍是 `<pre caption="&#xA;" lang="sql">`）。语言检测启发式（覆盖 28 个真实代码块：sql 13 / java 3 / json 3 / yaml 3 / text 6）：SQL（select/alter table/create table 关键字）、Java（public class/@AllArgsConstructor/import）、JSON（`{` 开头 + `"k": v`）、YAML（`key:` 行开头）、XML、bash；否则 text。完整规则见 `references/format-enhance.md`
- ⚠️ **服务端会静默丢弃的属性**（用独立测试文档实测）：
  - `th background-color="light-gray"` → 写入成功但 fetch 后属性消失
  - `img width="800" height="177"` → 同样被丢弃
  - 结论：**不要**在 XML overwrite 里塞 th 背景色 / img 尺寸，纯属白费。飞书 web 端宽图默认等比缩放、表格表头默认灰底加粗，视觉已达标
- 验证正则注意：`lang` 可能排在 `caption` 之后，用 `<pre[^>]*lang="([^"]+)"`；`img` 用 `<img[^>]*src="` 计数，别用 `width=` 统计（写了也会被丢）

## 跨租户迁移（lark-cli 租户绑定 + 浏览器 CSRF 墙）

把内容迁到**另一个租户**的知识空间时（如 jknokh6yvw → wanlianyida），两条路都是墙，先认清再动手：

- **lark-cli 应用绑定租户**：`lark-cli wiki +space-list --as user` 只列出注册租户的空间；另一租户的空间完全不可见（同一个人也不行）。对另一租户 `drive +inspect` → 131006 permission_denied。user token / user identity 全部租户隔离，**lark-cli 无法跨租户**
- **浏览器内部 API 只读可用、写入被 CSRF 墙**：页面上下文（用户已登录目标租户）里 GET 类内部 API 可用（无需 CSRF）：`/space/api/wiki/v2/tree/get_info/?space_id=X&with_space=true&with_perm=true`、`tree/get_node/`、`perm/node/`、`space/get_info/`——可查空间名、`user_space_perm`（edit_wiki_collaborator/delete_wiki）、`node_operate_control`、节点 owner/creator、`is_wiki_home_page`
- **写入（POST `wiki/v2/tree/create_node`）→ 403 "csrf token error"**。CSRF 机制已逆向：请求头 `X-Csrf-Token` 取自 cookie **`swp_csrf_token`**（`common_shared_vendors_npm_1.88ae6c90.js` 中 `e.CSRF="swp_csrf_token"`；另一套 lib 用 `_csrf_token` → `X-CSRFToken`）。但**即使带上正确 cookie 值仍 403**——token 与页面会话/请求上下文绑定，外部注入不可行。cookie 里 `bv_csrf_token`/`et` 均无效
- **is_wiki_home_page 节点 can_create=false**（飞书设计：空间首页节点列表视图的新建按钮禁用，`perm/node` 返回 can_create:false），普通节点 can_create=true——根级节点创建可能被 `node_operate_control` 限制
- UI 自动化兜底：AppleScript `System Events` 模拟点击需 macOS「辅助功能」权限（未授权报 "不允许辅助访问"）；XHR 拦截器在页面 reload 后丢失
- 跨租户现实可行的出口：① 用户开 macOS 辅助功能权限后全自动；② 用户手动建文件夹/拖拽上传；③ 在目标租户可创建的节点下手动导入。详见 `references/cross-tenant-migration.md`

## 参考文件

- `references/run_js.applescript` — AppleScript 执行 JS 文件模板
- `references/slate2md.js` — Slate DOM → Markdown 转换器（表格/代码块/图片）
- `references/export_all.py` — 批量导出主脚本（导航+轮询+转换+落盘）
- `references/import_to_feishu.py` — 飞书 Wiki 批量导入（递归建节点+写内容+幂等）
- `references/format-fix.md` — 导入后排版修复（Plain Text/br堆叠/空表头 清理规则、扫描陷阱、备份-写回-验证工作流）
- `references/format-enhance.md` — 排版增强：`<pre lang>` 代码高亮 + 语言检测启发式、被服务端静默丢弃的属性（th background-color / img width）、验证正则
- `references/cross-tenant-migration.md` — 跨租户迁移：lark-cli 租户绑定、浏览器内部 API（只读可用/写入 CSRF 墙）、is_wiki_home_page 限制、macOS 辅助权限
