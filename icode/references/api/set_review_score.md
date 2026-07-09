# set_review_score - 设置评审分数

为代码评审设置评分。

## 命令格式

```bash
icode-cli api set_review_score --repo <代码库名称> --change-number <评审编号> --score <分数>
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--score` | `-s` | 是 | - | 评分值（-2 到 +2） |

## 使用示例

```bash
# 批准评审（+2）
icode-cli api set_review_score --repo baidu/icode/test -n 12345 --score 2

# 表示认可但需要其他人批准（+1）
icode-cli api set_review_score -r baidu/icode/test -n 12345 -s 1

# 请求修改（-1）
icode-cli api set_review_score --repo baidu/icode/test --change-number 12345 --score -1

# 拒绝评审（-2）
icode-cli api set_review_score -r baidu/icode/test -n 12345 -s -2
```

## 分数含义

| 分数 | 含义 |
|------|------|
| `+2` | 批准合并（Looks good to me, approved） |
| `+1` | 认可但需要其他人批准（Looks good to me, but someone else must approve） |
| `0` | 无评分 |
| `-1` | 建议不要提交（I prefer you don't submit this） |
| `-2` | 拒绝合并（Do not submit） |

## 返回数据

```
Status: OK
Message: 操作成功
Score: 2
```

## 注意事项

- 需要有该评审的评审权限
- 评分值必须在 -2 到 +2 之间
- 评分会影响评审是否可以合并
- 同一评审者的新评分会覆盖之前的评分
