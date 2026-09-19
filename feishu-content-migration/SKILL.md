---
name: feishu-content-migration
description: "把外部知识库内容（云效 thoughts、企业微信文档等）迁移到飞书文档/Wiki 时使用。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 外部内容迁移到飞书（Feishu Content Migration）

当用户给出来自飞书以外的知识库链接（云效 thoughts.aliyun.com、企业微信文档 doc.weixin.qq.com 等）并要求"放到飞书"时使用。飞书侧的落点可能是云文档（`lark-doc`）或知识库 Wiki（`lark-wiki`）。

## 通用流程

1. **确认源端可访问性**：外部知识库通常需要登录。先用 curl 探测（`curl -s -o /dev/null -w "%{http_code}" <url>`），若 302 到登录页说明无公开访问，**不要反复尝试抓取**，直接引导用户本地操作。
2. **让用户导出源内容**：引导用户在本地登录后导出（Markdown 优先，Word 次之），文件通常落在 `~/Downloads`。导出前先让用户报文档清单（标题/数量），用于规划飞书侧目录结构。
3. **准备飞书侧容器**（目标为 Wiki 时）：
   ```bash
   lark-cli wiki +space-create --name <空间名> [--description <描述>] --as user   # 仅 user 身份
   lark-cli wiki +node-create --space-id <SPACE_ID> --title <标题>                 # 顶层节点
   lark-cli wiki +node-create --parent-node-token <PARENT> --title <子标题>        # 子节点
   ```
4. **导入内容**（本地 Markdown 文件 → 飞书文档，**实测最可靠**）：
   ```bash
   # ✅ stdin 管道：大文件/中文/特殊字符都安全
   cat /path/to/file.md | lark-cli docs +update --api-version v2 --doc <OBJ_TOKEN> \
     --command overwrite --doc-format markdown --content - --as user
   ```
   > 坑：`--content-file` 参数不存在；`--content @绝对路径` 报错（必须相对路径）。`--doc` 用 docx obj_token（`wiki +node-get` 返回，注意 obj_token 在 data **顶层**）。飞书导入时会**自动转存网络图片**为内部 file token，无需手动上传。
   
   也可用 `docs +create --api-version v2 --doc-format markdown --content ...` 直接建文档；长文档先建标题+骨架，正文用 `docs +update --command append` 分段追加。

## 排版修复与增强（迁移后必做）

导入的 Markdown 常带源平台残留（云效的 `Plain Text`、零宽字符、段落内 `<br/>` 堆叠）且代码块无语言标注。完整经验（扫描/修复/增强脚本逻辑、飞书 API 忽略的样式属性）见 [`references/feishu-import-polish.md`](references/feishu-import-polish.md)。要点：
- 排版扫描**先替换 table/pre 为占位**再统计主体段落，否则表格单元格误报
- Plain Text 残留 → 删除（含 `(?:<br/>\s*)+</code>` 清理、零宽字符）
- 段落 br 按行特征转换：全数字前缀→`<ol>`、短行→`<ul>`、长行→拆 `<p>`
- 代码块自动检测语言加 `lang` 属性（sql/java/json/yaml/text）→ 飞书渲染语法高亮
- ⚠️ **飞书 API 忽略 `<th background-color>` 和 `<img width>`**（写入成功但被丢弃）；表头灰底/图片等比缩放是渲染端默认行为，XML 层无法控制
- 写回前先 fetch 备份 `backup_all.json`（obj_token → content），可回滚

## 授权前置（必查）

创建 Wiki 空间、文档写操作依赖 **user 身份**，而 user refresh token 会过期（bot 可能仍 ready）。执行前先 `lark-cli auth status`，看到 `"User identity: missing (refresh token expired)"` 就先走设备流重新授权（见 references），**别等写操作报权限错误才排查身份**。

## References

- [`references/yunxiao-kb-to-feishu.md`](references/yunxiao-kb-to-feishu.md) — 云效知识库→飞书迁移的完整分步：云效导出入口、飞书侧导入命令、lark-cli 设备流重新授权三步流程、二维码 `--output` 相对路径坑
- [`references/feishu-import-polish.md`](references/feishu-import-polish.md) — 飞书侧批量导入 + 排版修复/增强实战：overwrite stdin 导入、节点删除 URL 形式、图片自动转存、Plain Text/br/代码高亮处理、飞书 API 忽略的样式属性

## 相关技能

- 飞书知识库管理（建空间/节点/成员）：`lark-wiki`
- 飞书文档读写/创建：`lark-doc`
- lark-cli 认证与权限排障：`lark-shared`
