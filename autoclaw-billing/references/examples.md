# 执行示例

仅在路由、确认或失败处理不清楚时读取。本文件是回归用例，不替代链路 reference 和模板。

## 1. 查询月度会员

User: `都有哪些会员套餐`

同类：`会员多少钱`、`月卡多少钱`、`首月优惠有吗`、`会员每天送多少积分`。

预期：
1. 读 `monthly-membership-list.md` 和模板。
2. 运行 `member-list`。
3. `current_member_list` 非空才展示当前订阅；为空不输出空订阅提示。
4. 表格只展示 `purchasable_member_list`，不展示有效期/周期，不下单。

## 2. 获取/购买方式咨询

User: `都可以怎么买积分？`

同类：`积分怎么获取`、`积分怎么买`、`怎么买积分`、`积分怎么充值`、`有哪些购买方式`、`额度不够怎么办`。

预期：
1. 读选定语言模板。
2. 使用“AutoClaw 获取方式”模板。
3. 同时推荐月度会员套餐和积分加油包两个途径。
4. 不查询列表，不下单；用户要求具体价格/档位时再查询。
5. 不补充注册赠送、官方活动、开发者计划等模板外途径。

## 3. 订购月度会员

User: `帮我开个会员`

预期：
1. 读 `monthly-membership-order.md` 和模板。
2. 获取 `source_id/session_id`，运行 `member-list`。
3. 未指定档位时展示 `purchasable_member_list` 让用户选择。
4. 指定档位时只从 `purchasable_member_list` 匹配。
5. 使用月度会员订阅确认模板；用户确认后才 `create-subscribe`。

## 4. 取消订阅

User: `关闭自动续费`

预期：
1. 读 `monthly-membership-cancel.md` 和模板。
2. 不调用下单接口，不声称已代取消。
3. 引导移动端支付宝：我的 - 支付设置 - 自动续费/免密支付。

## 5. 当前订阅详情/状态

User: `我现在是什么会员`

预期：
1. 运行 `member-list`，用 `current_member_list` 展示套餐、状态、价格、月积分、日积分、总积分量。
2. 只有接口返回订阅有效期字段时展示有效期。
3. `current_member_list` 为空只说明当前没有已订阅月度会员套餐。

User: `会员是否已生效`

预期：运行 `subscribe-info`，按接口返回报告；不要用支付状态或下单结果推断。

## 6. 查询积分加油包

User: `有哪些积分包？`

预期：
1. 读 `credit-pack-list.md` 和模板。
2. 运行 `product-info`，只读 `boost_list`。
3. 展示名称、积分、赠送、价格、有效期、状态。

## 7. 订购积分加油包

User: `给我买1000积分`

同类：`帮我买积分`、`给我充值`、`买青铜包`、`加 1000 点数`。

预期：
1. 读 `credit-pack-order.md` 和模板。
2. 获取 `framework/session_id`，运行 `product-info`。
3. 只从 `boost_list` 匹配；多候选让用户选择。
4. 使用积分加油包下单确认模板；用户确认后才 `create-onetime`。
5. 返回 `alipayMetadata.orderStr` 时立即交给 `alipay-payment-skill`。

## 8. 触发边界

User: `信用卡积分怎么兑换？`

预期：没有 AutoClaw 或智谱积分上下文时不触发本 skill。
