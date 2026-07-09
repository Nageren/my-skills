# 中文回复模板

仅中文输出时读取。所有 ```text 代码块都是对客格式：保留换行、空行、表格和项目符号，只替换占位符。

## 查询月度会员套餐

数据源：`member-list`。若 `current_member_list` 非空，先展示当前已订阅套餐；可订购表格只展示 `purchasable_member_list`。价格用 `display_price_yuan`；只有 `display_price_kind=first_month` 时展示并加粗首月优惠，否则写 `-`。可订购会员列表不要展示有效期/周期。

```text
当前已订阅月度会员：
- <current_member_name>（状态：<subscribe_status>）

您可以选购如下月度会员套餐：

| 名称 | 价格 | 首月优惠 | 续费 | 主要权益 |
|---|---:|---:|---|---|
| **...** | ... | **...** | ... | 月积分：...；日积分：...；总积分量：**...** |
```

若 `current_member_list` 为空，省略“当前已订阅月度会员”段落，不输出空订阅提示。若 `purchasable_member_list` 为空，表格改为：

```text
当前暂无其他可订购月度会员套餐。
```

## 查询积分加油包

数据源：`boost_list`。有效期缺失写“未返回”；`available=true` 写“可购买”，`false` 写“暂时缺货”或“不可购买”。

```text
您可以选购如下积分加油包：

| 名称 | 积分 | 赠送 | 价格 | 有效期 | 状态 |
|---|---:|---:|---:|---|---|
| ... | ... | ... | ... | ... | ... |
```

## 当前订阅套餐详情

数据源：`member-list.current_member_list`。为空时只输出“当前没有已订阅的月度会员套餐。”只有订阅信息返回有效期字段时，才在价格后插入 `- 有效期：<对应值>`。

```text
当前已订阅月度会员：

- 套餐：<name>
- 状态：<subscribe_status>
- 价格：¥<display_price_yuan 或 price_yuan>/月
- 月积分：<send_score_month 或 未返回>
- 日积分：<send_score_day 或 未返回>
- 总积分量：<monthly_total_score 或 send_score_month + send_score_day * 30 或 未返回>
```

## AutoClaw 获取方式

用于询问积分/点数/额度/权益怎么获取、怎么买、怎么充值、有哪些购买方式。必须同时推荐会员和加油包，不主动下单，不追加模板外获取方式。

```text
AutoClaw 积分/权益可以通过两种方式获取：

1. 月度会员套餐
适合有稳定使用需求的用户，可以按月获得会员权益和积分，使用更持续。

2. 积分加油包
适合临时补充积分或高频使用场景，一次性补充更灵活。

如果你想看具体价格和档位，我可以继续为你查询当前月度会员套餐和积分加油包。
```

## 月度会员订阅确认

数据源：新鲜 `member-list.purchasable_member_list`。只在 `show_first_month_price=true` 且候选 `display_price_kind=first_month` 时用首月优惠版；否则用常规价版。未返回月/日积分写“未返回”；总积分优先 `monthly_total_score`。

### 首月优惠版

```text
已为你选择月度会员权益【<name>】

首月优惠价：¥<display_price_yuan>/首月
次月起续订价：¥<renewal_price_yuan 或 price_yuan>/月

适合有稳定使用需求的用户，每日可领取积分，使用更持续。

权益：
- 月积分：<send_score_month>积分
- 日积分：<send_score_day>积分
- 总积分量：<monthly_total_score 或 send_score_month + send_score_day * 30>积分/月
- 每日登录即送

提示：
- 会员服务属于虚拟商品，一经支付无法退款，请您理解
- 订阅即表示您授权 AutoClaw 根据条款向您收费，直至您取消订阅
- 支付即代表你同意 AutoClaw 积分充值服务协议

回复“确认订购”后我再提交订单。
```

### 常规价版

```text
已为你选择月度会员权益【<name>】

续订价格：¥<display_price_yuan>/月

适合有稳定使用需求的用户，每日可领取积分，使用更持续。

权益：
- 月积分：<send_score_month>积分
- 日积分：<send_score_day>积分
- 总积分量：<monthly_total_score 或 send_score_month + send_score_day * 30>积分/月
- 每日登录即送

提示：
- 会员服务属于虚拟商品，一经支付无法退款，请您理解
- 订阅即表示您授权 AutoClaw 根据条款向您收费，直至您取消订阅
- 支付即代表你同意 AutoClaw 积分充值服务协议

回复“确认订购”后我再提交订单。
```

## 月度会员取消订阅

```text
你可以在移动端支付宝取消月度会员订阅：

打开支付宝 APP - 我的 - 支付设置 - 自动续费/免密支付，找到 AutoClaw 月度会员订阅后按页面提示关闭。
```

## 月度会员订阅支付

`create-subscribe` 成功返回二维码后，在 `payment_markdown` 前追加：

```text
支付宝扫码支付¥<pay_amount_yuan>
```

然后原样追加接口返回的 `payment_markdown`。

## 积分加油包下单确认

数据源：新鲜 `boost_list`。`<description>` 缺失则省略该行；`<credits>` 优先 `total_score`，否则 `send_score_forever`；有效期缺失写“未返回”。默认不展示 `product_id`、价格、`framework`、`session_id`。

```text
已为你选择加油包【<name>】
[<description>]

积分：<credits>积分
有效期：<period_day 天 或 未返回>

提示：
- 积分充值服务属于虚拟商品，一经支付无法退款，请您理解
- 支付即代表你同意 AutoClaw 积分充值服务协议

回复“确认订购”后我再提交订单。
```

## 缺少数据源

```text
抱歉，获取当前登录账号失败，无法查询真实套餐或加油包，请确认您的AutoClaw账号已登录。若您已登录，请重启AutoClaw应用后稍后重试，谢谢
```

## 下单结果

```text
订单结果：
- 订单 ID：<order_id>
- 状态：<status>
- 商品：<item_name>
- 金额：<amount> <currency>
- 链接：<payment_or_receipt_url>
```

如果返回 `payment_markdown`，原样追加；如果返回 `alipayMetadata.orderStr`，不要输出普通结果，立即交给 `alipay-payment-skill`。

## 查询已有会员状态

```text
当前订阅状态：

<subscribe_status_summary>
```

## 状态文案

| 原始状态 | 中文 |
|---|---|
| `paid` | 已支付 |
| `pending_payment` | 待支付 |
| `processing` | 处理中 |
| `failed` | 失败 |
| `canceled` | 已取消 |
| `available: true` | 可购买 |
| `available: false` | 不可购买 |

未列出的状态保留原值。
