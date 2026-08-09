# ERP Demo — Self-hosted deploy (CentOS + GitHub Actions SSH)

# ERP Demo — 自有服务器部署（CentOS + GitHub Actions SSH）

Target layout / 目标形态：

- Nginx `:80` → `frontend/dist` + reverse proxy `/api`
- systemd `erp-api` → uvicorn on `127.0.0.1:8000`
- Docker → MySQL 8 only（仅数据库容器）
- Python → **uv** + project `.venv`（不再用 Miniconda，适合约 1GiB 小内存 VPS）

Access by **IP over HTTP** (certificates are usually for domains; HTTPS can be added later).  
用 **IP + HTTP** 访问（证书一般绑域名；HTTPS 可后续再加）。

### Low-RAM tip / 小内存提示

If the host has ~1GiB RAM, add **2GiB swap** before first build (does **not** create a separate Alibaba Cloud bill item; it only uses disk space):

约 1GiB 内存主机建议先加 **2GiB swap** 再首次构建（**不会**单独产生阿里云 Swap 费用，只占用云盘空间）：

```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
free -h
```

Skip Miniconda on these hosts — use bootstrap/`uv` instead.  
此类主机请跳过 Miniconda，改用 bootstrap / `uv`。

**Frontend build / 前端构建：** `deploy.sh` runs `npx vite build` (skips `vue-tsc`) with `NODE_OPTIONS=--max-old-space-size=384`. Full typecheck stays on local/CI via `npm run build`.  
**前端构建：** `deploy.sh` 使用 `npx vite build`（跳过 `vue-tsc`），并设置 `NODE_OPTIONS=--max-old-space-size=384`。完整类型检查仍在本地/CI 用 `npm run build`。

**Demo seed / 演示种子数据：** After `alembic upgrade head`, `deploy.sh` runs `python -m app.scripts.seed` by default (idempotent; safe for demo VPS). Set `SKIP_SEED=1` to skip.  
**演示种子数据：** `alembic upgrade head` 之后默认执行 `python -m app.scripts.seed`（幂等，适合演示 VPS）。设 `SKIP_SEED=1` 可跳过。

If a previous `npm run build` is hung / 若旧的 `npm run build` 已卡住：

```bash
# Ctrl+C the hung deploy, then free memory / 先 Ctrl+C 卡住的部署，再腾内存
free -h
pkill -f 'vue-tsc|vite|node' || true   # only if safe / 确认无其他关键 Node 任务后再杀
cd /opt/erp_demo && sudo git pull   # or re-run deploy which pulls BRANCH
sudo DEPLOY_PATH=/opt/erp_demo BRANCH=main bash /opt/erp_demo/deploy/deploy.sh
# Manual frontend only / 仅手动构建前端:
# cd /opt/erp_demo/frontend && NODE_OPTIONS=--max-old-space-size=384 npx vite build
```

---

## 0. Files in this folder / 本目录文件

