# get_submit_settings

获取代码库的提交规则配置（提交规则、代码质量检查、流水线检查、评审设置、合入策略等）。

## 命令格式

```bash
icode-cli api get_submit_settings --repo <repo-name> [--check-permission] [-o json|yaml]
```

## 参数说明

| 参数 | 短参数 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--repo` | `-r` | 是 | - | 代码库全名，格式如 `baidu/project/repo` |
| `--check-permission` | - | 否 | false | 查询前检查读权限 |
| `--output` | `-o` | 否 | json | 输出格式：json、yaml |

## 使用示例

```bash
# 获取代码库的提交规则配置
icode-cli api get_submit_settings --repo baidu/icode/test

# 先检查权限再查询
icode-cli api get_submit_settings --repo baidu/icode/test --check-permission
```

## 输出格式

### JSON 格式（默认）

```json
{
  "status": "OK",
  "message": "",
  "data": {
    "needSubmitCheck": true,
    "forbidMergedCommit": false,
    "singleCommitPerReview": false,
    "checkCodeStyle": true,
    "needStaticCheck": true,
    "needSecurityCheck": true,
    "needUtCheck": false,
    "utCovRate": 0.6,
    "ignoreAgileScore": false,
    "reviewSetting": "REVIEW_REQUIRED",
    "autoSubmit": false,
    "submitStrategy": "MERGE_IF_NECESSARY"
  }
}
```

## 返回字段说明

### 提交规则

| 字段 | 类型 | 说明 |
|------|------|------|
| `needSubmitCheck` | bool | 是否需要提交检查 |
| `forbidMergedCommit` | bool | 是否禁止合并提交 |
| `singleCommitPerReview` | bool | 每次评审是否只能有一个提交 |
| `needIcafeCard` | bool | 是否需要关联 iCafe 卡片 |

### 代码质量检查

| 字段 | 类型 | 说明 |
|------|------|------|
| `checkCodeStyle` | bool | 是否检查代码风格 |
| `needStaticCheck` | bool | 是否需要静态检查 |
| `needSecurityCheck` | bool | 是否需要安全检查 |
| `needUtCheck` | bool | 是否需要单测检查 |
| `utCovRate` | float | 单测覆盖率要求 |

### 评审设置

| 字段 | 类型 | 说明 |
|------|------|------|
| `reviewSetting` | string | 评审设置 |
| `mustBeFixedBlock` | bool | 是否必须修复所有问题 |

### 合入设置

| 字段 | 类型 | 说明 |
|------|------|------|
| `autoSubmit` | bool | 是否自动合入 |
| `submitStrategy` | string | 合入策略 |

## 使用场景

1. **了解提交要求**：提交代码前了解仓库的各项检查要求
2. **配置检查**：检查仓库的检查项配置是否符合预期
3. **自动化流程**：根据配置决定是否执行某些检查

## 错误处理

| 错误信息 | 说明 | 解决方案 |
|----------|------|----------|
| `Repository may not exist` | 代码库不存在 | iCode API 对不存在的代码库返回 500 错误，请检查代码库名称 |
| `No read permission` | 无权限 | 确认是否有该代码库的读取权限 |

## 相关命令

- `icode-cli api get_repo_config`: 获取代码库基本配置
- `icode-cli api check_repo_permission`: 检查代码库权限
