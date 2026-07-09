# submit_review - 提交/合并评审

提交代码评审进行合并。

## 命令格式

```bash
icode-cli api submit_review --repo <代码库名称> --change-number <评审编号>
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库名称，三层目录形式 |
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |

## 使用示例

```bash
# 提交评审进行合并
icode-cli api submit_review --repo baidu/icode/test -n 12345

# 简写形式
icode-cli api submit_review -r baidu/icode/test -n 12345
```

## 返回数据

```
Status: OK
Message: 操作成功
Review 12345 has been submitted
```

## 合并前提条件

评审必须满足以下条件才能被合并：

1. 已获得必要的评审批准（+2）
2. 所有机器检查已通过
3. 没有未解决的评审意见
4. 代码可以无冲突合并

## 注意事项

- 需要有该评审的提交权限
- 评审必须处于 NEW 状态
- 如果评审不满足合并条件，操作会失败
- 合并后评审状态变为 MERGED
