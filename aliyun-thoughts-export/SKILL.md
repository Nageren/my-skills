---
name: aliyun-thoughts-export
description: 导出云效知识库（thoughts.aliyun.com）内容到飞书。用户说「把云效知识库放到飞书」时用。
---

# 云效知识库导出（thoughts.aliyun.com → 飞书/其他平台）

将云效 Thoughts 知识库（workspaces/{id}）全部文档迁移到飞书 wiki 或其他平台。核心难点是**登录墙**（curl/headless 浏览器会被 302 到登录页）和**图片签名 URL 被前端截断**。解决方案：用用户已登录的 Chrome 注入 JS。

## 前置条件（必须让用户先做）

1. 用户在自己的 Chrome 打开知识库并登录
2. 用户开启菜单：**查看 → 开发者 → 允许 Apple 事件中的 JavaScript**（可能需重启 Chrome 生效；重启后标签页和登录态自动恢复）
3. 验证注入可用：`osascript -e 'tell application "Google Chrome" to execute active tab of front window javascript "document.title"'` 能返回页面标题即生效。若报错 `36:191 execution error ... 已关闭` 说明设置未生效（检查用户是否真的勾选 + 重启）

## 关键技术点（踩过的坑）

### AppleScript 注入 JS 的坑
- **多行/复杂 JS 内联到 osascript 会报 `syntax error: 预期是行的结尾`**。解法：把 JS 写入 `.js` 文件，AppleScript 里 `set js to read POSIX file jsFile` 再 `execute active tab javascript js`
- **异步 fetch/Promise 的结果拿不到**（AppleScript 不等 Promise 就返回）。必须用**同步 XMLHttpRequest**（`xhr.open('GET', url, false)`）
- `make new tab` 可能开进**新窗口** → 用返回值拿到 window id，后续统一 `tell window id N`
- 导航用 `set URL of active tab`，加载完成靠轮询 `document.querySelector('div[data-slate-editor=true]')` 出现（每 2s，最多 ~40s），出现后再等 2s 确保渲染完

### 知识库 API（页面上下文 XHR 自动带登录态）
- `GET /api/workspaces/{ws}/nodes?pageSize=1000` — 顶层节点（folder/document）
- 加 `&_parentId={folderId}` — 取子节点，**folder 需 BFS 递归**（顶层 API 只返回 folder，不会带出子文档！）
- `nodes/{id}` — 元数据（title/creator/contentsEditor），**不含正文**
- 正文只能从 DOM 提取：`div[data-slate-editor=true]`

### Slate 编辑器 DOM → Markdown
- block 的 `data-type`：title / header-one / header-two / header-three / header-four / paragraph / image / table
- **代码块陷阱**：`[data-type=code]` 会匹配到工具栏 SVG 图标（误伤）。真实代码在 `<pre>`（父级 `code-wrapper`）内，直接取 `pre.innerText`，文本完整
- 表格：标准 HTML `<table>`（thead/tbody/tr/td），**必须过滤全空行**（空 thead 行会污染表头）
- 正文容器 class：`.content__j_QW` / `.editor__1NQI`，编辑器根是 `div[data-slate-editor=true]`
- 完整转换器见 `scripts/slate2md.js`（含表格/代码块/图片，已实测 36 篇）

### 图片下载（关键坑）
- DOM 中 `img.src` 被前端**截断**（中间是 `...`，如 `?Signature=eyJhbG...ZDVj`）；`performance.getEntriesByType('resource')` 拿到的也是截断版
- `canvas.toDataURL()` 报 `SecurityError: Tainted canvases`（跨域污染，不可用）
- **可用方案**：`https://tcs-devops.aliyuncs.com/thumbnail/{fileId}/w/2000/h/2000` **无需签名**直接下载（返回完整 PNG，实测 2000px 约 160KB；原图 `storage/{fileId}` 无签名 403）
- 从截断 src 中用正则 `storage\/([0-9a-f]+)` 提取 fileId 即可，无需完整签名

## 导出流程

1. 遍历节点树（BFS 递归 folder）→ 保存 nodes_all.json
2. 对每篇 document：导航 `/docs/{id}` → 轮询编辑器 → 注入转换器 → 存 `<docId>__<标题>.md`
3. 从 md 正则提取 `!\[image\]\((...)\)` → 换 thumbnail 源下载（urllib + UA/Referer 头）
4. 导入飞书：lark-wiki / lark-doc skill。**注意 lark-cli 的 user 身份会过期**（refresh token），先 `lark-cli auth status` 检查；`wiki +space-create` 仅支持 user 身份，需 `lark-cli auth login` 设备流重新授权（`--no-wait --json` 拿链接 → 用户浏览器授权 → `--device-code` 完成；二维码 `lark-cli auth qrcode`，输出路径必须相对当前目录；用户看不到链接时用 `--ascii` 直接输出终端二维码）。**设备码 600s 过期**：`--device-code` 放后台跑 + notify，用 `lark-cli auth status` 判断是否授权成功（别读后台进程输出，旧进程过期报错会误导）；用户没及时操作就重发新链接+二维码（详见 `feishu-content-migration/references/yunxiao-kb-to-feishu.md`）
5. 导入用 `docs +update --command overwrite --doc-format markdown --content -`（stdin 管道，最可靠）；飞书自动转存图片。**迁移后排版修复/增强**（Plain Text 残留、br 转列表、代码 lang 高亮、飞书 API 忽略的样式属性）见 `feishu-content-migration/references/feishu-import-polish.md`

## 文件

- `scripts/slate2md.js` — Slate DOM → Markdown 转换器（v2 完整版）
- `references/export-pipeline.md` — 完整流水线实现要点（AppleScript runner、同步 XHR 模板、Python 编排骨架）
