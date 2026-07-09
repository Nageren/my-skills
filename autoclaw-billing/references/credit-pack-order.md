# 订购积分加油包

用于订购 AutoClaw/智谱积分加油包、积分包、点数包、额度包或充值档位。若用户问“积分怎么买/怎么买积分/都可以怎么买积分/积分怎么充值/有哪些购买方式”，先走获取方式咨询，同时说明会员和加油包。

## 流程

1. 获取当前 `framework` 和 `session_id`；任一缺失则要求调用方提供，不准备下单。
2. 运行新鲜列表：
   ```bash
   <PY> "scripts/autoclaw_pay_cli.py" product-info
   ```
3. 只从 `boost_list` 匹配候选；候选 `available=false` 时停止。
4. 候选唯一后，读取选定语言模板的“积分加油包下单确认”。用户显式确认前不得下单。
5. 确认后运行：
   ```bash
   <PY> "scripts/autoclaw_pay_cli.py" create-onetime --framework <framework> --session-id <session_id> --product-id <boost_product_id>
   ```
6. 如果返回非空 `alipayMetadata.orderStr`，立即交给 `alipay-payment-skill`，不要输出普通订单结果。

## 匹配和确认

- 支持完整 `product_id`、商品名精确/包含、青铜等部分名称、基础积分、总积分、最便宜、最多积分/最高档。
- “点数/额度/credits”在 AutoClaw/智谱上下文中等价于积分数量。
- 基础积分用 `send_score_forever`，总积分用 `total_score`；产生不同候选时先让用户选择。
- 多候选：只问一个澄清问题，列名称、ID、积分、价格。
- 没指定档位但明确“帮我买/给我充值/我要买”：展示可购买加油包并让用户选择。
- 确认模板默认不展示 `product_id`、价格、`framework`、`session_id`，除非用户明确要求。

## 失败处理

| 情况 | 处理 |
|---|---|
| 没有匹配商品 | 展示当前可购买加油包并请用户选择 |
| “青铜包”等名称不存在 | 不编造，展示当前可购买加油包 |
| 确认后价格变化 | 停止下单，用新价格重新确认 |
| API 返回处理中 | 如实报告状态和预计到账信息 |
| 脚本失败 | 报告错误；只有用户要求页面调试时才考虑 browser |
