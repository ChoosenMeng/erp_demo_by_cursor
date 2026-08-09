#!/usr/bin/env bash
# First-time CentOS bootstrap for ERP Demo (Docker MySQL + Nginx + Node + uv/Python)
# CentOS 首次环境初始化（Docker MySQL + Nginx + Node + uv/Python）
#
# Uses Astral uv instead of Miniconda (better for ~1GiB RAM VPS).
# 使用 Astral uv 而非 Miniconda（更适合约 1GiB 内存的 VPS）。
#
# Run as root (or sudo) once / 请以 root（或 sudo）执行一次:
#   bash deploy/bootstrap-centos.sh
#
# Env overrides / 可用环境变量覆盖:
#   DEPLOY_PATH=/opt/erp_demo
#   GIT_REPO=https://github.com/ChoosenMeng/erp_demo_by_cursor.git
#   BRANCH=main
#   SERVER_IP=x.x.x.x

set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/erp_demo}"
GIT_REPO="${GIT_REPO:-https://github.com/ChoosenMeng/erp_demo_by_cursor.git}"
BRANCH="${BRANCH:-main}"
SERVER_IP="${SERVER_IP:-}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Please run as root / 请使用 root 执行"

detect_pkg() {
  if command -v dnf >/dev/null 2>&1; then
    echo dnf
  elif command -v yum >/dev/null 2>&1; then
    echo yum
  else
    die "Neither dnf nor yum found / 未找到 dnf 或 yum"
  fi
}

PKG="$(detect_pkg)"

install_base() {
  log "Installing base packages / 安装基础软件包"
  "$PKG" -y install git curl wget ca-certificates tar gzip which
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed / Docker 已安装"
  else
    log "Installing Docker Engine via yum/dnf repo / 通过 yum/dnf 仓库安装 Docker"
    # Avoid get.docker.com on CentOS 8 EOL: it may pull missing packages
    # (e.g. docker-model-plugin) and fail.
    # CentOS 8 已 EOL，官方便捷脚本常因缺失包（如 docker-model-plugin）失败。
    "$PKG" -y install dnf-plugins-core || true
    if [[ ! -f /etc/yum.repos.d/docker-ce.repo ]]; then
      dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo \
        || yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    fi
    # Do not install docker-model-plugin (unavailable on CentOS 8)
    # 不要安装 docker-model-plugin（CentOS 8 仓库中不存在）
    "$PKG" -y install \
      docker-ce \
      docker-ce-cli \
      containerd.io \
      docker-compose-plugin \
      docker-buildx-plugin \
      || die "Docker package install failed / Docker 软件包安装失败"
  fi
  systemctl enable --now docker
  if ! docker compose version >/dev/null 2>&1; then
    log "Installing docker compose plugin / 安装 docker compose 插件"
    "$PKG" -y install docker-compose-plugin || true
  fi
  docker --version
  docker compose version || true
}

install_nginx() {
  if command -v nginx >/dev/null 2>&1; then
    log "Nginx already installed / Nginx 已安装"
  else
    log "Installing Nginx / 安装 Nginx"
    "$PKG" -y install nginx
  fi
  systemctl enable --now nginx
}

install_node() {
  if command -v node >/dev/null 2>&1; then
    log "Node already installed: $(node -v) / Node 已安装"
    return 0
  fi
  log "Installing Node.js 22 via NodeSource / 通过 NodeSource 安装 Node.js 22"
  curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
  "$PKG" -y install nodejs
  node -v
  npm -v
}

ensure_swap_hint() {
  # Small VPS tip only — do not auto-create swap (user already may have done it)
  # 小内存提示：不自动创建 swap（用户可能已手动添加）
  local mem_kb
  mem_kb="$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
  if [[ "${mem_kb:-0}" -gt 0 && "${mem_kb}" -lt 1500000 ]]; then
    if ! swapon --show 2>/dev/null | grep -q .; then
      log "WARN: RAM <1.5GiB and no swap. Consider 2GiB swap for npm/build. / 内存较小且无 swap，建议加 2GiB swap"
    else
      log "Low-RAM host with swap detected — OK for uv/npm / 小内存主机已有 swap"
    fi
  fi
}

install_uv() {
  # Install Astral uv into /usr/local/bin for all users
  # 将 Astral uv 安装到 /usr/local/bin，供全局使用
  export PATH="/usr/local/bin:/root/.local/bin:${PATH}"
  if command -v uv >/dev/null 2>&1; then
    log "uv already installed: $(uv --version) / uv 已安装"
    return 0
  fi
  log "Installing uv (lightweight Python toolchain) / 安装 uv（轻量 Python 工具链）"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if [[ -x /root/.local/bin/uv ]]; then
    ln -sfn /root/.local/bin/uv /usr/local/bin/uv
  fi
  command -v uv >/dev/null 2>&1 || die "uv install failed / uv 安装失败"
  uv --version
}

