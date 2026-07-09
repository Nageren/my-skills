# push_cr - 推送代码评审

将当前分支推送到 Gerrit 进行代码评审（Code Review）。

## 命令格式

```bash
icode-cli git push_cr [--repo-path <仓库路径>] [--branch <目标分支>]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo-path` | `-r` | 否 | 当前目录 | Git 仓库路径 |
| `--branch` | `-b` | 否 | master 或当前分支 | 目标分支名称 |

## 使用示例

```bash
# 推送到 master 分支进行代码评审
icode-cli git push_cr

# 推送到指定分支
icode-cli git push_cr --branch develop

# 从指定仓库路径推送
icode-cli git push_cr --repo-path ./my-project --branch feature/test
```

## 执行流程

1. **检查仓库**：确认当前目录是 Git 仓库
2. **检查凭证**：检查 Git 凭证配置
3. **获取远程**：从 origin 获取远程 URL
4. **配置 HTTPS**：确保 HTTPS 远程可用
5. **推送到 Gerrit**：执行 `git push origin HEAD:refs/for/<branch>`
6. **返回 CR URL**：解析并输出代码评审链接

## 输出示例

```
https://icode.baidu.com/c/baidu/icode/test/+/123456
```

输出的 URL 即为代码评审（CR）的链接，可以直接在浏览器中打开进行评审操作。

## Gerrit 代码评审说明

### refs/for 机制

Gerrit 使用特殊的 `refs/for/<branch>` 引用来接收代码评审：

- 推送到 `refs/for/master` 会创建一个针对 master 分支的 CR
- 代码不会直接合并到目标分支，而是进入评审流程
- 评审通过后，代码才会被合并

### Change-Id

每个提交需要包含 Change-Id，用于标识同一个变更的多次修订：

```
commit abc123
Author: zhangsan <zhangsan@baidu.com>
Date:   Mon Jan 15 10:00:00 2024 +0800

    feat: add new feature

    Change-Id: I1234567890abcdef
```

使用 `icode-cli git clone` 克隆的仓库会自动安装 `commit-msg` hook，自动生成 Change-Id。

## 代码评审流程

```
1. 提交代码评审
   icode-cli git push_cr --branch master

2. 获得 CR URL，分享给评审人
   https://icode.baidu.com/c/baidu/icode/test/+/123456

3. 评审人在 iCode 平台进行评审
   - 查看代码变更
   - 添加评论
   - 给出评分（+2 批准，-2 拒绝）

4. 根据评审意见修改代码
   git add .
   git commit --amend  # 修订同一个变更
   icode-cli git push_cr --branch master

5. 评审通过后合并
   - 在 iCode 平台点击 Submit
   - 或使用 API: icode-cli api submit_review
```

## 注意事项

- 必须在 Git 仓库内执行，或使用 `--repo-path` 指定仓库路径
- 提交必须包含 Change-Id（使用 `commit-msg` hook 自动生成）
- 需要有代码库的提交权限
- 同一个 Change-Id 的多次推送会更新同一个 CR（而不是创建新的）
