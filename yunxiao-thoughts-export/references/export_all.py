#!/usr/bin/env python3
"""云效 Thoughts 知识库批量导出主流程（会话验证版，需配合 run_js.applescript + slate2md.js）

用法：
  1. 修改 WS 为知识库 workspace id
  2. 先跑 `python3 export_flow.py tree` 抓节点树（递归），保存 nodes_all.json
  3. 再跑 `python3 export_flow.py docs` 批量导出全部文档为 Markdown
前置：本机 Chrome 已登录云效 + 已开启「允许 Apple 事件中的 JavaScript」
"""
import json
import os
import subprocess
import sys
import time

WS = "6a2b607bb46fd80014e9300c"          # 替换为目标 workspace
OUT_DIR = "/tmp/thoughts_export"
BASE = f"https://thoughts.aliyun.com/api/workspaces/{WS}"
MD_DIR = os.path.join(OUT_DIR, "markdown")
os.makedirs(MD_DIR, exist_ok=True)

RUN_JS = "/tmp/run_js.applescript"       # 复制自 references/run_js.applescript
CONVERTER = "/tmp/slate2md.js"           # 复制自 references/slate2md.js
with open(CONVERTER) as f:
    CONVERTER_JS = f.read()


def run_js(js_content):
    """经 AppleScript 在本机 Chrome 活动标签页执行 JS"""
    js_path = "/tmp/_tmp_js.js"
    with open(js_path, "w") as f:
        f.write(js_content)
    r = subprocess.run(["osascript", RUN_JS, js_path],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return {"error": r.stderr[:500]}
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"raw": r.stdout.strip()[:3000]}


def sync_get(url):
    """页面上下文同步 XHR——fetch 是异步的，AppleScript 等不到 Promise"""
    js = f"""(function(){{
      var xhr = new XMLHttpRequest();
      xhr.open('GET', {json.dumps(url)}, false);
      xhr.send();
      if (xhr.status !== 200) return JSON.stringify({{err: xhr.status, body: xhr.responseText.slice(0,500)}});
      try {{ return JSON.stringify(JSON.parse(xhr.responseText)); }} catch(e) {{ return JSON.stringify({{err: 'parse', body: xhr.responseText.slice(0,500)}}); }}
    }})()"""
    return run_js(js)


def fetch_tree():
    """递归抓全部节点：顶层只返回 folder，必须按 _parentId 递归"""
    all_nodes, seen = [], set()

    def fetch_children(parent_id):
        url = f"{BASE}/nodes?pageSize=1000"
        if parent_id:
            url += f"&_parentId={parent_id}"
        d = sync_get(url)
        if "err" in d:
            print("ERR:", json.dumps(d, ensure_ascii=False)[:500]); return []
        new = []
        for n in d.get("result", []):
            if n.get("_id") not in seen:
                seen.add(n.get("_id")); new.append(n)
        return new

    top = fetch_children(None)
    all_nodes.extend(top)
    queue = [n for n in top if n.get("type") == "folder"]
    while queue:
        n = queue.pop(0)
        kids = fetch_children(n.get("_id"))
        all_nodes.extend(kids)
        queue.extend(k for k in kids if k.get("type") == "folder")
    with open(os.path.join(OUT_DIR, "nodes_all.json"), "w") as f:
        json.dump(all_nodes, f, ensure_ascii=False, indent=1)
    print(f"total nodes: {len(all_nodes)}")
    return all_nodes


def navigate_and_convert(doc_id):
    """导航到文档页 → 轮询等待 Slate 编辑器 → 转换 Markdown"""
    url = f"https://thoughts.aliyun.com/workspaces/{WS}/docs/{doc_id}"
    run_js(f'(function(){{ window.location.href = {json.dumps(url)}; return "nav"; }})()')
    for _ in range(20):
        time.sleep(2)
        probe = run_js('(function(){ var r = document.querySelector("div[data-slate-editor=true]"); return JSON.stringify({has: !!r, title: document.title}); })()')
        if isinstance(probe, dict) and probe.get("has"):
            time.sleep(2)
            result = run_js(CONVERTER_JS)
            if isinstance(result, dict) and result.get("ok"):
                return result
            if isinstance(result, dict) and result.get("err") == "NO_EDITOR":
                continue
            return result
    return {"error": "timeout waiting for editor"}


def export_docs():
    with open(os.path.join(OUT_DIR, "nodes_all.json")) as f:
        nodes = json.load(f)
    docs = [n for n in nodes if n.get("type") == "document"]
    results = {}
    for i, doc in enumerate(docs):
        doc_id, title = doc["_id"], doc.get("title", "")
        print(f"[{i+1}/{len(docs)}] {title}...", flush=True)
        r = navigate_and_convert(doc_id)
        if r.get("ok"):
            md = r["md"]
            first_line = md.split('\n')[0] if md else ''
            fname = (first_line.replace('# ', '').strip() or title).replace('/', '_')[:80]
            path = os.path.join(MD_DIR, f"{doc_id}__{fname}.md")
            with open(path, "w") as f:
                f.write(md)
            results[doc_id] = {"title": fname, "path": path, "len": len(md)}
            print(f"  OK {len(md)} chars")
        else:
            print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:200]}")
            results[doc_id] = {"title": title, "error": str(r)[:200]}
    with open(os.path.join(OUT_DIR, "export_results.json"), "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    ok = sum(1 for v in results.values() if "path" in v)
    print(f"\n完成。成功: {ok}/{len(docs)}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "tree"
    if mode == "tree":
        fetch_tree()
    elif mode == "docs":
        export_docs()
