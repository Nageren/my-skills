#!/usr/bin/env bash
# Jenkins gtsp-k8s-slave 快速部署脚本
set -euo pipefail

BUILD_FLAG="true"
RESTART_FLAG="true"
WORK_DIR="/data/deploy/gtsp-develop"
JOB_NAME="gtsp-k8s-slave"
POLL_INTERVAL=15
MAX_WAIT=900
APP=""

usage() {
  cat <<'EOF'
用法: deploy.sh <app> [选项]

选项:
  --no-build       跳过编译打包 (BUILD=false)
  --no-restart     跳过重启 (RESTART=false)
  --work-dir PATH  源码目录 (默认 /data/deploy/gtsp-develop)
  -h, --help       显示帮助

示例:
  deploy.sh pay-service-cashier
  deploy.sh pay-service-trade --no-build
EOF
}

load_credentials() {
  if [[ -n "${JENKINS_URL:-}" && -n "${JENKINS_USERNAME:-}" && -n "${JENKINS_PASSWORD:-}" ]]; then
    return 0
  fi

  local mcp_json="${HOME}/.cursor/mcp.json"
  if [[ ! -f "$mcp_json" ]]; then
    echo "错误: 未设置 JENKINS_* 环境变量，且找不到 $mcp_json" >&2
    exit 1
  fi

  eval "$(python3 - "$mcp_json" <<'PY'
import json, sys, shlex
with open(sys.argv[1]) as f:
    cfg = json.load(f)
env = cfg.get("mcpServers", {}).get("jenkins-mcp", {}).get("env", {})
for key in ("JENKINS_URL", "JENKINS_USERNAME", "JENKINS_PASSWORD"):
    val = env.get(key, "")
    print(f"export {key}={shlex.quote(val)}")
PY
)"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --no-build) BUILD_FLAG="false" ;;
      --no-restart) RESTART_FLAG="false" ;;
      --work-dir)
        WORK_DIR="${2:?缺少 --work-dir 参数值}"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      -*)
        echo "未知选项: $1" >&2
        usage
        exit 1
        ;;
      *)
        if [[ -n "$APP" ]]; then
          echo "错误: 只能指定一个应用名" >&2
          usage
          exit 1
        fi
        APP="$1"
        ;;
    esac
    shift
  done

  if [[ -z "$APP" ]]; then
    usage
    exit 1
  fi
}

parse_args "$@"

load_credentials
JENKINS_URL="${JENKINS_URL%/}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "$COOKIE_JAR"' EXIT

echo ">>> 部署应用: $APP"
echo ">>> Jenkins:  $JENKINS_URL/job/$JOB_NAME/"

PREV_BUILD="$(curl -sf -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
  "${JENKINS_URL}/job/${JOB_NAME}/lastBuild/api/json" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('number',0))" || echo 0)"

CRUMB="$(curl -sf -c "$COOKIE_JAR" -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
  "${JENKINS_URL}/crumbIssuer/api/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])")"

BUILD_URL="${JENKINS_URL}/job/${JOB_NAME}/buildWithParameters"
QUERY="app=${APP}&work_dir=${WORK_DIR//\//%2F}&BUILD=${BUILD_FLAG}&RESTART=${RESTART_FLAG}"

HTTP_CODE="$(curl -sf -b "$COOKIE_JAR" -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
  -H "Jenkins-Crumb: ${CRUMB}" -X POST "${BUILD_URL}?${QUERY}" -o /dev/null -w '%{http_code}')"

if [[ "$HTTP_CODE" != "201" ]]; then
  echo "错误: 触发构建失败 (HTTP $HTTP_CODE)" >&2
  exit 1
fi

echo ">>> 构建已触发，等待任务入队..."

BUILD_NUMBER=""
for _ in $(seq 1 20); do
  sleep 3
  CURRENT="$(curl -sf -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
    "${JENKINS_URL}/job/${JOB_NAME}/lastBuild/api/json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('number',0))")"
  if [[ "$CURRENT" -gt "$PREV_BUILD" ]]; then
    BUILD_NUMBER="$CURRENT"
    break
  fi
done

if [[ -z "$BUILD_NUMBER" ]]; then
  echo "错误: 未能获取新构建号" >&2
  exit 1
fi

echo ">>> 构建号: #${BUILD_NUMBER}"
echo ">>> 链接: ${JENKINS_URL}/job/${JOB_NAME}/${BUILD_NUMBER}/"

ELAPSED=0
while [[ $ELAPSED -lt $MAX_WAIT ]]; do
  read -r BUILDING RESULT <<< "$(curl -sf -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
    "${JENKINS_URL}/job/${JOB_NAME}/${BUILD_NUMBER}/api/json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(str(d.get('building', False)), d.get('result') or 'None')
")"

  echo "[$(date '+%H:%M:%S')] building=${BUILDING} result=${RESULT}"

  if [[ "$BUILDING" == "False" ]]; then
    DURATION="$(curl -sf -u "${JENKINS_USERNAME}:${JENKINS_PASSWORD}" \
      "${JENKINS_URL}/job/${JOB_NAME}/${BUILD_NUMBER}/api/json" | python3 -c "
import sys,json
print(round(json.load(sys.stdin).get('duration',0)/1000, 1))
")"
    echo ""
    echo "=== 部署完成 ==="
    echo "应用:   $APP"
    echo "构建号: #${BUILD_NUMBER}"
    echo "结果:   ${RESULT}"
    echo "耗时:   ${DURATION}s"
    echo "链接:   ${JENKINS_URL}/job/${JOB_NAME}/${BUILD_NUMBER}/"

    if [[ "$RESULT" != "SUCCESS" ]]; then
      exit 1
    fi
    exit 0
  fi

  sleep "$POLL_INTERVAL"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

echo "错误: 等待超时 (${MAX_WAIT}s)" >&2
exit 1
