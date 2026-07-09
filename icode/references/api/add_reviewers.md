# add_reviewers - 添加评审人

为代码评审添加一个或多个评审人。

## 命令格式

```bash
icode-cli api add_reviewers --change-number <评审编号> --reviewers <评审人列表>
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--change-number` | `-n` | 是 | - | 评审编号（数字） |
| `--reviewers` | `-r` | 是 | - | 评审人用户名，多个用逗号分隔 |

## 使用示例

```bash
# 添加单个评审人
icode-cli api add_reviewers -n 12345 --reviewers zhangsan

# 添加多个评审人
icode-cli api add_reviewers --change-number 12345 --reviewers zhangsan,lisi,wangwu

# 简写形式
icode-cli api add_reviewers -n 12345 -r zhangsan,lisi
```

## 返回数据

```
Status: OK
Message: 操作成功
Added reviewers: zhangsan, lisi, wangwu
```

## 注意事项

- 需要有该评审的编辑权限
- 评审人用户名必须是有效的 iCode 用户
- 多个评审人使用逗号分隔，不要有空格
- 已经是评审人的用户会被忽略
