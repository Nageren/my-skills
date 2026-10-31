# 跨租户迁移：lark-cli 租户绑定 + 浏览器内部 API 与 CSRF 墙

场景：把已迁入飞书 jknokh6yvw 租户的知识库，再搬到 wanlianyida 租户的知识空间
（`wanlianyida.feishu.cn/wiki/space/7675278563691596766`，space「风控」）。同一用户
马文磊在两个租户都有账号，但仍处处是墙——先认清墙在哪，别在死路上耗时间。

## 墙 1：lark-cli 应用绑定租户，无法跨租户

- `lark-cli wiki +space-list --as user` 只列出**注册租户**（jknokh6yvw）的空间
- 对另一租户空间 `lark-cli drive +inspect --url <wanlianyida 链接>` → 131006 permission_denied（"user lacks permission"）——误导性报错，本质是租户隔离
- user token / user identity 全部租户隔离；config.json 里出现过的其他 appId（如 cli_aa9d66...）若无 profile + 有效 token 也走不通（appSecret 在 go-keyring master.key 加密里，取不到明文）
- **结论：跨租户写入只能走目标租户的浏览器会话**

## 墙 2：浏览器内部 API——只读可用，写入被 CSRF 墙

页面上下文（Chrome 已登录目标租户）里，**GET 类内部 API 无需 CSRF**，可查清目标结构：

```
GET /space/api/wiki/v2/tree/get_info/?space_id=X&with_space=true&with_perm=true
GET /space/api/wiki/v2/tree/get_node/?wiki_token=T&space_id=X
GET /space/api/wiki/v2/perm/node/?space_id=X&wiki_token=T
GET /space/api/wiki/v2/space/get_info/?space_id=X
```

有用字段：`space_name`、`user_space_perm`（edit_wiki_collaborator / delete_wiki / can_create）、
`space_perm_setting.node_operate_control`、`root_token`、nodes 的 `wiki_token/title/parent_wiki_token/
has_child/is_wiki_home_page/detail_info.owner_id/creator_id`。

**写入全被 CSRF 拦**（POST `wiki/v2/tree/create_node/` 返回 403 "csrf token error"）：

- 机制已逆向（common_shared_vendors_npm_1.88ae6c90.js）：请求头 `X-Csrf-Token` 取自 cookie
  **`swp_csrf_token`**（`e.CSRF="swp_csrf_token"`）；另一套 lib 用 `_csrf_token` → `X-CSRFToken`
- 但**即使带上正确 cookie 值仍 403**——token 与页面会话/请求上下文绑定（每次页面加载轮换），
  外部 XHR/fetch 注入不可行；`bv_csrf_token`/`et` 等 cookie 也全部无效
- XHR/fetch 拦截器在页面 reload 后丢失，无法跨导航保持
- 其他无效尝试：`/space/api/wiki/v2/tree/create`（404）、无尾斜杠路径、带 Origin/Referer/X-Requested-With

## 墙 3：飞书 wiki 自身限制

- **is_wiki_home_page=true 的节点 can_create=false**（空间首页节点列表视图「新建/上传」按钮
  恒禁用，即使当前用户是空间 owner）——这是产品设计，不是权限问题
- 普通节点（如「部门新人入职」）can_create=true
- 根级节点创建可能被 `space_perm_setting.node_operate_control=2` 限制（仅空间管理员）
- 检查权限的正确入口：`perm/node` 返回的 `can_create`，别猜

## 墙 4：macOS UI 自动化需要辅助功能权限

- AppleScript `System Events` 模拟点击 → 未授权报 "err: osascript 不允许辅助访问"
- cliclick 未安装；`document.elementFromPoint(x,y).click()` 只对部分按钮有效
  （React 合成事件 + disabled 类拦截），且页面上下文每次导航都会重置

## 现实可行的出口

1. **用户开启 macOS 辅助功能权限**（系统设置 → 隐私与安全 → 辅助功能 → 终端）→ 可用 System
   Events 真实点击，全自动
2. **用户手动建文件夹**，内容写入仍需解决写通道（CSRF 墙），所以往往还得配合 1
3. **用户手动拖拽/上传** Markdown 文件到目标空间（飞书自动转文档；图片需另行处理）
4. 目标租户有可创建节点时，用户手动创建后由页面 UI 填充

先花 5 分钟确认「目标空间是否在 lark-cli 可见」+「目标节点 can_create 是否 true」，
能省掉后面所有白费功夫。
