---
name: gtsp-code-contribution
description: "统计云效组织下所有 Git 仓库的代码贡献数据。统计提交数、行数变更、发版次数（tag），并按人员/仓库/组汇总。输出到 Obsidian 报告。触发词: 代码贡献、贡献统计、代码量、发版次数、人员统计、项目统计、gtsp"
---

# gtsp 代码贡献统计

统计云效组织下指定组的 Git 仓库贡献数据。自动拉取最新代码，排除 target/ 目录和 merge 提交，按人员和仓库维度汇总，包含发版次数（tag）。

## 关键参数

从用户对话中确认：

| 参数 | 说明 | 默认值 |
|------|------|-------|
| `groups` | 需要统计的子组 | 用户指定（如 `gtsp/account`, `gtsp/payment`） |
| `base_dir` | 本地仓库根目录 | `/Users/marvin/IdeaProjects` |
| `since` | 统计起始日期 | `2026-04-01`（或用户指定） |
| `output` | 输出方式 | 控制台 + Obsidian `reports/` |
| `exclude_target` | 是否排除 target/ | `true` |
| `exclude_merge` | 是否排除 merge 提交 | `true` |

## 工作流

### Phase 1: 查找仓库

扫描 `base_dir` 下所有 `.git` 目录，根据 remote origin URL 匹配组织下的目标组。

```bash
find <base_dir> -name ".git" -maxdepth 3 -type d
git -C <repo_dir> remote get-url origin
# 过滤 pattern: <org_id>/<groups>/ 如: 610b3c9d86508f8da8b08436/gtsp/account/
```

### Phase 2: 拉取最新代码

```bash
git -C <repo_dir> fetch --all --prune --quiet
```
失败记录但不中断流程。

### Phase 3: 统计提交数

```bash
git shortlog -sn --no-merges --since=<since> --all
```

### Phase 4: 统计行数变更

```bash
# shortstat 方式（推荐）
git log --no-merges --since=<since> --format=%aN --all --shortstat
```
解析 shortstat 行：匹配 `(\d+) insertion` 和 `(\d+) deletion`。

排除 target/ 可通过两个途径：
- shortstat 无法排除 → 用整体行数减去 target/ 行数（通过 numstat 过滤）
- 或用 numstat 方式逐文件过滤 `/target/`

### Phase 5: 统计发版次数（tag）

```bash
# 全部 tag
git tag -l

# 周期内 tag（带日期）
git tag -l --sort=-creatordate --format="%(refname:short)|%(creatordate:short)"

# 打 tag 人
git tag -l --format="%(taggername)"
```

### Phase 5.5: 作者名映射

输出前将 git author 映射为真实姓名。映射表见 `references/author-mapping.md`。

关键映射（可直接在脚本中使用）：

```python
AUTHOR_MAP = {
    "Marvin": "马文磊", "chenlongxing": "陈龙星", "fandayong": "范大勇", "yangyahui": "杨亚辉",
    "liyonghu": "李勇虎", "dayu": "朱大余", "mawanlei": "马万垒",
    "chenjiafu": "陈家富", "tanxm": "谭祥美", "caiwenchen": "蔡汶辰",
    "bx": "单宝新", "yeyushuai": "叶玉帅", "18310002279": "李彬",
    "zhaoxianghe": "赵向鹤",
    "sunjinglong": "孙景龙", "lishizhang": "李世章",
    "XuanShuangQi": "宣双奇", "zhangchao3": "张超", "zhangxin": "张鑫",
    "renshibo": "任世波", "liuchenghu": "刘成虎", "mengfanping": "孟凡平",
    "xiawbo": "夏文波", "nzhch": "倪志超",
    "wangyoufu01": "王有富", "yuanhaodong": "袁浩东", "zhangteng": "张腾",
    "wenbin.zhou": "周文斌", "songyang01": "宋杨", "henry": "Henry",
}
```

### Phase 6: 汇总聚合

```python
# 按作者聚合
author_data[(group, author)] = [commits, ins, del]

# 按仓库明细
repo_data[(group, repo)] = {commits, authors: [(name, count), ...]}
```

## 解析注意事项

### shortstat 格式

```
" 1 file changed, 10 insertions(+), 2 deletions(-)"
" 1 file changed, 5 insertions(+)"
" 1 file changed, 2 deletions(-)"
```

区分统计行和作者名：含 ` file` 关键字的是统计行。

### 已知问题

- **宋杨** ~98% 是 merge 提交，必须用 `--no-merges`
- **liyonghu** ~40% 是 merge 提交（发布工程师）
- 中文作者名在 shortstat 中可能编码异常，提交数改用 `shortlog -sn`
- 发布工程师 liyonghu 负责全部 tag 操作
- 版本号统一为 `Release-v1.2.3.xxx`，各服务同批次发版

## Obsidian 输出

路径：`<vault_path>/reports/<report-name>.md`

包含 frontmatter（tags, created, status），总览表格、各组统计、人员-项目矩阵、团队画像。
