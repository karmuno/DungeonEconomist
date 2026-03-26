# VentureKeep — VPS Deployment Guide

From brand-new Ubuntu VPS to production instance with custom domain and HTTPS.

---

## Prerequisites

- A VPS running Ubuntu 22.04+ (DigitalOcean, Linode, Hetzner, etc.)
- SSH access as root (or a sudo-capable user)
- A domain name (e.g. `venturekeep.com`) purchased from any registrar
- The VentureKeep repo cloned locally or accessible via GitHub

---

## Step 1: Initial Server Setup

SSH into your VPS:

```bash
ssh root@YOUR_SERVER_IP
```

Update packages and install essentials:

```bash
apt update && apt upgrade -y
apt install -y curl git ufw fail2ban
```

Create a non-root user:

```bash
adduser venturekeep
usermod -aG sudo venturekeep
```

Set up the firewall:

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
```

Switch to the new user for all remaining steps:

```bash
su - venturekeep
```

---

## Step 2: Install Docker

```bash
# Docker's official install script
curl -fsSL https://get.docker.com | sudo sh

# Let your user run Docker without sudo
sudo usermod -aG docker venturekeep

# Log out and back in for the group change to take effect
exit
su - venturekeep

# Verify
docker --version
docker compose version
```

---

## Step 3: Install and Configure PostgreSQL

You can use Dockerized Postgres or a managed database. Dockerized is simpler for a single VPS:

```bash
# Create a directory for persistent data
mkdir -p ~/venturekeep-data

# Run Postgres
docker run -d \
  --name venturekeep-db \
  --restart unless-stopped \
  -e POSTGRES_USER=venturekeep \
  -e POSTGRES_PASSWORD=CHANGE_THIS_TO_A_REAL_PASSWORD \
  -e POSTGRES_DB=venturekeep \
  -v ~/venturekeep-data/pgdata:/var/lib/postgresql/data \
  -p 127.0.0.1:5432:5432 \
  postgres:16-alpine
```

Note: binding to `127.0.0.1` keeps Postgres off the public internet.

---

## Step 4: Clone and Build the App

```bash
cd ~
git clone https://github.com/karmuno/DungeonEconomist.git venturekeep
cd venturekeep
```

Build the Docker image:

```bash
docker build -t venturekeep:latest .
```

This runs a multi-stage build: Node 20 compiles the Vue frontend, then Python 3.11 bundles everything into one image. Alembic migrations run automatically on startup.

---

## Step 5: Configure Environment

Create the env file:

```bash
cat > ~/venturekeep/.env.production << 'EOF'
DATABASE_URL=postgresql://venturekeep:CHANGE_THIS_TO_A_REAL_PASSWORD@host.docker.internal:5432/venturekeep
VENTUREKEEP_SECRET_KEY=GENERATE_ME
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PORT=8000
EOF
```

Generate a real secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Paste the output into the `.env.production` file, replacing `GENERATE_ME`.

Update `CORS_ORIGINS` with your actual domain.

**Note on Docker networking:** If Postgres runs as a separate container (not in the same compose network), use the host's IP. On Linux with default Docker, use `172.17.0.1` instead of `host.docker.internal`:

```
DATABASE_URL=postgresql://venturekeep:PASSWORD@172.17.0.1:5432/venturekeep
```

---

## Step 6: Run the App

```bash
docker run -d \
  --name venturekeep-app \
  --restart unless-stopped \
  --env-file ~/venturekeep/.env.production \
  -p 127.0.0.1:8000:8000 \
  venturekeep:latest
```

Verify it started:

```bash
docker logs venturekeep-app
# Should show Alembic migrations running, then Uvicorn starting
```

Test locally:

```bash
curl http://localhost:8000/
# Should return HTML
```

---

## Step 7: Install Nginx as Reverse Proxy

```bash
sudo apt install -y nginx
```

Create the site config:

```bash
sudo tee /etc/nginx/sites-available/venturekeep << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP to HTTPS (Certbot will handle this after Step 9,
    # but we need a working HTTP config first for the ACME challenge)

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed later)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/venturekeep /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 8: Point Your Domain to the Server

Go to your domain registrar (Namecheap, Cloudflare, GoDaddy, Porkbun, etc.) and set DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |

If your registrar offers it, you can also use a CNAME for `www`:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| CNAME | www | yourdomain.com | 300 |

DNS propagation takes anywhere from 5 minutes to 48 hours. Check with:

```bash
dig yourdomain.com +short
# Should return YOUR_SERVER_IP
```

Wait until this resolves before proceeding to the next step.

---

## Step 9: Enable HTTPS with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx

sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will:
1. Verify you own the domain via HTTP challenge
2. Obtain a free TLS certificate
3. Automatically modify your Nginx config to redirect HTTP → HTTPS
4. Set up auto-renewal (runs via systemd timer)

Verify auto-renewal works:

```bash
sudo certbot renew --dry-run
```

Your site is now live at `https://yourdomain.com`.

---

## Step 10: Verify Everything

```bash
# App container running?
docker ps

# Postgres healthy?
docker exec venturekeep-db pg_isready -U venturekeep

# Nginx serving?
curl -I https://yourdomain.com

# Check app logs
docker logs --tail 50 venturekeep-app
```

---

## Updating the App

When you push new code:

```bash
cd ~/venturekeep
git pull origin main
docker build -t venturekeep:latest .
docker stop venturekeep-app && docker rm venturekeep-app
docker run -d \
  --name venturekeep-app \
  --restart unless-stopped \
  --env-file ~/venturekeep/.env.production \
  -p 127.0.0.1:8000:8000 \
  venturekeep:latest
```

Migrations run automatically on container start. Downtime is ~10 seconds.

---

## Database Backups

Set up a daily cron job:

```bash
mkdir -p ~/venturekeep-data/backups

crontab -e
# Add this line:
0 3 * * * docker exec venturekeep-db pg_dump -U venturekeep venturekeep | gzip > ~/venturekeep-data/backups/venturekeep-$(date +\%Y\%m\%d).sql.gz

# Clean up backups older than 30 days:
0 4 * * * find ~/venturekeep-data/backups -name "*.sql.gz" -mtime +30 -delete
```

To restore from a backup:

```bash
gunzip -c ~/venturekeep-data/backups/venturekeep-20260326.sql.gz | \
  docker exec -i venturekeep-db psql -U venturekeep venturekeep
```

---

## Troubleshooting

**App won't start:** Check `docker logs venturekeep-app`. Usually a bad `DATABASE_URL`.

**502 Bad Gateway:** Nginx can't reach the app. Check `docker ps` — is the container running? Check it's bound to port 8000.

**Certbot fails:** DNS hasn't propagated yet. Wait and retry. Check `dig yourdomain.com`.

**Database connection refused:** Make sure Postgres is running and the `DATABASE_URL` host is correct (`172.17.0.1` on Linux, not `localhost` — the app container can't reach the host's loopback).

**Migrations fail:** Check `docker logs venturekeep-app` for the Alembic error. You may need to run migrations manually: `docker exec venturekeep-app alembic upgrade head`.
