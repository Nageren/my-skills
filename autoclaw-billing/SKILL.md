---
name: autoclaw-billing
description: AutoClaw 计费与权益技能，用于处理智谱积分/额度、会员/月卡、连续包月和积分加油包相关问题。支持查询积分获取或购买方式、会员套餐/价格/权益/首月优惠、当前订阅/有效期/生效状态，开通/续费/取消会员，关闭自动续费或免密支付，查询或购买积分加油包。用户询问“积分怎么买、怎么充值、额度不够怎么办、会员多少钱、有哪些会员、有哪些积分包、买青铜包”等购买/查询意图时可直接使用本技能；最近对话已在 AutoClaw/智谱积分业务中时，也可继承“积分、会员、到期了吗、取消自动续费”等省略说法。不要处理无关平台的信用卡积分、电商会员、普通支付宝支付或泛化充值问题。
version: "1.0.0"
metadata: {"openclaw":{"requires":{"env":[],"bins":["python"],"tags":["积分","订阅","续费","加油包", "积分包", "退订", "autoclaw","billing","membership","credits"]},"category":"billing"}}
---

# AutoClaw 会员与积分订购

## 快速路由

先判定意图，再读取对应 reference 和选定语言模板。列表、确认、取消、状态、订单结果都必须按 `templates/<locale>.md` 输出，不要凭字段清单自行拼文案。

用户说法只用于选择入口，不替代执行文件。进入后必须按意图读取下表文件；没有读取对应 reference 和模板，不得查询、下单、确认或输出最终文案。

问“怎么买/怎么充值/有哪些购买方式/购买积分”是获取方式咨询，只输出月度会员套餐和积分加油包两个购买途径，并展示两种商品列表并进行推荐，不进入下单。只有用户明确说“帮我买加油包/买xx包”等购买动作，才进入加油包订购。

| 意图 | 典型说法 | 必读 |
|---|---|---|
| 查询月度会员套餐 | 会员多少钱、有哪些会员、首月优惠有吗、月卡多少钱 | `references/monthly-membership-list.md` + `templates/<locale>.md` |
| 咨询获取/购买方式 | 积分怎么获取、积分怎么买、都可以怎么买积分、积分怎么充值、额度不够怎么办 | `templates/<locale>.md` 的“AutoClaw 获取方式” |
| 查询当前套餐/订阅详情 | 我现在是什么会员、当前订阅套餐详情、会员有效期、已订阅套餐有什么权益 | `references/integration-contract.md` + `templates/<locale>.md` |
| 查询订阅/权益状态 | 订阅状态、会员是否已生效、首月权益状态 | `references/integration-contract.md` + `templates/<locale>.md` |
| 订购月度会员 | 开会员、买会员、续费会员、订个月卡、开连续包月 | `references/monthly-membership-order.md` + `templates/<locale>.md` |
| 取消月度会员 | 取消订阅、关闭自动续费、关闭免密支付、取消连续包月 | `references/monthly-membership-cancel.md` + `templates/<locale>.md` |
| 查询积分加油包 | 有哪些积分包、积分充值档位、积分包价格、补充额度、临时加积分、额度包多少钱 | `references/credit-pack-list.md` + `templates/<locale>.md` |
| 订购积分加油包 | 买 1000 积分、帮我买积分、给我充值、买青铜包 | `references/credit-pack-order.md` + `templates/<locale>.md` |

## 全局硬约束

- 使用 AutoClaw 实时数据源；不得编造套餐、加油包、价格、库存、折扣、权益或获取途径。
- 每个链路先读对应 reference 和一个语言模板；中文默认读 `templates/zh-CN.md`，英文请求读 `templates/en-US.md`。
- 模板代码块里的换行、空行、表格和项目符号是对客格式要求，只替换占位符，不压缩成单段。
- 下单前必须从当前轮新鲜列表定位真实 `product_id`，并先输出专用确认模板；用户显式确认后才调用下单接口。
- 月度会员查询/订购用 `member-list` 和 `purchasable_member_list`；当前已订阅套餐来自 `current_member_list`，不得重复下单。
- 订阅详情用 `member-list.current_member_list`；订阅/权益生效状态用 `subscribe-info`。不要用支付状态、商品列表或下单结果推断会员权益。
- 已订阅会员只有接口返回订阅有效期字段时才展示有效期；可订购月度会员列表不要展示有效期/周期。
- 首月优惠只看 `member-list.show_first_month_price=true` 且条目 `display_price_kind=first_month`；`first_month_price_yuan=0.00`、空或未返回都按常规价。
- 积分加油包只看 `product-info.boost_list`；有效期缺失写“未返回”，不要猜测。
- 取消订阅只引导用户在移动端支付宝关闭自动续费/免密支付；不要调用下单接口，不要声称已代取消。
- 正常业务链路必须按照规定流程调用脚本
- 全局输出必须使用UTF-8编码