| File | Purpose |
| --- | --- |
| `bootstrap-centos.sh` | First-time setup (Docker/Nginx/Node/**uv**) / 首次初始化 |
| `deploy.sh` | Pull + uv/pip + build + migrate + **seed** + restart / 拉取编译迁移种子重启 |
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
export BRANCH=main
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
sudo DEPLOY_PATH=/opt/erp_demo BRANCH=main \
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
| `DEPLOY_BRANCH` | `main`（默认） | optional |

SSH key tips / SSH 密钥建议：

1. On your PC generate a **deploy-only** key (no passphrase for Actions):  
   `ssh-keygen -t ed25519 -C "erp-deploy" -f erp-deploy -N ""`
2. Append `erp-deploy.pub` to server `~/.ssh/authorized_keys`
3. Put **private** key content into `SSH_PRIVATE_KEY` secret
4. Test: `ssh -i erp-deploy -p 51822 USER@HOST`

If `SSH_USER` is not root, ensure it can run `systemctl` / docker（或改脚本用 sudo）。

---

## 3. Trigger deploy / 触发部署

After secrets + first bootstrap are done / 配置好 Secrets 且完成首次 bootstrap 后：

1. **自动**：push / merge 到 **`main`** 即触发生产部署  
2. **手动**：Actions → **Deploy to Server** → **Run workflow**（任意分支可用，含 feature）

Pipeline will SSH in and run `deploy/deploy.sh`.  
流水线会 SSH 到服务器执行 `deploy/deploy.sh`（默认拉 `main`；可用 Secret `DEPLOY_BRANCH` 覆盖）。

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


### MYSQL_USER=root container crash / MYSQL_USER=root 导致容器失败

Official `mysql:8` image: `MYSQL_ROOT_PASSWORD` is for **root**; `MYSQL_USER` + `MYSQL_PASSWORD` create a **non-root** app user.  
官方 `mysql:8`：`MYSQL_ROOT_PASSWORD` 给 **root**；`MYSQL_USER` + `MYSQL_PASSWORD` 创建 **非 root** 应用用户。

If logs show / 若日志出现：

`MYSQL_USER and MYSQL_PASSWORD are for configuring a regular user and cannot be used for the root user`

Fix on the server (do **not** paste passwords into chat) / 服务器上修复（**不要**把密码贴到聊天里）：

```bash
# 1) Edit deploy/.env — MYSQL_USER must be erp_admin (NOT root)
#    编辑 deploy/.env：MYSQL_USER 必须是 erp_admin（不能是 root）
sudo nano /opt/erp_demo/deploy/.env
# MYSQL_USER=erp_admin
# MYSQL_ROOT_PASSWORD=root
# MYSQL_PASSWORD=erp_admin

# 2) Align backend DATABASE_URL to the same erp_admin user/password
#    让 backend DATABASE_URL 与 erp_admin 用户/密码一致
sudo nano /opt/erp_demo/backend/.env
# DATABASE_URL=mysql+pymysql://erp_admin:erp_admin@127.0.0.1:3306/erp_demo?charset=utf8mb4

# 3) Recreate MySQL volume (only if data can be discarded) / 可丢数据时重建卷
cd /opt/erp_demo
docker compose -f deploy/docker-compose.yml --env-file deploy/.env down -v
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d

# 4) Re-run deploy / 重新部署
sudo DEPLOY_PATH=/opt/erp_demo BRANCH=main \
  bash /opt/erp_demo/deploy/deploy.sh
```

`deploy.sh` now refuses `MYSQL_USER=root` or empty before `compose up`.  
`deploy.sh` 在 `compose up` 前会拒绝 `MYSQL_USER=root` 或空值。

### MySQL timeout on small VPS / 小内存 VPS 上 MySQL 超时

`deploy.sh` waits ~5 minutes for MySQL. On ~1GiB RAM hosts, first `mysql:8` boot (InnoDB init) is slow and may need swap.  
`deploy.sh` 会等待约 5 分钟。约 1GiB 内存主机上，MySQL 8 **首次**启动（InnoDB 初始化）很慢，务必先有 swap。

If you see `MySQL did not become ready in time` / 若出现超时：

```bash
# 1) Container & memory / 容器与内存
docker ps -a --filter name=erp-mysql
docker logs --tail 80 erp-mysql
free -h

# 2) Password mismatch after changing deploy/.env /
#    改过 .env 密码但数据卷仍是旧密码时 ping 会失败（可丢数据才重建）:
cd /opt/erp_demo
docker compose -f deploy/docker-compose.yml --env-file deploy/.env down
docker volume rm erp_demo_erp_mysql_data   # name may vary: docker volume ls | grep mysql
# 卷名可能不同：docker volume ls | grep mysql
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d

# 3) Re-run deploy / 重新部署
sudo DEPLOY_PATH=/opt/erp_demo BRANCH=main \
  bash /opt/erp_demo/deploy/deploy.sh
```

Align `deploy/.env` `MYSQL_*` with `backend/.env` `DATABASE_URL` before recreate.  
重建前请让 `deploy/.env` 的 `MYSQL_*` 与 `backend/.env` 的 `DATABASE_URL` 一致。

### Nginx: `duplicate default server` / 重复 default_server

On CentOS, stock `/etc/nginx/nginx.conf` often already has `listen ... default_server` on `:80`.  
If `erp_demo.conf` also used `default_server`, `nginx -t` fails with:

CentOS 自带 `/etc/nginx/nginx.conf` 常在 `:80` 已有 `default_server`。  
若 `erp_demo.conf` 也写了 `default_server`，`nginx -t` 会报：

`nginx: [emerg] a duplicate default server for 0.0.0.0:80`

Fix on the server / 服务器上快速修复：

```bash
# 1) Remove default_server from ERP site / 从 ERP 站点配置去掉 default_server
sudo sed -i -E 's/ default_server//g' /etc/nginx/conf.d/erp_demo.conf

# 2) Also strip it from main nginx.conf listen lines / 主配置 listen 行同样去掉
sudo cp -a /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
sudo sed -i -E '/listen/s/[[:space:]]+default_server//g' /etc/nginx/nginx.conf

sudo nginx -t && sudo systemctl reload nginx
```

Current `nginx.conf.example` no longer sets `default_server`; bootstrap also neutralizes the stock one.  
当前示例配置已不再使用 `default_server`；bootstrap 也会中和系统自带的。

Firewall: open **80** (and keep **51822** for SSH).  
防火墙：开放 **80**（SSH 继续用 **51822**）。

---

## 5. Security notes / 安全提示

- MySQL is bound to `127.0.0.1:3306` only / 数据库仅本机可访问  
- Change default passwords before public exposure / 公网暴露前务必改密  
- Prefer a dedicated deploy SSH key with limited rights / 建议独立部署密钥  
- Later: switch Nginx to your domain + existing TLS cert / 后续可改域名并挂已有证书  
