#!/usr/bin/env bash
# Deploy ERP Demo on the server: pull → MySQL → backend → frontend build → restart
# 在服务器上部署 ERP Demo：拉取代码 → MySQL → 后端 → 前端构建 → 重启服务
#
# Usage / 用法:
#   DEPLOY_PATH=/opt/erp_demo bash deploy/deploy.sh
#   BRANCH=feature/m0-m1-scaffold bash deploy/deploy.sh

set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/erp_demo}"
BRANCH="${BRANCH:-feature/m0-m1-scaffold}"
COMPOSE_FILE="${DEPLOY_PATH}/deploy/docker-compose.yml"
COMPOSE_ENV="${DEPLOY_PATH}/deploy/.env"

log() {
  # Print timestamped log / 打印带时间戳的日志
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1 / 缺少命令: $1"
}

pick_python() {
  # Prefer project venv → 3.13 → 3.12 → python3
  # 优先项目 venv，其次 3.13 / 3.12 / python3
  if [[ -x "$DEPLOY_PATH/.venv/bin/python" ]]; then
    echo "$DEPLOY_PATH/.venv/bin/python"
    return 0
  fi
  for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  die "No python3 found. Run bootstrap (uv) or install Python 3.12+. / 未找到 python3，请先 bootstrap（uv）。"
}

compose() {
  # Prefer "docker compose" plugin, fallback to docker-compose
  # 优先使用 docker compose 插件，否则回退 docker-compose
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    die "docker compose not found / 未找到 docker compose"
  fi
}

