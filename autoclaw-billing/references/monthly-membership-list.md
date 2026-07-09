# 查询月度会员套餐

用于查看 AutoClaw 月度会员、月卡、首月优惠、会员价格或权益。

## 流程

1. 运行：
   ```bash
   <PY> "scripts/autoclaw_pay_cli.py" member-list
   ```
2. 读取 `current_member_list`、`purchasable_member_list`、`show_first_month_price`。
3. 输出前读取选定语言模板的会员列表模板。

## 展示规则

- `current_member_list` 非空：先展示当前已订阅套餐名称和 `subscribe_status`；只有订阅信息返回有效期字段时才追加有效期。
- `current_member_list` 为空：不要输出“暂无订阅/没有订购”等空订阅提示，直接展示可订购表格。
- 可订购表格只展示 `purchasable_member_list`，不要展示当前已订阅套餐，不展示有效期/周期。
- 价格用 `display_price_yuan`；只有 `show_first_month_price=true` 且条目 `display_price_kind=first_month` 时展示首月优惠。
- 套餐名称、首月优惠、总积分量加粗；无首月优惠写 `-` 且不加粗。
- `monthly_total_score` 缺失时，如月积分和日积分均为数值，按 `send_score_month + send_score_day * 30`；否则写“未返回”。
- `purchasable_member_list` 为空时，只说明当前暂无其他可订购月度会员套餐。

不要主动下单；用户要求订购后转 `monthly-membership-order.md`。
