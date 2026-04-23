# Deploy Guide

This guide uses:

- Ubuntu 22.04
- Docker + Docker Compose
- Nginx reverse proxy
- A single server deployment

## 1. DNS

Create these DNS records for your domain:

- `A` record: `@` -> your server public IP
- `A` record: `www` -> your server public IP

## 2. Server packages

```bash
apt update
apt install -y docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker
```

## 3. Clone repository

```bash
git clone https://github.com/missrosery/resume-screening-agent.git
cd resume-screening-agent
```

## 4. Prepare environment files

```bash
cp .env.production.example .env.production
cp backend/.env.production.example backend/.env
```

Edit:

- `.env.production`
- `backend/.env`

## 5. Start containers

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

## 6. Check logs

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f backend
```

## 7. HTTPS

After DNS is effective and port 80 is reachable, install certbot and configure HTTPS on the host.

Typical next step:

```bash
apt install -y certbot
```

You can later terminate HTTPS either:

- directly on the host with Nginx + Certbot
- or inside a separate reverse proxy setup
