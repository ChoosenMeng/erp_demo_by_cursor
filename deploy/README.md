# ERP Demo — Self-hosted deploy (CentOS + GitHub Actions SSH)

# ERP Demo — 自有服务器部署（CentOS + GitHub Actions SSH）

Target layout / 目标形态：

- Nginx `:80` → `frontend/dist` + reverse proxy `/api`
- systemd `erp-api` → uvicorn on `127.0.0.1:8000`
- Docker → MySQL 8 only（仅数据库容器）

Access by **IP over HTTP** (certificates are usually for domains; HTTPS can be added later).  
用 **IP + HTTP** 访问（证书一般绑域名；HTTPS 可后续再加）。

---

## 0. Files in this folder / 本目录文件

| File | Purpose |
| --- | --- |
| `bootstrap-centos.sh` | First-time server setup / 服务器首次初始化 |
| `deploy.sh` | Pull + build + migrate + restart / 拉取编译迁移重启 |
| `docker-compose.yml` | MySQL container / MySQL 容器 |
| `.env.example` | MySQL passwords template / MySQL 密码模板 |
| `backend.env.production.example` | Backend `.env` template / 后端环境模板 |
| `erp-api.service` | systemd unit |
| `nginx.conf.example` | Nginx site config |

Workflow: `../.github/workflows/deploy.yml`

---

## 1. One-time on the server / 服务器首次操作

SSH（端口 **51822**）：

```bash
ssh -p 51822 YOUR_USER@YOUR_SERVER_IP
```

Upload or curl the bootstrap script after the repo exists, or clone manually then run:

```bash
# Example / 示例
export DEPLOY_PATH=/opt/erp_demo
export BRANCH=feature/m0-m1-scaffold
export SERVER_IP=YOUR_SERVER_IP
export GIT_REPO=https://github.com/ChoosenMeng/erp_demo_by_cursor.git

# If repo not cloned yet, you can copy bootstrap from a machine that has the files,
# or clone first:
# sudo git clone -b "$BRANCH" "$GIT_REPO" "$DEPLOY_PATH"

sudo SERVER_IP="$SERVER_IP" DEPLOY_PATH="$DEPLOY_PATH" BRANCH="$BRANCH" \
  bash "$DEPLOY_PATH/deploy/bootstrap-centos.sh"
```

Then edit secrets on the server（**不要提交到 Git**）：

```bash
sudo nano /opt/erp_demo/deploy/.env
sudo nano /opt/erp_demo/backend/.env
# Align MYSQL_* passwords with DATABASE_URL
# 让 MYSQL_* 密码与 DATABASE_URL 一致
# Set a strong SECRET_KEY / 设置强 SECRET_KEY
# CORS_ORIGINS=http://YOUR_SERVER_IP
```

First deploy:

```bash
sudo DEPLOY_PATH=/opt/erp_demo BRANCH=feature/m0-m1-scaffold \
  bash /opt/erp_demo/deploy/deploy.sh
sudo systemctl enable --now erp-api
sudo systemctl status erp-api --no-pager
```

Open: `http://YOUR_SERVER_IP/`  
API docs: `http://YOUR_SERVER_IP/docs`

---

## 2. GitHub Secrets / GitHub 仓库 Secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Example | Required |
| --- | --- | --- |
| `SSH_HOST` | `1.2.3.4` | yes |
| `SSH_USER` | `root` or your sudo user | yes |
| `SSH_PORT` | `51822` | yes |
| `SSH_PRIVATE_KEY` | full private key PEM | yes |
| `DEPLOY_PATH` | `/opt/erp_demo` | optional |
| `DEPLOY_BRANCH` | `feature/m0-m1-scaffold` | optional |

SSH key tips / SSH 密钥建议：

1. On your PC generate a **deploy-only** key (no passphrase for Actions):  
   `ssh-keygen -t ed25519 -C "erp-deploy" -f erp-deploy -N ""`
2. Append `erp-deploy.pub` to server `~/.ssh/authorized_keys`
3. Put **private** key content into `SSH_PRIVATE_KEY` secret
4. Test: `ssh -i erp-deploy -p 51822 USER@HOST`

If `SSH_USER` is not root, ensure it can run `systemctl` / docker（或改脚本用 sudo）。

---

## 3. Trigger deploy / 触发部署

After secrets + first bootstrap are done:

1. Push to `feature/m0-m1-scaffold` or `main`，或  
2. Actions → **Deploy to Server** → **Run workflow**

Pipeline will SSH in and run `deploy/deploy.sh`.

---

## 4. Common checks / 常见排查

```bash
docker ps | grep erp-mysql
systemctl status erp-api --no-pager
journalctl -u erp-api -n 100 --no-pager
nginx -t
curl -s http://127.0.0.1:8000/api/v1/health
curl -s http://YOUR_SERVER_IP/api/v1/health
```

Firewall: open **80** (and keep **51822** for SSH).  
防火墙：开放 **80**（SSH 继续用 **51822**）。

---

## 5. Security notes / 安全提示

- MySQL is bound to `127.0.0.1:3306` only / 数据库仅本机可访问  
- Change default passwords before public exposure / 公网暴露前务必改密  
- Prefer a dedicated deploy SSH key with limited rights / 建议独立部署密钥  
- Later: switch Nginx to your domain + existing TLS cert / 后续可改域名并挂已有证书  
