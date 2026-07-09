# add-reviewer - 添加评审人

按优先级从多个来源自动选择合适的评审人，也支持手动指定。

## 执行流程

```
开始
  │
  ▼
获取当前 CR 信息（change-number）
  │
  ▼
用户是否指定了评审人?
  │
  ├─ 是 → 直接添加用户指定的评审人 → 结束
  │
  └─ 否 → 继续自动选择流程
           │
           ▼
         【按优先级收集候选评审人】
           │
           ├─ 1. 当前 CR 已有评审人（续传 CR 场景）
           │      └─ get_review_info → globalReviewers
           │
           ├─ 2. 仓库成员（repo members）
           │      └─ get_repo_members
           │
           └─ 3. 历史 CR 评审人（补充，当前两个来源不足 5 人时）
                  └─ get_repo_reviews(MERGED) → 遍历获取 reviewers
           │
           ▼
         汇总所有候选评审人，排除自己，去重
           │
           ▼
         是否有符合条件的评审人?
           │
           ├─ 是 → 展示候选列表供选择（或随机选取1个）
           │         │
           │         ▼
           │       添加评审人到当前 CR → 结束
           │
           └─ 否 → 提示用户手动指定评审人 → 结束
```

## 评审人来源优先级

| 优先级 | 来源 | 说明 | API |
|--------|------|------|-----|
| 1 | 当前 CR 评审人 | 续传 CR 时，优先使用已有评审人 | `get_review_info` |
| 2 | 仓库成员 | 有仓库权限的成员 | `get_repo_members` |
| 3 | 历史 CR 评审人 | 当前用户已合入 CR 的评审人 | `get_repo_reviews` + `get_review_info` |

## 快速使用

```bash
# 自动选择评审人
./add-reviewer.sh

# 指定 CR 编号，自动选择评审人
./add-reviewer.sh 120247220

# 手动指定评审人（跳过自动选择）
./add-reviewer.sh 120247220 zhangsan

# 多个评审人用逗号分隔
./add-reviewer.sh 120247220 "zhangsan,lisi"
```

## 参数说明

| 参数 | 说明 |
|------|------|
| CR 编号（第1个位置参数） | 可选，不指定则自动检测当前 commit 对应的 CR |
| 评审人（第2个位置参数） | 可选，指定后跳过自动选择，直接添加指定的评审人 |

## 注意事项

1. **用户指定优先**：如果用户指定了评审人，直接使用指定的，跳过自动选择
2. **优先级顺序**：当前 CR 评审人 > 仓库成员 > 历史 CR 评审人
3. **去重处理**：同一用户只添加一次，避免重复
4. **排除自己**：自动选择时会排除提交者本人
5. **补充机制**：仅当候选人不足 5 人时才查询历史 CR

## 相关命令

| 命令 | 说明 |
|------|------|
| `icode-cli api get_review_info` | 获取 CR 详情（含评审人） |
| `icode-cli api get_repo_members` | 获取仓库成员列表 |
| `icode-cli api get_repo_reviews` | 获取仓库 CR 列表 |
| `icode-cli api add_reviewers` | 添加评审人 |
