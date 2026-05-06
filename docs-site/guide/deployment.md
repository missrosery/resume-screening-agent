# 部署运维

生产环境建议使用 Docker Compose 管理 `frontend`、`backend` 和 `postgres`，宿主机 Nginx 负责 HTTPS 和反向代理。

## 部署拓扑

```text
Browser
  |
  v
Host Nginx (HTTPS)
  |-- /      -> frontend:3000
  |-- /api   -> backend:8000

Docker Compose Network
  |-- frontend
  |-- backend
  |-- postgres + pgvector
```

## 准备环境文件

```bash
cp .env.production.example .env.production
cp backend/.env.production.example backend/.env
```

`.env.production` 用于 PostgreSQL 容器：

```ini
POSTGRES_DB=resume_screener
POSTGRES_USER=resume_user
POSTGRES_PASSWORD=replace_with_a_strong_password
```

`backend/.env` 用于 FastAPI 后端：

```ini
DATABASE_URL=postgresql+asyncpg://resume_user:password@postgres:5432/resume_screener
SYNC_DATABASE_URL=postgresql+psycopg://resume_user:password@postgres:5432/resume_screener
DASHSCOPE_API_KEY=your_dashscope_api_key
UPLOAD_DIR=/app/uploads
CORS_ORIGINS=https://your-domain.com
```

## 启动容器

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

生产 compose 会把服务绑定到宿主机本地端口：

- `frontend`: `127.0.0.1:3000`
- `backend`: `127.0.0.1:8000`
- `postgres`: Docker 内部网络

## Nginx

宿主机 Nginx 负责对外暴露域名和 HTTPS。配置可参考仓库的 `deploy/nginx/default.conf`。

更新配置后检查并 reload：

```bash
nginx -t
systemctl reload nginx
```

## 更新线上版本

```bash
git pull origin main
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build --remove-orphans
nginx -t
systemctl reload nginx
```

## 部署后验证

```bash
curl -I https://your-domain.com
curl https://your-domain.com/api/health
```

然后在浏览器里验证：

- 创建岗位
- 上传简历
- 筛选候选人
- 多人对比
- 生成面试题
- Agent 对话
