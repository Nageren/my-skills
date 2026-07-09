# 订购月度会员套餐

用于开通、购买、续费 AutoClaw 月度会员、月卡或连续包月。

## 流程

1. 获取 `source_id`；没有时可用当前会话 `session_id`。两者都没有则先要求调用方提供。
2. 运行新鲜列表：
   ```bash
   <PY> "scripts/autoclaw_pay_cli.py" member-list
   ```
3. 只从 `purchasable_member_list` 匹配候选，不从 `current_member_list`、`member_list` 或 `boost_list` 下单。
4. 如 `current_member_list` 非空，先告知当前已订阅套餐；这些套餐不能再次作为候选。
5. 候选唯一后，读取选定语言模板的“月度会员订阅确认”。用户显式确认前不得下单。
6. 确认后运行：
   ```bash
   <PY> "scripts/autoclaw_pay_cli.py" create-subscribe --source-id <source_id> --product-id <member_product_id>
   ```
7. 返回 `payment_markdown` 时原样追加；中文场景先输出 `支付宝扫码支付¥<pay_amount_yuan>`。

## 匹配和确认

- 支持完整 `product_id`、商品名精确/包含、最便宜、最高档/旗舰。
- 多候选：只问一个澄清问题，列名称、ID、价格。
- 没指定档位：展示可订购套餐并让用户选择，不判定失败。
- 价格/首月优惠只用 `display_price_yuan`、`display_price_kind`、`renewal_price_yuan`；`first_month_price_yuan=0.00` 不算优惠。
- 确认模板不得额外展示账号、商品 ID、有效期/周期、续费方式，除非用户明确要求。

## 失败处理

| 情况 | 处理 |
|---|---|
| 当前已订阅该套餐 | 停止下单，说明已订阅并展示其他可订购套餐 |
| 确认后价格变化 | 停止下单，用新价格重新确认 |
| API 返回已订阅/重复订阅 | 报告接口原始提示，不推断权益状态 |
| 脚本失败 | 报告错误；只有用户要求页面调试时才考虑 browser |
