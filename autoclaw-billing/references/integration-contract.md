# 集成契约

需要解析脚本输出、字段、payload 或错误处理时读取本文件。业务主链路优先使用内置 CLI；只有用户明确要求页面调试、检查登录态或排查页面/API 不一致时才考虑 browser。

## CLI 入口

运行任何 CLI 前先解析 Python 解释器。下面示例里的 `<PY>` 表示已解析出的解释器命令或完整路径，不是字面量。

- Windows PowerShell：优先用 `Get-Command python`，找不到再用 `Get-Command python3`。不要用 `where`，PowerShell 里 `where` 通常是 `Where-Object` 别名；若在 `cmd.exe` 中才用 `where python` / `where python3`。
- macOS/Linux shell：用 `command -v python3`，找不到再用 `command -v python`。
- 解析失败时停止并报告“未找到 Python 解释器”。
- Windows/PowerShell 中不要使用 `VAR=value command` 或 `cmd1 && cmd2`；如需设置环境变量，使用 `$env:VAR="value"; command`。
- 如果终端中文输出乱码，用全局参数 `--output <file>` 写出 UTF-8 JSON 文件，不要用 shell 重定向；`--output` 必须放在子命令前。

```bash
# 查询所有积分产品信息，包括月度会员和积分加油包；会员业务优先用 member-list，加油包只读 boost_list
<PY> "scripts/autoclaw_pay_cli.py" product-info

# 查询月度会员套餐，并过滤当前已订阅套餐；用于会员列表、会员订购前选品、当前订阅套餐详情
<PY> "scripts/autoclaw_pay_cli.py" member-list

# 查询订阅和权益生效状态；用于“会员是否生效”“订阅状态”“首月权益状态”
<PY> "scripts/autoclaw_pay_cli.py" subscribe-info

# 创建积分加油包一次性订单；product_id 必须来自当前轮新鲜 product-info.boost_list
<PY> "scripts/autoclaw_pay_cli.py" create-onetime --framework <framework> --session-id <session_id> --product-id <product_id>

# 创建月度会员订阅订单；product_id 必须来自当前轮新鲜 member-list.purchasable_member_list
<PY> "scripts/autoclaw_pay_cli.py" create-subscribe --source-id <source_id> --product-id <product_id>

# 同上；当 source_id 使用当前会话 id 时，可用 --session-id 作为别名
<PY> "scripts/autoclaw_pay_cli.py" create-subscribe --session-id <session_id> --product-id <product_id>

# 检查本地运行环境和支付上报依赖；不访问 AutoClaw API，不提交订单
<PY> "scripts/autoclaw_pay_cli.py" runtime-check

# 输出乱码时写 UTF-8 文件
<PY> "scripts/autoclaw_pay_cli.py" --output product-info.json product-info
```

| 命令 | 用途 | 关键返回/输入 |
|---|---|---|
| `product-info` | 查原始商品 | `member_list`、`boost_list` |
| `member-list` | 查会员并过滤当前已订阅套餐 | `current_member_list`、`purchasable_member_list`、`show_first_month_price` |
| `subscribe-info` | 查订阅和首月权益状态 | `subscribe_list`、`current_subscribe_list`、`alipay_first_month_rights`、`hit_first_month_exp` |
| `create-onetime` | 创建积分加油包订单 | `product_id` 必须来自新鲜 `boost_list`；必须传 `framework/session_id` |
| `create-subscribe` | 创建月度会员订阅 | `product_id` 必须来自新鲜 `member-list.purchasable_member_list`；必须传 `source_id` 或 `session_id` |
| `runtime-check` | 本地环境检查 | 不访问 AutoClaw API，不提交订单 |

正常业务不要求用户配置环境变量。查询和下单使用 CLI 参数、脚本默认值和本地 token 服务；本地 token 服务不可用时才显式传 `--token`。其他脚本是库、扩展层、payload 校验或依赖安装工具，不作为业务查询/下单入口。

## 商品和订阅字段

`product-info` 返回两个列表：月度会员对客查询/订购优先用 `member-list`；积分加油包只用 `boost_list`。不要跨列表匹配商品。

