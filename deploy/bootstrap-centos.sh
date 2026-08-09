#!/usr/bin/env bash
# First-time CentOS bootstrap for ERP Demo (Docker MySQL + Nginx + Node + Python)
# CentOS 首次环境初始化（Docker MySQL + Nginx + Node + Python）
#
# Run as root (or sudo) once / 请以 root（或 sudo）执行一次:
#   bash deploy/bootstrap-centos.sh
#
# Env overrides / 可用环境变量覆盖:
#   DEPLOY_PATH=/opt/erp_demo
#   GIT_REPO=https://github.com/ChoosenMeng/erp_demo_by_cursor.git
#   BRANCH=feature/m0-m1-scaffold
#   SERVER_IP=x.x.x.x

set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/erp_demo}"
GIT_REPO="${GIT_REPO:-https://github.com/ChoosenMeng/erp_demo_by_cursor.git}"
BRANCH="${BRANCH:-feature/m0-m1-scaffold}"
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
    log "Installing Docker Engine / 安装 Docker Engine"
    # Official convenience script works on many CentOS / Stream versions
    # 官方便捷脚本兼容多数 CentOS / Stream
    curl -fsSL https://get.docker.com | sh
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

install_python() {
  if command -v python3.13 >/dev/null 2>&1 || command -v python3.12 >/dev/null 2>&1; then
    log "Python 3.12+ already present / 已有 Python 3.12+"
    return 0
  fi

  log "Installing Miniconda (Python 3.13) / 安装 Miniconda（Python 3.13）"
  local installer="/tmp/Miniconda3.sh"
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "$installer"
  bash "$installer" -b -p /opt/miniconda3
  # shellcheck disable=SC1091
  source /opt/miniconda3/etc/profile.d/conda.sh
  conda create -y -n cursor-erp-demo python=3.13 pip
  ln -sfn /opt/miniconda3/envs/cursor-erp-demo/bin/python /usr/local/bin/python3.13
  ln -sfn /opt/miniconda3/envs/cursor-erp-demo/bin/pip /usr/local/bin/pip3.13
  python3.13 --version
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
  # Avoid conflicting default site if present / 避免与默认站点冲突
  if [[ -f /etc/nginx/conf.d/default.conf ]]; then
    mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak || true
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
  install_python
  clone_repo
  prepare_env_files
  install_systemd_nginx
  open_firewall

  chmod +x "$DEPLOY_PATH/deploy/deploy.sh"
  log "Bootstrap done. Next: / 初始化完成。下一步："
  log "  1) Edit $DEPLOY_PATH/deploy/.env and $DEPLOY_PATH/backend/.env"
  log "  2) DEPLOY_PATH=$DEPLOY_PATH bash $DEPLOY_PATH/deploy/deploy.sh"
  log "  3) sudo systemctl enable --now erp-api"
}

main "$@"
