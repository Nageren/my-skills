# 云效知识库（Thoughts）→ 飞书知识库迁移

当用户给出 thoughts.aliyun.com 的 workspace/folder 链接并要求把内容搬到飞书时使用。

## 云效侧（Source）

- **无公开访问**：未登录访问直接 302 到 `account.aliyun.com/login`，curl 也拿不到内容（只能拿到登录跳转）。不要浪费时间尝试抓取，直接走「用户本地登录 + 导出」路线。
- 引导用户：登录后打开链接 → 先看文件夹里有哪几篇文档（让用户报标题清单，用于规划飞书侧目录结构）→ 每篇打开 → 右上角「···」→ **导出** → 选 **Markdown**（保真最高，图片/表格/代码块都带）→ 下载到 `~/Downloads`。
- 没有 Markdown 选项时选 **Word**，可本地提取（docx 可被 read_file 自动提取）。
- 导出菜单具体位置以用户实际界面为准（阿里云官方帮助文档路径经常 404，别依赖查文档）。

## 飞书侧（Destination）

1. **创建知识空间**（必须 user 身份，bot 会被拒）：
   ```bash
   lark-cli wiki +space-create --name <空间名> [--description <描述>] --as user
   ```
   返回 `space_id`（create API 不返回 URL）。
2. **按目录结构建节点**：
   ```bash
   lark-cli wiki +node-create --space-id <SPACE_ID> --title <标题>            # 顶层节点
   lark-cli wiki +node-create --parent-node-token <PARENT_NODE_TOKEN> --title <子标题>  # 子节点
   ```
   返回 `node_token` / `obj_token`。
3. **导入文档内容**（Markdown 文件 → 飞书文档，节点即父容器）：
   ```bash
   lark-cli docs +create --api-version v2 --doc-format markdown \
     --parent-token <node_token> --content "$(cat /path/to/file.md)"
   ```
   长文档先只建标题+骨架，正文用 `docs +update --command append` 分段追加，避免超长 content 触发参数限制。

## lark-cli user 身份过期（设备流重新授权）

创建 wiki 空间等用户资源操作依赖 user 身份，常遇到 refresh token 过期：

1. **先查状态**：`lark-cli auth status` — 看到 `"User identity: missing (refresh token expired)"` 即 user 身份过期（bot 可能仍 ready）。**别等写操作报错才排查身份**。
2. **发起授权**（一次性，别缓存 device_code，下次授权重新生成；有效期 600s）：
   ```bash
   lark-cli auth login --no-wait --json --domain all
   # 返回 verification_url + device_code
   ```
3. **生成二维码**：`lark-cli auth qrcode "<verification_url>" --output qr.png`
   ⚠️ **实测坑：`--output` 只接受当前目录下的相对路径**，绝对路径（如 `/tmp/qr.png`）报 `validation/invalid_argument`。先 `cd` 到目标目录再生成。
4. **给用户**：先给 verification_url，再给二维码文件/图片；用户授权后执行：
   ```bash
   lark-cli auth login --device-code <device_code>
   ```

### 设备码过期 / 用户迟迟不授权（实测高频坑）

- 设备码**有效期仅 600s（10 分钟）**，过期后 `--device-code` 报 `authorization failed: The device_code is invalid. Please restart the device authorization flow.`。`expires_in` 字段在 `--no-wait` 返回里有。
- **把 `lark-cli auth login --device-code <code>` 放后台跑**（terminal background=true + notify_on_complete），不要前台阻塞等用户；授权完成后会收到进程完成通知。
- **判断授权是否成功用 `lark-cli auth status`**（user identity 从 `missing` 变 `ready`）。不要读后台进程的输出文件——旧进程可能因过期失败退出，残留的输出是过期报错，会误导判断（实测因此误判 2 次）。
- 过期后**不要复用旧 device_code**：每次重新 `lark-cli auth login --no-wait --json` 生成全新链接+码，并用 `lark-cli auth qrcode` 重新生成二维码（`MEDIA:<path>` 直接展示）。
- 用户没及时操作时主动重发新链接（旧链接在用户手里可能已过期打不开），别干等旧进程自然超时；每次提醒都带上验证码和二维码。

## 流程要点

- 用户身份未授权时先处理授权，再执行任何 wiki 写操作。
- 迁移前先拿到云效侧文档清单，和用户确认飞书侧知识空间名与目录结构再动手。