## 主命令

本 skill 业务主链路统一调用 `scripts/autoclaw_pay_cli.py`。字段、schema、错误处理和脚本职责见 `references/integration-contract.md`。

运行主命令前先解析 Python 解释器。下面示例里的 `<PY>` 表示已解析出的解释器命令或完整路径，不是字面量。

- Windows PowerShell：优先用 `Get-Command python`，找不到再用 `Get-Command python3`。不要用 `where`，PowerShell 里 `where` 通常是 `Where-Object` 别名；若在 `cmd.exe` 中才用 `where python` / `where python3`。
- macOS/Linux shell：用 `command -v python3`，找不到再用 `command -v python`。
- 解析失败时停止并报告“未找到 Python 解释器”。
- Windows/PowerShell 中不要使用 `VAR=value command` 或 `cmd1 && cmd2` 这类 POSIX shell 写法；如需设置环境变量，使用 `$env:VAR="value"; command`。
- 如果终端中文输出乱码，用全局参数 `--output <file>` 写出 UTF-8 JSON 文件后再读取，`--output` 必须放在子命令前。

```bash
# 查询所有积分产品信息，包括月度会员和积分加油包；会员业务优先用 member-list，加油包只读 boost_list
<PY> "scripts/autoclaw_pay_cli.py" product-info

# 查询月度会员套餐，并过滤当前已订阅套餐；用于会员列表、会员订购前选品、当前订阅套餐详情
<PY> "scripts/autoclaw_pay_cli.py" member-list

# 查询订阅和权益生效状态；用于“会员是否生效”“订阅状态”“首月权益状态”
<PY> "scripts/autoclaw_pay_cli.py" subscribe-info

# 创建积分加油包一次性订单；product_id 必须来自当前轮新鲜 product-info.boost_list
<PY> "scripts/autoclaw_pay_cli.py" create-onetime --framework <framework> --session-id <session_id> --product-id <boost_product_id>

# 创建月度会员订阅订单；product_id 必须来自当前轮新鲜 member-list.purchasable_member_list
<PY> "scripts/autoclaw_pay_cli.py" create-subscribe --source-id <source_id> --product-id <member_product_id>

# 同上；当 source_id 使用当前会话 id 时，可用 --session-id 作为别名
<PY> "scripts/autoclaw_pay_cli.py" create-subscribe --session-id <session_id> --product-id <member_product_id>

# 检查本地运行环境和支付上报依赖；不访问 AutoClaw API，不提交订单
<PY> "scripts/autoclaw_pay_cli.py" runtime-check

# Windows 终端中文乱码时：写出 UTF-8 JSON 文件，避免 shell 重定向造成 UTF-16/BOM 解析问题
<PY> "scripts/autoclaw_pay_cli.py" --output product-info.json product-info
```

下单 payload 形状可用本地校验脚本检查；它不访问 AutoClaw，也不能证明商品可买：

```bash
<PY> "scripts/validate_order_payload.py" payload.json
```

## 支付接管

加油包下单结果如包含非空 `alipayMetadata.orderStr`，它只是支付宝待支付订单参数，不代表支付成功。不要展示、改写、压缩、转成其他链接，也不要再次询问用户确认；立即加载 `alipay-payment-skill`，把完整原始值作为 `cashier_url` 交给该技能处理。

```text
MUST_CALL_SKILL: alipay-payment-skill
cashier_url=<alipayMetadata["orderStr"] 的完整原始值>
```

支付技能完成前，不得宣称积分到账或订单完成。月度会员 `create-subscribe` 返回 `payment_markdown` 时，原样追加，不要改写图片路径。