| 字段 | 处理方式 |
|---|---|
| `product_id` | 下单唯一可信 ID，原样使用 |
| `name` | 对客商品名 |
| `price_cent` / `price_yuan` | 价格；分/元 |
| `send_score_month` / `send_score_day` | 月度会员权益 |
| `monthly_total_score` | 月度会员总积分量；缺失写“未返回” |
| `send_score_forever` | 加油包基础积分 |
| `send_activity_score` | 活动赠送积分；没有或 0 不编造赠送 |
| `total_score` | `send_score_forever + send_activity_score`，用于展示/比较，不作下单 ID |
| `period_day` | 加油包有效期必须展示；缺失/空/非数值写“未返回”。可订购会员列表不要展示 |
| `available` | `false` 不能下单 |

`member-list` 关键字段：

| 字段 | 处理方式 |
|---|---|
| `current_member_list` | 当前已订阅月度会员；列表展示前先说明 |
| `current_member_list[].subscribe_status` | 订阅状态，原样展示 |
| `current_member_list[].subscribe_list[]` 有效期字段 | 仅接口返回时展示；不要用商品 `period_day` 补“未返回” |
| `purchasable_member_list` | 已移除当前订阅且 `available=true` 的可订购会员；列表和订购候选只用它 |
| `show_first_month_price` | 首月优惠总开关 |
| `display_price_yuan` / `display_price_kind` / `renewal_price_yuan` | 对客价格字段；只有 `display_price_kind=first_month` 才展示首月优惠 |

`subscribe-info` 关键字段：

| 字段 | 处理方式 |
|---|---|
| `subscribe_list` | 原始订阅列表；为空不编造套餐 |
| `current_subscribe_list` | 过滤取消/过期/失败后的当前订阅 |
| `current_subscribed_product_ids` | `member-list` 用于隐藏已订阅套餐 |
| `subscribe_status` | 原始状态值，非明确映射不自行解释 |
| `alipay_first_month_rights` / `hit_first_month_exp` | 首月权益状态，按布尔值报告 |
| `show_first_month_price` | 仅当 `hit_first_month_exp=true`、`subscribe_list` 为空、`alipay_first_month_rights=true` |
| `apple_subscribe_status` | 按整数状态码报告，不猜含义 |

订阅有效期字段名单：`period_day`、`valid_until`、`valid_to`、`expire_time`、`expire_at`、`end_time`、`next_billing_time`、`subscribe_end_time`。

## 商品匹配

按顺序匹配：完整 `product_id`、`name` 精确匹配、`name` 包含匹配、价格/积分量/最便宜/最高档计算候选。多个候选只问一个简短澄清问题；没有候选则展示对应可选列表。

新鲜列表指用户提出订购后在当前 assistant 轮次内拉取的列表，或用户同一轮提供且包含准确 ID 的列表响应。更早数据不得用于下单。

## 下单 Payload

月度会员：

```json
{
  "kind": "monthly_membership",
  "item_id": "<member product_id from fresh member-list.purchasable_member_list>",
  "source_id": "<source_id_or_session_id>",
  "quantity": 1,
  "idempotency_key": "<unique-request-key>"
}
```

积分加油包：

```json
{
  "kind": "credit_pack",
  "item_id": "<boost product_id from fresh boost_list>",
  "framework": "autoclaw",
  "session_id": "session_123",
  "quantity": 1,
  "idempotency_key": "<unique-request-key>"
}
```

`framework`、`session_id`、`source_id` 只能来自当前框架上下文、调用方显式参数或会话探测结果；不要由模型生成或猜测。

## 支付接管和错误

`create-onetime` 标准化返回如果包含非空 `alipayMetadata.orderStr`，表示支付宝待支付订单参数，不是支付成功。立即调用 `alipay-payment-skill`，把完整原始 `alipayMetadata["orderStr"]` 作为 `cashier_url`；不要展示、改写、截断、转码或转换成 `excashier`。

| 情况 | 必需行为 |
|---|---|
| 列表为空 | 说明未返回可购买商品，不提供猜测项 |
| 商品不可用 | 说明不可购买，必要时重新拉取并展示可用替代 |
| 确认后价格变化 | 停止下单，用新价格重新确认 |
| 下单待支付/处理中 | 如实说明当前仍未完成 |
| 重复请求/idempotency 冲突 | 报告接口已有订单/状态；否则询问是否重试 |
| 缺少配置或 token 服务不可用 | 报告失败原因，等待配置/授权；不要模拟成功 |
| 查询当前套餐详情 | 用 `member-list.current_member_list` |
| 查询订阅/权益是否生效 | 用 `subscribe-info`，不要用支付状态推断 |
