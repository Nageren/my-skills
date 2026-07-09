# Draw.io → 飞书画板 导入流程

将 draw.io 导出的 HTML 架构图转换为飞书画板的完整工作流。

## 整体流程

```
drawio.html → 解析 XML → 分析架构结构 → 生成 DSL JSON → 渲染审查 → 创建飞书文档+画板 → 写入画板
```

## Step 1: 解析 draw.io HTML

draw.io HTML 文件在 `data-mxgraph` 属性中嵌入 XML 数据：

```python
import html, json, re

with open('drawio.html') as f:
    content = f.read()

match = re.search(r'data-mxgraph="({.+?})"', content)
raw = html.unescape(match.group(1))
data = json.loads(raw)
xml = data['xml'].replace('\\n', '\n').replace('\\"', '"')
```

从 XML 中提取所有节点标题（`value` 属性 + `vertex="1"`）：

```python
cells = re.findall(r'value="([^"]*?)"\s+vertex="1"', xml)
for cell in cells:
    print(cell)  # 每个 cell 是一个架构组件
```

## Step 2: 分析架构结构

提取的节点列表包含标题和层级关系。常见结构：
- **分层架构**：接入层 → 服务层 → 数据层
- **模块分组**：核心业务、平台支撑、平台扩展等
- **子服务**：每个模块下的具体服务

根据内容量选择合适的布局：
- 3-5 层 → 分层条带（Label-Outside）
- 6层以上 → 分层条带 + 子区域拆分

## Step 3: 生成 DSL JSON

参考 `scenes/architecture.md` 的分层条带模板。关键规则：

### JSON 不支持注释

```json
// ❌ 错误 — 字符串会被当作节点元素，导致 DSL 校验失败
"children": [
  "= LAYER 1: 接入层 =",  // ← 这是字符串，不是注释！
  { "type": "frame", ... }
]

// ✅ 正确 — 直接写有效节点
"children": [
  { "type": "frame", ... }
]
```

### 配色方案（经典色板）

| 层 | fillColor | borderColor | 说明 |
|---|-----------|-------------|------|
| 1 | #F0F4FC | #5178C6 | 蓝 |
| 2 | #EAE2FE | #8569CB | 紫 |
| 3 | #DFF5E5 | #509863 | 绿 |
| 4 | #FEF1CE | #D4B45B | 黄 |
| 5 | #FEE3E2 | #D25D5A | 红 |
| 6+ | 复用前5种 | 复用前5种 | 循环 |

### 节点结构

每层用 Label-Outside 模式：
```
[horizontal row]
  ├─ [text] 层标签（右对齐，80-90px）
  └─ [frame] 层容器（fill-container，浅色背景+深色边框）
       ├─ [frame] 服务卡片（白色背景+层色边框）
       │    ├─ [icon] 图标
       │    ├─ [text] 服务名
       │    └─ [text] 说明
       └─ ...
```

### 数据层用 cylinder

```json
{ "type": "cylinder", "width": 140, "height": "fit-content",
  "text": "db_name", "fillColor": "#FFFFFF",
  "borderColor": "#8569CB", "borderWidth": 2,
  "fontSize": 12, "textAlign": "center" }
```

> ⚠️ cylinder 固定宽度 120-200px，禁止用 fill-container

## Step 4: 渲染审查

```bash
npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.json -o diagram.png
```

检查项：
- 文字完整无截断
- 节点无重叠
- 配色清晰可读
- 间距合理

## Step 5: 创建飞书画板

### 所需 Auth Scope（3 次授权）

创建文档+画板需要依次授权以下 scope：

1. `docx:document:create` — 创建文档
2. `docx:document:write_only` + `docx:document:readonly` — 写入画板块
3. `board:whiteboard:node:create` — 写入画板内容

每次授权走 split-flow：
```bash
# 发起授权（返回二维码 URL）
lark-cli auth login --scope "docx:document:create" --no-wait --json
# → 展示二维码给用户 → 用户确认后：
lark-cli auth login --device-code <code>
```

### 创建文档

```bash
lark-cli docs +create --title "图表标题" --as user
```

### 添加画板块

```bash
lark-cli docs +update --api-version v2 \
  --doc <document_id> \
  --command append \
  --content '<whiteboard type="blank"></whiteboard>' \
  --as user
# → 从响应 data.new_blocks[].block_token 获取 whiteboard token
```

### 写入画板

```bash
TIMESTAMP=$(date +%s)
npx -y @larksuite/whiteboard-cli@^0.2.11 \
  -i diagram.json --to openapi --format json \
  | lark-cli whiteboard +update \
    --whiteboard-token <board_token> \
    --source - --input_format raw \
    --idempotent-token "arch-${TIMESTAMP}" \
    --as user \
    --overwrite
```

`--idempotent-token` 最少 10 字符，防重放。

## 常见陷阱

| 问题 | 原因 | 修复 |
|------|------|------|
| DSL 校验失败 "connector/svg/image/name required" | JSON 中混入了字符串元素（伪注释） | 删除 children 数组中的字符串，只留对象 |
| 授权失败 missing_scope | 未完成某次 auth login | 检查并逐一授权缺失 scope |
| whiteboard token 怎么拿 | 需先创建文档+添加画板块 | 从 docs +update 响应中提取 |
| 画板内容被追加而非覆盖 | 缺少 --overwrite | 加上 `--overwrite` flag |
| 文字被截断 | height 用了固定值 | 改为 `"height": "fit-content"` |
