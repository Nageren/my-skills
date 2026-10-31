#!/usr/bin/env python3
"""云效 Thoughts → 飞书 Wiki 批量导入（会话验证版）

要点：
- 飞书 wiki 的"文件夹"就是有子节点的 docx，文件夹/文档统一用 wiki +node-create
- 内容写入用 stdin（--content -），因为 --content @file 只接受相对路径
- 幂等：云效 node_id → 飞书 node_token 映射存 JSON，重跑跳过已建
- 图片无需手动上传：飞书导入 Markdown 时自动转存 URL 图片
"""
import json
import os
import subprocess

SPACE_ID = "7675227339063561199"          # wiki +space-create 返回的 space_id
EXPORT_DIR = "/tmp/thoughts_export"
MD_DIR = os.path.join(EXPORT_DIR, "markdown")
MAP_FILE = os.path.join(EXPORT_DIR, "feishu_node_map.json")


def run(cmd, timeout=180):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
    return r.stdout + r.stderr


def create_node(title, parent_token=None):
    cmd = f'lark-cli wiki +node-create --space-id {SPACE_ID} --title "{title}" --as user --json 2>&1'
    if parent_token:
        cmd = f'lark-cli wiki +node-create --space-id {SPACE_ID} --parent-node-token {parent_token} --title "{title}" --as user --json 2>&1'
    out = run(cmd)
    try:
        idx = out.find('{')
        d = json.loads(out[idx:])
        data = d.get("data", {})
        return data.get("node_token"), data.get("obj_token"), data.get("url", "")
    except Exception as e:
        print(f"  !! create_node FAILED for {title}: {out[:250]} {e}", flush=True)
        return None, None, None


def write_doc_content(obj_token, md_content, title):
    """覆盖写入 Markdown（stdin 方式；自动转存图片）"""
    md_file = "/tmp/_doc_content.md"
    with open(md_file, "w") as f:
        f.write(md_content)
    cmd = f'cat "{md_file}" | lark-cli docs +update --api-version v2 --doc {obj_token} --command overwrite --doc-format markdown --content - --as user --json 2>&1'
    out = run(cmd)
    if "success" in out:
        return True
    print(f"  !! write FAILED for {title}: {out[:200]}", flush=True)
    return False


def main():
    with open(os.path.join(EXPORT_DIR, "nodes_all.json")) as f:
        nodes = json.load(f)
    created_map = {}
    if os.path.exists(MAP_FILE):
        with open(MAP_FILE) as f:
            created_map = json.load(f)

    by_parent = {}
    for n in nodes:
        pid = n.get("_parentId") or "root"
        by_parent.setdefault(pid, []).append(n)

    def process_level(parent_id, parent_feishu_token=None, depth=0):
        for n in by_parent.get(parent_id, []):
            nid, title, ntype = n["_id"], n.get("title", ""), n.get("type", "")
            indent = "  " * depth
            if nid in created_map and created_map[nid]:  # 幂等跳过
                print(f"{indent}[SKIP] {title}", flush=True)
                if ntype == "folder":
                    process_level(nid, created_map[nid], depth + 1)
                continue
            node_token, obj_token, url = create_node(title, parent_feishu_token)
            if not node_token:
                print(f"{indent}  !! FAILED", flush=True)
                continue
            created_map[nid] = node_token
            print(f"{indent}[{'FOLDER' if ntype=='folder' else 'DOC'}] {title} -> {url}", flush=True)
            if ntype == "folder":
                process_level(nid, node_token, depth + 1)
            else:
                md_path = next((os.path.join(MD_DIR, fn) for fn in os.listdir(MD_DIR)
                                if fn.startswith(nid + "__")), None)
                if md_path:
                    with open(md_path) as f:
                        md = f.read()
                    ok = write_doc_content(obj_token, md, title)
                    print(f"{indent}  内容: {'OK' if ok else 'FAIL'} ({len(md)} chars)", flush=True)

    process_level("root", None, 0)
    with open(MAP_FILE, "w") as f:
        json.dump(created_map, f, ensure_ascii=False, indent=1)
    print(f"\n完成。共创建 {len(created_map)} 个节点", flush=True)


if __name__ == "__main__":
    main()
