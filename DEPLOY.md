# Deploy Guide

This guide describes the production setup used by the live demo:

- Ubuntu 22.04
- Docker Compose for `frontend`, `backend`, and `postgres`
- Host Nginx for HTTPS and reverse proxy
- Certbot for Let's Encrypt certificates

## 1. DNS

Create these DNS records:

- `A` record: `@` -> your server public IP
- `A` record: `www` -> your server public IP

## 2. Install Docker

The official Docker installation script is the quickest route on a fresh server:

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
docker --version
docker compose version
```

## 3. Clone Repository

```bash
git clone https://github.com/missrosery/resume-screening-agent.git
cd resume-screening-agent
```

## 4. Prepare Environment Files

```bash
cp .env.production.example .env.production
cp backend/.env.production.example backend/.env
```

Edit `.env.production`:

```env
POSTGRES_DB=resume_screener
POSTGRES_USER=resume_user
POSTGRES_PASSWORD=replace_with_a_strong_password
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://resume_user:replace_with_a_strong_password@postgres:5432/resume_screener
SYNC_DATABASE_URL=postgresql+psycopg://resume_user:replace_with_a_strong_password@postgres:5432/resume_screener
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
UPLOAD_DIR=/app/uploads
CORS_ORIGINS=https://hx-code.xyz,https://www.hx-code.xyz
VECTOR_COLLECTION_NAME=resume_documents
VECTOR_RECALL_K=15
RERANK_TOP_N=5
AGENT_MAX_STEPS=4
```

Use your own domain in `CORS_ORIGINS`.

## 5. Start Containers

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

The production compose file binds the app to localhost only:

- frontend: `127.0.0.1:3000`
- backend: `127.0.0.1:8000`
- postgres: Docker network only

## 6. Install Host Nginx and Certbot

```bash
apt update
apt install -y nginx certbot python3-certbot-nginx
```

Before requesting HTTPS, make sure ports `80` and `443` are open in the cloud firewall.

## 7. Request HTTPS Certificate

```bash
certbot --nginx -d hx-code.xyz -d www.hx-code.xyz
```

Use your own domain names in the command.

## 8. Configure Host Nginx

Use `deploy/nginx/default.conf` as the reference config. On the server:

```bash
nano /etc/nginx/sites-available/default
nginx -t
nginx -s reload
```

If Nginx is managed cleanly by systemd, this also works:

```bash
systemctl reload nginx
```

## 9. Verify

```bash
curl -I https://hx-code.xyz
curl https://hx-code.xyz/api/health
```

Expected API response:

```json
{"status":"ok"}
```

Then verify the main workflow in the browser:

- create a position
- upload resumes
- screen candidates
- compare candidates
- generate interview questions
- use the Agent chat

## 10. Update Deployment

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build --remove-orphans
nginx -t
nginx -s reload
```
