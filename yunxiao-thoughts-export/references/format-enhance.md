# 飞书 docx 排版增强：代码高亮与服务器属性行为

实测于「风控」知识库 36 篇文档（28 个代码块、47 个表格、20 张图片）。

## 代码块语言高亮（可落地 ✅）

给 `<pre>` 加 `lang` 属性，飞书渲染端显示对应语法高亮：

```xml
<pre lang="sql"><code>select ...</code></pre>
```

写回后 fetch 验证：`<pre caption="&#xA;" lang="sql">` — lang 持久保存。

### 语言检测启发式（真实库分布：sql 13 / java 3 / json 3 / yaml 3 / text 6）

```python
def detect_lang(code_text):
    t = code_text.strip()
    if not t: return 'text'
    first_lines = '\n'.join(t.split('\n')[:5]).lower()
    # SQL
    if re.search(r'\b(select|insert|update|delete|create table|alter table|create index|drop table)\b', t, re.I) \
       or (re.search(r'\b(from|into|where|values)\b', t, re.I) and re.search(r'\b(sql|table|select)\b', t, re.I)):
        return 'sql'
    # Java
    if re.search(r'\b(public|private|protected|class|interface|void|import|package)\b', t[:500]) \
       or re.search(r'@\w+ArgsConstructor', t):
        return 'java'
    # JSON
    if re.match(r'^\s*[{\[]', t) and re.search(r'"[^"]+"\s*:', t):
        return 'json'
    # YAML（首行 key: 形式）
    if re.match(r'^[a-zA-Z_-]+:\s*$', t.split('\n')[0]) or re.match(r'^[a-zA-Z_-]+:\s', t.split('\n')[0]):
        return 'yaml'
    # XML
    if re.match(r'^\s*<[?]?xml', t) or (re.search(r'<[a-zA-Z]+[^>]*>', t[:200]) and '</' in t):
        return 'xml'
    # Bash
    if re.match(r'^(#!/|export |cd |curl |git |mvn |docker |kubectl |sh |java -jar|nohup )', t.split('\n')[0]):
        return 'bash'
    return 'text'
```

注意：代码内容里 `<`/`>`/`&` 已被 XML 转义（`&gt;`/`&lt;`/`&amp;`），检测前先还原。

## 服务端静默丢弃的属性（白费力气，别做 ❌）

用独立测试文档（`docs +create` + XML overwrite + fetch）实测：

| 属性 | 结果 |
|---|---|
| `th background-color="light-gray"` | 写入 success 但 fetch 后**属性消失** |
| `img width="800" height="177"` | 同样**被丢弃** |

结论：
- 飞书 web 端宽图默认等比缩放适配页面宽度（图原宽 2260px 也无须处理）
- 表格表头默认灰底加粗，视觉已满足「表头标题」需求
- 不要把 th/img 样式塞进 XML overwrite——纯属白费，且无法验证

## 验证正则（避开陷阱）

- 代码块：`<pre[^>]*lang="([^"]+)"` —— lang 可能排在 caption 之后，`[^>]*` 必须在前
- 图片数量：`<img[^>]*src="` 计数；**不要**用 `width=` 统计（写了也会被服务端丢弃）
- 写回后全库验证：统计 lang 分布 + `<img[^>]*src=` 总数不变 + 无 `Plain Text` 残留

## 批量写回模式

1. 先 `docs +fetch` 全量备份（含 revision_id）
2. dry-run 本地转换统计变更数
3. 后台批量 `cat file.xml | lark-cli docs +update --api-version v2 --doc <token> --command overwrite --doc-format xml --content - --as user`
4. 全量 fetch 验证（不是抽查）
