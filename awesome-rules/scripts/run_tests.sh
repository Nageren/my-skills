#!/usr/bin/env bash
# 全量测试门禁 — 串行套件循环 + 尾段
#
# 各套件有独立 rootdir（pytest.ini / conftest.py 注入 sys.path），不能用一次
# pytest 跑完，故按目录循环。部分套件 pytest.ini 带覆盖率 addopts（--cov），
# 本机未装 pytest-cov 时会被拦，门禁统一覆盖为空 addopts——覆盖率由专职
# 命令负责，门禁只管测试通过与否。
#
# 历史（ADR-016，2026-09-29 迁移裁决）：8 套件 + badcase + lease-sql 共 10 段
# 的 fan-out 编排曾下沉工厂并行门（.factory/factory_lib.py parallel-gate）；黑盒
# 工厂已整体迁至 im47cn/awesome-factory，本仓不再有工厂编排器，套件面随迁收窄
# 为 5 个技能套件 + badcase 的串行循环（实测 ≈40s；提速需求重现时按 ADR-016
# 先例在 awesome-factory 侧重建编排，负控制随迁）。
# 秒级尾段（plugin_lock/doc_freshness/lint-shellcheck）不并行：无收益，
# 且 lint-shellcheck 层的文件清单被 NC16 镜像锁按文本抽取
#（tools/test_gauntlet_checks.sh），保持原序原形态以保其解析与负控制语义。
#
# 并行安全（审计 2026-09-04）：各 pytest 段临时文件均唯一命名
# （mkdtemp / NamedTemporaryFile）；skill-evo 固定 /tmp/ar-skill-evo-prompt.md
# 仅 skill-evo 段读写——单实例内安全，但禁止两个本脚本实例并发运行
# （固定路径会互撞）。
#
# 用法:
#   bash scripts/run_tests.sh            # 测试 + 安装入口 blob 锁定校验
#   bash scripts/run_tests.sh --no-lock  # 仅测试
set -u -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1
PY="${PYTHON:-python3}"

FAILED=()  # 先于 trap 注册（set -u 下 trap 引用 ${#FAILED[@]}，提前退出不 unbound）
rc=0  # 先于 trap 注册：trap 串内 rc=$? 对 shellcheck 静态不可见（SC2154 消音，同上先例）
trap 'rc=$?; if [ $rc -ne 0 ] || [ "${#FAILED[@]}" -gt 0 ]; then
  echo "❌ run_tests 失败 (rc=$rc)" >&2
fi' EXIT

# ── 串行套件段：5 个技能套件（rootdir 各异，见头注释）──────────────────
run_suite() {
  # run_suite <失败tag> <cwd> <pytest 位置参数...>
  _tag=$1 _cwd=$2
  shift 2
  echo "── ${_tag}"
  if ! (cd "$_cwd" && "$PY" -m pytest "$@" -o addopts= -q); then
    FAILED+=("$_tag")
  fi
}

run_suite api-guard skills/api-guard/scripts .
run_suite arch-guard skills/arch-guard/scripts .
run_suite ddl-guard skills/ddl-guard/scripts .
run_suite impact-guard skills/impact-guard/scripts tests
run_suite skill-evo skills/skill-evo/scripts tests

echo "── badcase"
if ! "$PY" scripts/badcase_runner.py | tail -3; then
  FAILED+=("badcase")
fi

# ── 尾段（秒级；lint-shellcheck 受 NC16 文本镜像锁约束）─────────────────

# 安装入口锁定（zero-regression 门禁，与测试同为推送前置）
if [ "${1:-}" != "--no-lock" ]; then
  echo "── plugin_lock"
  if ! "$PY" scripts/plugin_lock.py; then
    FAILED+=("plugin_lock")
  fi
  echo "── md_link_check"
  if ! "$PY" scripts/md_link_check.py; then
    FAILED+=("md_link_check")
  fi
fi

# 文档新鲜度（实现↔文档一致性，R3-R12 见 tools/check_doc_freshness.py 头注释）。
# 刻意放在 --no-lock 分支外：快速回归（--no-lock）也须核文档一致性。
echo "── doc_freshness"
if ! "$PY" tools/check_doc_freshness.py; then
  FAILED+=("doc_freshness")
fi

# lint-shellcheck：tools/ 门禁脚本静态检查，文件清单镜像自 gauntlet.sh 的
# lint-shellcheck 层（权威清单），两处须同步维护。本地 push 面此前缺此层，
# CI（config-evals-gate 全量 gauntlet）拦下而本地四闸放行（2026-09-04
# SC2016 实证「本地绿 CI 红」）。软门禁：未装 shellcheck 时提示安装指引后
# 跳过（安装指引见层内提示；CI 侧仍会拦），装好即自动生效硬拦。
echo "── lint-shellcheck"
if command -v shellcheck >/dev/null 2>&1; then
  if ! shellcheck tools/gauntlet.sh tools/must_not_match.sh tools/run_diff_cover.sh \
      tools/test_gauntlet_orchestration.sh tools/test_gauntlet_checks.sh \
      tools/test_spec_check.sh tools/test_pre-push-delete-guard.sh \
      tools/git/install.sh tools/git/lefthook/coverage.sh \
      tools/git/lefthook/commitmsg-check.sh tools/git/lefthook/run-tests.sh \
      tools/git/lefthook/spec-check.sh tools/git/lefthook/sourcery-gate.sh \
      tools/git/lefthook/coderabbit-gate.sh \
      tools/git/lefthook/pre-push-delete-guard.sh; then
    FAILED+=("lint-shellcheck")
  fi
else
  echo "[lint] 缺 shellcheck，跳过（mac: brew install shellcheck / Linux: apt install shellcheck 启用；CI 侧仍会拦）"
fi

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "❌ 门禁失败: ${FAILED[*]}" >&2
  exit 1
fi
echo "✅ 全量测试门禁通过（5 个技能套件 + badcase）"