install_python() {
  # Prefer uv on small VPS — Miniconda solver often OOMs under ~1GiB RAM
  # 小内存 VPS 优先用 uv；Miniconda 求解在约 1GiB 内存下容易 OOM
  ensure_swap_hint
  export PATH="/usr/local/bin:/root/.local/bin:${PATH}"

  local venv_py="$DEPLOY_PATH/.venv/bin/python"
  if [[ -x "$venv_py" ]]; then
    log "Project venv already exists: $venv_py / 项目虚拟环境已存在"
    ln -sfn "$venv_py" /usr/local/bin/python3.13
    "$venv_py" --version
    return 0
  fi

  if command -v python3.13 >/dev/null 2>&1 || command -v python3.12 >/dev/null 2>&1; then
    log "Python 3.12+ already present / 已有 Python 3.12+"
    local existing
    existing="$(command -v python3.13 || command -v python3.12)"
    mkdir -p "$DEPLOY_PATH"
    "$existing" -m venv "$DEPLOY_PATH/.venv"
    ln -sfn "$DEPLOY_PATH/.venv/bin/python" /usr/local/bin/python3.13
    "$DEPLOY_PATH/.venv/bin/python" --version
    return 0
  fi

  install_uv
  log "Installing Python 3.13 via uv and creating .venv / 用 uv 安装 Python 3.13 并创建 .venv"
  mkdir -p "$DEPLOY_PATH"
  uv python install 3.13
  uv venv "$DEPLOY_PATH/.venv" --python 3.13
  ln -sfn "$DEPLOY_PATH/.venv/bin/python" /usr/local/bin/python3.13
  ln -sfn "$DEPLOY_PATH/.venv/bin/pip" /usr/local/bin/pip3.13 2>/dev/null || true
  "$DEPLOY_PATH/.venv/bin/python" --version
}

clone_repo() {
  if [[ -d "$DEPLOY_PATH/.git" ]]; then
    log "Repo exists at $DEPLOY_PATH / 仓库已存在"
    return 0
  fi
  log "Cloning $GIT_REPO → $DEPLOY_PATH"
  mkdir -p "$(dirname "$DEPLOY_PATH")"
  git clone --branch "$BRANCH" "$GIT_REPO" "$DEPLOY_PATH"
}

prepare_env_files() {
  log "Preparing env files / 准备环境文件"
  if [[ ! -f "$DEPLOY_PATH/deploy/.env" ]]; then
    cp "$DEPLOY_PATH/deploy/.env.example" "$DEPLOY_PATH/deploy/.env"
    log "Created deploy/.env — CHANGE PASSWORDS / 已创建 deploy/.env，请修改密码"
  fi
  if [[ ! -f "$DEPLOY_PATH/backend/.env" ]]; then
    cp "$DEPLOY_PATH/deploy/backend.env.production.example" "$DEPLOY_PATH/backend/.env"
    if [[ -n "$SERVER_IP" ]]; then
      sed -i "s/YOUR_SERVER_IP/${SERVER_IP}/g" "$DEPLOY_PATH/backend/.env"
    fi
    log "Created backend/.env — set SECRET_KEY and passwords / 已创建 backend/.env，请设置密钥与密码"
  fi
}

install_systemd_nginx() {
  log "Installing systemd unit + nginx conf / 安装 systemd 与 Nginx 配置"
  cp "$DEPLOY_PATH/deploy/erp-api.service" /etc/systemd/system/erp-api.service
  if [[ "$DEPLOY_PATH" != "/opt/erp_demo" ]]; then
    sed -i "s|/opt/erp_demo|${DEPLOY_PATH}|g" /etc/systemd/system/erp-api.service
  fi
  systemctl daemon-reload

  local nginx_conf="/etc/nginx/conf.d/erp_demo.conf"
  cp "$DEPLOY_PATH/deploy/nginx.conf.example" "$nginx_conf"
  sed -i "s|/opt/erp_demo|${DEPLOY_PATH}|g" "$nginx_conf"
  if [[ -n "$SERVER_IP" ]]; then
    sed -i "s/YOUR_SERVER_IP/${SERVER_IP}/g" "$nginx_conf"
  fi
  # Avoid duplicate default_server (CentOS embeds one in nginx.conf, not only conf.d)
  # 避免重复 default_server（CentOS 常写在主 nginx.conf，不只是 conf.d）
  if [[ -f /etc/nginx/conf.d/default.conf ]]; then
    mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak || true
  fi
  # Strip default_server from main nginx.conf listen lines (keep listen ports)
  # 从主 nginx.conf 的 listen 行去掉 default_server（保留端口监听）
  if [[ -f /etc/nginx/nginx.conf ]] && grep -q 'default_server' /etc/nginx/nginx.conf; then
    cp -a /etc/nginx/nginx.conf "/etc/nginx/nginx.conf.bak.$(date +%Y%m%d%H%M%S)"
    # Only on listen lines: remove default_server, keep port / 仅改 listen 行：去掉 default_server，保留端口
    sed -i -E '/listen/s/[[:space:]]+default_server//g' /etc/nginx/nginx.conf
    log "Neutralized default_server in /etc/nginx/nginx.conf / 已中和主配置中的 default_server"
  fi
  nginx -t
  systemctl reload nginx
}

open_firewall() {
  # Open HTTP; SSH port is already in use by you (51822)
  # 开放 HTTP；SSH 端口你已在用（51822）
  if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld; then
    log "Opening firewall HTTP / 开放防火墙 HTTP"
    firewall-cmd --permanent --add-service=http || true
    firewall-cmd --reload || true
  else
    log "firewalld not active — ensure port 80 is open / firewalld 未启用，请自行开放 80"
  fi
}

main() {
  install_base
  install_docker
  install_nginx
  install_node
  # Clone before Python so .venv can live under DEPLOY_PATH
  # 先克隆仓库，再在 DEPLOY_PATH 下创建 .venv
  clone_repo
  install_python
  prepare_env_files
  install_systemd_nginx
  open_firewall

  chmod +x "$DEPLOY_PATH/deploy/deploy.sh"
  log "Bootstrap done. Next: / 初始化完成。下一步："
  log "  1) Edit $DEPLOY_PATH/deploy/.env and $DEPLOY_PATH/backend/.env"
  log "  2) DEPLOY_PATH=$DEPLOY_PATH bash $DEPLOY_PATH/deploy/deploy.sh"
  log "  3) sudo systemctl enable --now erp-api"
  log "Note: Python via uv (not Miniconda) for low-RAM VPS / 小内存用 uv，不用 Miniconda"
}

main "$@"
