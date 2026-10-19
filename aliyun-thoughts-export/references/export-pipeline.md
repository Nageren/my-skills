# 导出流水线实现要点

实测环境：macOS + 用户已登录云效的 Chrome + lark-cli（飞书侧）。36 篇文档约 3-5 分钟。

## AppleScript runner（执行任意 JS 文件）

```applescript
on run argv
  set jsFile to item 1 of argv
  set js to read POSIX file jsFile
  tell application "Google Chrome"
    tell window id 1518279837   -- 用实际 window id（make new tab 返回值）
      set r to execute active tab javascript js
    end tell
  end tell
  return r
end run
```

Python 侧：`subprocess.run(["osascript", runner, js_path], capture_output=True, text=True, timeout=120)`，stdout 为 JSON。

## 同步 XHR 模板（页面上下文，自动带登录 cookie）

```js
(function(){
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '<url>', false);  // false = 同步，AppleScript 等不到 Promise
  xhr.send();
  if (xhr.status !== 200) return JSON.stringify({err: xhr.status, body: xhr.responseText.slice(0,500)});
  try { return JSON.stringify(JSON.parse(xhr.responseText)); }
  catch(e) { return JSON.stringify({err: 'parse', body: xhr.responseText.slice(0,500)}); }
})()
```

## 导航 + 等待加载（Python 侧轮询）

```python
run_js('(function(){ window.location.href = ' + json.dumps(url) + '; return "nav"; })()')
for attempt in range(20):
    time.sleep(2)
    probe = run_js('(function(){ return JSON.stringify({has: !!document.querySelector("div[data-slate-editor=true]"), title: document.title}); })()')
    if probe.get("has"):
        time.sleep(2)  # 等内容渲染完
        result = run_js(CONVERTER_JS)
        break
```

## Python 编排骨架

1. 读 nodes_all.json（BFS 递归得到的全部节点），筛 `type == "document"`
2. 每篇：导航 → 轮询 → 注入 `slate2md.js` → 写 `<docId>__<标题>.md`
3. 标题从 md 第一行 `# ` 提取（比 node.title 准），文件名 docId 前缀防重名
4. 图片：正则 `!\[image\]\((https?://[^)]+)\)` 提取 URL → 截断的换 thumbnail 源（见 SKILL.md）→ urllib 下载（带 `User-Agent` + `Referer: https://thoughts.aliyun.com/`，SSL 证书可跳过校验）

## 注意事项

- 导出期间提醒用户别操作那个 Chrome 窗口/标签页（导航会覆盖当前标签）
- `make new tab` 可能开进新窗口：记录返回的 `tab id X of window id Y`，用 window id 定位
- 图片下载用 md5(url) 前 12 位 + docId 前 8 位命名，存 `url -> 本地路径` 映射 json，导入飞书时替换 md 中的 URL
- 云效侧验证：`lark-cli auth status` 若 `user identity: missing (refresh token expired)`，需设备流重授权；`wiki +space-create` 仅支持 `--as user`
