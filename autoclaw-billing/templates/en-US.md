# English Response Templates

Read only for English output. Every ```text block is customer-facing formatting: preserve line breaks, blank lines, tables, and bullets; replace placeholders only.

## Monthly Membership List

Data source: `member-list`. If `current_member_list` is non-empty, show it before the table. The table uses only `purchasable_member_list`. Use `display_price_yuan`; only `display_price_kind=first_month` may show and bold a first-month discount. Do not show validity/period for purchasable monthly plans.

```text
Current monthly membership:
- <current_member_name> (status: <subscribe_status>)

Current monthly membership plans:

| Name | Price | First-month discount | Renewal | Key benefits |
|---|---:|---:|---|---|
| **...** | ... | **...** | ... | Monthly credits: ...; daily credits: ...; total monthly credits: **...** |
```

If `current_member_list` is empty, omit the current-membership section. If `purchasable_member_list` is empty, replace the table with:

```text
There are no other purchasable monthly membership plans right now.
```

## Credit Top-Up Pack List

Data source: `boost_list`. Missing validity is `Not returned`; `available=true` is `Available`, `false` is `Unavailable`.

```text
Current credit top-up packs:

| Name | Credits | Bonus | Price | Validity | Status |
|---|---:|---:|---:|---|---|
| ... | ... | ... | ... | ... | ... |
```

## Current Subscription Plan Details

Data source: `member-list.current_member_list`. If empty, only say `You do not currently have an active monthly membership subscription.` Insert `- Validity: <value>` after price only when the subscription info returns a validity field.

```text
Current monthly membership:

- Plan: <name>
- Status: <subscribe_status>
- Price: ¥<display_price_yuan or price_yuan>/month
- Monthly credits: <send_score_month or Not returned>
- Daily credits: <send_score_day or Not returned>
- Total monthly credits: <monthly_total_score or send_score_month + send_score_day * 30 or Not returned>
```

## AutoClaw Acquisition Methods

Use for questions about how to get, buy, purchase, or top up AutoClaw credits, points, quota, or benefits as available methods. Always recommend both membership plans and top-up packs. Do not place an order proactively.

```text
You can get AutoClaw credits/benefits in two ways:

1. Monthly membership plans
Best for steady, ongoing usage. You can receive membership benefits and credits on a monthly basis.

2. Credit top-up packs
Best for temporary credit replenishment or high-frequency usage. They are more flexible for one-time credit needs.

I can also query the current monthly membership plans and credit top-up packs if you want to compare prices and options.
```

## Monthly Membership Order Confirmation

Data source: fresh `member-list.purchasable_member_list`. Use the first-month version only when `show_first_month_price=true` and the item has `display_price_kind=first_month`; otherwise use the regular version.

### First-Month Price Version

```text
I selected the monthly membership plan: <name>

First month: ¥<display_price_yuan>
Renews at: ¥<renewal_price_yuan>/month

Best for steady usage, with daily credits and ongoing membership benefits.

Benefits:
- Monthly credits: <send_score_month>
- Daily credits: <send_score_day>
- Total monthly credits: <monthly_total_score or send_score_month + send_score_day * 30>
- Daily login credits included

Notes:
- Membership service is a virtual product and cannot be refunded after payment.
- By subscribing, you authorize AutoClaw to charge you under the subscription terms until you cancel.
- Payment means you agree to the AutoClaw credit top-up service agreement.

Reply "confirm order" and I will submit the order.
```

### Regular Price Version

```text
I selected the monthly membership plan: <name>

Recurring price: ¥<display_price_yuan>/month

Best for steady usage, with daily credits and ongoing membership benefits.

Benefits:
- Monthly credits: <send_score_month>
- Daily credits: <send_score_day>
- Total monthly credits: <monthly_total_score or send_score_month + send_score_day * 30>
- Daily login credits included

Notes:
- Membership service is a virtual product and cannot be refunded after payment.
- By subscribing, you authorize AutoClaw to charge you under the subscription terms until you cancel.
- Payment means you agree to the AutoClaw credit top-up service agreement.

Reply "confirm order" and I will submit the order.
```

## Credit Top-Up Pack Order Confirmation

Data source: fresh `boost_list`. Omit `<description>` when missing. Credits use `total_score` first, then `send_score_forever`; validity missing is `Not returned`. Do not show `product_id`, `framework`, or `session_id` unless requested.

```text
I selected the credit top-up pack: <name>
[<description>]

Credits: <credits>
Validity: <period_day days or Not returned>

Notes:
- Credit top-up service is a virtual product and cannot be refunded after payment.
- Payment means you agree to the AutoClaw credit top-up service agreement.

Reply "confirm order" and I will submit the order.
```

## Monthly Membership Cancellation

```text
To cancel your monthly membership subscription, open the mobile Alipay app:

Alipay app - Me - Payment Settings - Auto Debit/Password-free Payment, then find the AutoClaw monthly membership subscription and follow the page instructions to cancel it.
```

## Missing Data Source

```text
I do not have an available AutoClaw data source yet, so I cannot query real plans or packs. Please restart the application and try again later, thank you.
```

## Order Result

```text
Order result:
- Order ID: <order_id>
- Status: <status>
- Item: <item_name>
- Amount: <amount> <currency>
- Next action: <next_action>
- Link: <payment_or_receipt_url>
```

If `payment_markdown` is returned, append it exactly. If `alipayMetadata.orderStr` is returned, do not output the ordinary result; immediately pass it to `alipay-payment-skill`.

## Existing Membership Status

```text
Current subscription status:

<subscribe_status_summary>
```

## Status Labels

| Raw status | English |
|---|---|
| `paid` | Paid |
| `pending_payment` | Pending payment |
| `processing` | Processing |
| `failed` | Failed |
| `canceled` | Canceled |
| `available: true` | Available |
| `available: false` | Unavailable |

Keep unlisted statuses as raw values.