mysql_ping_ok() {
  # Try compose exec, then docker exec — both use root password from deploy/.env
  # 先 compose exec，再 docker exec；均使用 deploy/.env 中的 root 密码
  # Note: if .env password changed after first volume init, ping will keep failing
  # 注意：若首次建库后改过 .env 密码，而数据卷仍是旧密码，ping 会一直失败
  if compose -f "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" exec -T mysql \
    mysqladmin ping -h 127.0.0.1 -uroot -p"${MYSQL_ROOT_PASSWORD}" --silent >/dev/null 2>&1; then
    return 0
  fi
  if docker exec erp-mysql \
    mysqladmin ping -h 127.0.0.1 -uroot -p"${MYSQL_ROOT_PASSWORD}" --silent >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

mysql_compose_healthy() {
  # Optional: trust compose healthcheck when status is "healthy"
  # 可选：若 compose 健康检查已为 healthy 则视为就绪
  local status=""
  status="$(compose -f "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" ps --format json 2>/dev/null \
    | tr -d '\r' || true)"
  if [[ -n "$status" ]] && echo "$status" | grep -qi '"Health"[[:space:]]*:[[:space:]]*"healthy"'; then
    return 0
  fi
  # Fallback for older compose without JSON: look at "healthy" in ps output
  # 旧版 compose 无 JSON 时，从 ps 文本中查找 healthy
  if compose -f "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" ps 2>/dev/null | grep -qi 'healthy'; then
    return 0
  fi
  return 1
}

dump_mysql_logs() {
  # Last lines of MySQL container logs for diagnosis / 打印 MySQL 日志末尾便于排查
  log "----- last 80 lines of docker logs erp-mysql -----"
  docker logs --tail 80 erp-mysql 2>&1 || true
  log "----- end mysql logs -----"
}

wait_mysql() {
  # Wait until MySQL accepts connections (small VPS: first boot can take several minutes)
  # 等待 MySQL 可连接（小内存 VPS 首次启动可能需数分钟）
  # ~100 retries * 3s ≈ 5 minutes / 约 100 次 × 3 秒 ≈ 5 分钟
  local retries=100
  local sleep_secs=3
  local i=0

  log "MySQL container status before wait / 等待前容器状态:"
  docker ps -a --filter "name=erp-mysql" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1 || true
  compose -f "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" ps 2>&1 || true

  # Fail early if container is not running / 容器未运行则尽早失败
  if ! docker ps --filter "name=erp-mysql" --filter "status=running" --format '{{.Names}}' \
    | grep -qx 'erp-mysql'; then
    log "ERROR: erp-mysql is not running / erp-mysql 未在运行"
    dump_mysql_logs
    die "MySQL container is not running. Check OOM (dmesg/free -h) or docker logs. / MySQL 容器未运行，请查 OOM 或日志。"
  fi

  log "Waiting for MySQL health (up to ~$((retries * sleep_secs))s)... / 等待 MySQL 就绪（最长约 $((retries * sleep_secs)) 秒）..."
  while (( i < retries )); do
    if mysql_ping_ok; then
      log "MySQL is up (mysqladmin ping) / MySQL 已就绪（mysqladmin ping）"
      return 0
    fi
    # Also accept compose healthcheck "healthy" if ping briefly flakes
    # ping 偶发失败时，也接受 compose healthcheck 的 healthy
    if mysql_compose_healthy; then
      log "MySQL is up (compose healthcheck) / MySQL 已就绪（compose 健康检查）"
      return 0
    fi
    # Re-check container still running mid-wait / 等待过程中确认容器仍在运行
    if ! docker ps --filter "name=erp-mysql" --filter "status=running" --format '{{.Names}}' \
      | grep -qx 'erp-mysql'; then
      log "ERROR: erp-mysql stopped during wait / 等待期间 erp-mysql 已停止"
      dump_mysql_logs
      die "MySQL container exited during wait (OOM or crash?). / 等待期间 MySQL 退出（可能 OOM/崩溃）。"
    fi
    sleep "$sleep_secs"
    i=$((i + 1))
    if (( i % 10 == 0 )); then
      log "Still waiting for MySQL... (${i}/${retries}) / 仍在等待 MySQL... (${i}/${retries})"
    fi
  done

  dump_mysql_logs
  log "Hints / 排查提示:"
  log "  - Password mismatch: deploy/.env MYSQL_ROOT_PASSWORD may differ from volume (first init). Recreate volume if safe."
  log "    密码不一致：.env 可能与数据卷首次初始化密码不同；确认可丢数据后重建卷。"
  log "  - OOM: free -h; dmesg | tail; MySQL 8 needs RAM+swap on ~1GiB hosts."
  log "    内存不足：free -h；小内存主机需 swap。"
  log "  - First-boot slowness: InnoDB init on small VPS can exceed 2–5 minutes."
  log "    首次启动慢：小 VPS 上 InnoDB 初始化可能超过 2–5 分钟。"
  die "MySQL did not become ready in time / MySQL 超时未就绪"
}

main() {
  need_cmd git
  need_cmd docker
  need_cmd npm
  need_cmd systemctl

  [[ -d "$DEPLOY_PATH/.git" ]] || die "Repo not found at $DEPLOY_PATH. Run bootstrap first. / 仓库不存在，请先 bootstrap。"
  [[ -f "$COMPOSE_ENV" ]] || die "Missing $COMPOSE_ENV (copy from deploy/.env.example) / 缺少 deploy/.env"
  [[ -f "$DEPLOY_PATH/backend/.env" ]] || die "Missing backend/.env / 缺少 backend/.env"

  # Load MySQL password for healthcheck / 加载 MySQL 密码供健康检查
  # shellcheck disable=SC1090
  set -a
  source "$COMPOSE_ENV"
  set +a
  MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-erp_root_change_me}"

  cd "$DEPLOY_PATH"
  log "Pulling branch $BRANCH / 拉取分支 $BRANCH"
  git fetch origin
  git checkout "$BRANCH"
  git reset --hard "origin/$BRANCH"

  log "Starting MySQL container / 启动 MySQL 容器"
  compose -f "$COMPOSE_FILE" --env-file "$COMPOSE_ENV" up -d
  wait_mysql

  export PATH="/usr/local/bin:/root/.local/bin:${PATH}"
  VENV_DIR="$DEPLOY_PATH/.venv"

  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    if command -v uv >/dev/null 2>&1; then
      # uv is lighter than conda on ~1GiB RAM hosts / 约 1GiB 内存主机上比 conda 更省
      log "Creating venv with uv (Python 3.13) / 使用 uv 创建虚拟环境"
      uv python install 3.13 || true
      uv venv "$VENV_DIR" --python 3.13
    else
      PYTHON_BIN="$(pick_python)"
      log "Creating venv with $PYTHON_BIN / 使用 $PYTHON_BIN 创建虚拟环境"
      "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
  fi

  log "Installing backend dependencies / 安装后端依赖"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  if command -v uv >/dev/null 2>&1; then
    # Faster / lower peak memory than plain pip on small VPS
    # 小 VPS 上比裸 pip 更快、峰值内存更低
    uv pip install --python "$VENV_DIR/bin/python" -r backend/requirements.txt
  else
    pip install --upgrade pip
    pip install -r backend/requirements.txt
  fi

  log "Running DB migrations / 执行数据库迁移"
  cd "$DEPLOY_PATH/backend"
  alembic upgrade head
  cd "$DEPLOY_PATH"

  log "Building frontend / 构建前端"
  cd "$DEPLOY_PATH/frontend"
  # Same-origin API via Nginx — keep VITE_API_BASE empty
  # 通过 Nginx 同源反代 API，保持 VITE_API_BASE 为空
  export VITE_API_BASE=""
  npm ci
  npm run build
  cd "$DEPLOY_PATH"

  log "Restarting API service / 重启 API 服务"
  if systemctl list-unit-files | grep -q '^erp-api.service'; then
    systemctl restart erp-api
    systemctl is-active --quiet erp-api || die "erp-api failed to start / erp-api 启动失败"
  else
    log "WARN: erp-api.service not installed yet / 尚未安装 systemd 单元"
  fi

  if command -v nginx >/dev/null 2>&1; then
    if nginx -t >/dev/null 2>&1; then
      systemctl reload nginx || true
    fi
  fi

  log "Deploy finished. Open http://YOUR_SERVER_IP/ / 部署完成，请用 IP 访问"
}

main "$@"
