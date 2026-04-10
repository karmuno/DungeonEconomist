# VentureKeep — VPS Deployment Guide

From brand-new Ubuntu VPS to production instance with custom domain and HTTPS.

---

## Prerequisites

- A VPS running Ubuntu 22.04+ (DigitalOcean, Linode, Hetzner, RackNerd, etc.)
- SSH access as root (or a sudo-capable user)
- A domain name (e.g. `venturekeep.com`) purchased from any registrar
- The VentureKeep repo accessible via GitHub

---

## User Account Model

This guide uses **two accounts** with distinct roles:

| Account | Purpose | Sudo? |
|---------|---------|-------|
| **Your personal user** (e.g. `yourname`) | System administration — installing packages, configuring Nginx, managing certificates | Yes |
| **`venturekeep`** (service account) | Running the app — Docker, git, backups | No |

The `venturekeep` user never gets sudo. If the app or its environment is compromised, the attacker is confined to the service account and cannot escalate to root. System administration always goes through your personal account.

**Switching between accounts:**

```bash
# From your personal account → venturekeep (app tasks)
sudo su - venturekeep

# Back to your personal account (system tasks)
exit
```

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

Create your personal admin user (skip if your VPS provider already set one up):

```bash
adduser yourname
usermod -aG sudo yourname
```

Create the service account for the app — **no sudo**:

```bash
adduser venturekeep
```

Set up the firewall:

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
```

Log out of root and SSH back in as your personal user:

```bash
exit
ssh yourname@YOUR_SERVER_IP
```

---

## Step 2: Install Docker

Run these from **your personal account** (they need sudo):

```bash
# Docker's official install script
curl -fsSL https://get.docker.com | sudo sh

# Let the venturekeep service account run Docker
sudo usermod -aG docker venturekeep
```

Switch to venturekeep and verify (the group change takes effect on new login):

```bash
sudo su - venturekeep

docker --version
docker compose version
```

---

## Step 3: Create Docker Network and Start PostgreSQL

All remaining Docker/app commands run as the **venturekeep** service account. If you're not already switched, run `sudo su - venturekeep` from your personal account first.

Both containers must share a Docker network so they can reach each other by name. Do **not** rely on `172.17.0.1` or `host.docker.internal` — those are unreliable across Linux Docker configurations.

```bash
# Create a shared network
docker network create venturekeep-net

# Create a directory for persistent data
mkdir -p ~/venturekeep-data

# Run Postgres on the shared network
docker run -d \
  --name venturekeep-db \
  --restart unless-stopped \
  --network venturekeep-net \
  -e POSTGRES_USER=venturekeep \
  -e POSTGRES_PASSWORD=CHANGE_THIS_TO_A_REAL_PASSWORD \
  -e POSTGRES_DB=venturekeep \
  -v ~/venturekeep-data/pgdata:/var/lib/postgresql/data \
  postgres:16-alpine
```

Verify Postgres is running:

```bash
docker exec venturekeep-db pg_isready -U venturekeep
# Should print: accepting connections
```

Note: no `-p` flag needed — the app container reaches Postgres over the Docker network, not via host ports. Postgres is never exposed to the public internet.

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

This runs a multi-stage build: Node 20 compiles the Vue frontend (`vue-tsc` type-check + `vite build`), then Python 3.11 bundles everything into one image. Alembic migrations run automatically on container startup.

---

## Step 5: Configure Environment

Generate a secret key first:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Create the env file (paste your generated secret key and real DB password):

```bash
nano ~/venturekeep/.env.production
```

Contents:

```
DATABASE_URL=postgresql://venturekeep:CHANGE_THIS_TO_A_REAL_PASSWORD@venturekeep-db:5432/venturekeep
VENTUREKEEP_SECRET_KEY=PASTE_YOUR_GENERATED_KEY_HERE
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PORT=8000
```

Key points:
- The `DATABASE_URL` host is `venturekeep-db` — the container name on the shared Docker network. Not `localhost`, not `172.17.0.1`.
- Update `CORS_ORIGINS` with your actual domain (e.g. `https://yourdomain.com` or `https://game.yourdomain.com` for a subdomain). For initial testing without a domain, set it to `*`.
- The DB password here must match what you used in Step 3.

---

## Step 6: Run the App

```bash
docker run -d \
  --name venturekeep-app \
  --restart unless-stopped \
  --network venturekeep-net \
  --env-file ~/venturekeep/.env.production \
  -p 127.0.0.1:8000:8000 \
  venturekeep:latest
```

Wait a few seconds for migrations, then verify:

```bash
# Check container is running (not restarting)
docker ps --filter name=venturekeep-app

# Check logs — should show Alembic migrations then Uvicorn startup
docker logs venturekeep-app

# Test the app responds
curl http://localhost:8000/
# Should return HTML
```

If `docker ps` shows the container was created a while ago but "Up" for only a few seconds, it's crash-looping. Check `docker logs venturekeep-app` for the error.

**Common issues at this stage:**

- **"Connection timed out" to database**: The app container isn't on the `venturekeep-net` network, or the `DATABASE_URL` host isn't `venturekeep-db`. Verify with: `docker network inspect venturekeep-net --format '{{range .Containers}}{{.Name}} {{end}}'` — both containers should be listed.
- **Alembic migration error (enum types)**: Postgres has strict enum types unlike SQLite. If a migration fails with `invalid input value for enum`, the migration needs fixing upstream — check the repo for updates.

---

## Step 7: Install Nginx as Reverse Proxy

Switch back to **your personal account** for system administration (`exit` from venturekeep, or open a new SSH session).

Install nginx if it isn't already running:

```bash
sudo apt install -y nginx
```

Create the HTTP config (redirects to HTTPS):

```bash
sudo tee /etc/nginx/conf.d/venturekeep.yourdomain.com.conf << 'EOF'
server {
    listen 80;
    server_name venturekeep.yourdomain.com;

    location ~ /\.(?!well-known\/) {
        deny all;
        return 404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF
```

Create the HTTPS config (proxies to your Docker container — fill in after Step 9 when you have a cert):

```bash
sudo tee /etc/nginx/conf.d/venturekeep.yourdomain.com.ssl.conf << 'EOF'
server {
    listen 443 ssl;
    server_name venturekeep.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/venturekeep.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/venturekeep.yourdomain.com/privkey.pem;

    location ~ /\.(?!well-known\/) {
        deny all;
        return 404;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
EOF
```

Test and reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Step 8: Point Your Domain to the Server

Go to your domain registrar (Namecheap, Cloudflare, GoDaddy, Porkbun, etc.) and set DNS records.

**For a root domain** (`yourdomain.com`):

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |

(Or use a CNAME for `www` → `yourdomain.com` if your registrar supports it.)

**For a subdomain** (`game.yourdomain.com`):

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | game | YOUR_SERVER_IP | 300 |

No `www` record needed for subdomains.

DNS propagation takes anywhere from 5 minutes to 48 hours. Check with:

```bash
dig yourdomain.com +short        # root domain
dig game.yourdomain.com +short   # subdomain
# Should return YOUR_SERVER_IP
```

Wait until this resolves before proceeding to the next step.

---

## Step 9: Enable HTTPS with Let's Encrypt

Run from **your personal account** (needs sudo):

```bash
sudo apt install -y certbot

# For a subdomain like venturekeep.yourdomain.com:
sudo certbot certonly --webroot -w /var/www/html -d venturekeep.yourdomain.com
```

`certonly` obtains the certificate without modifying your nginx config (you've already written that in Step 7). The `-w` flag points to a directory nginx can serve for the HTTP challenge — `/var/www/html` is the default.

Certbot sets up auto-renewal via a systemd timer. Verify it works:

```bash
sudo certbot renew --dry-run
```

Now go back and create the HTTPS config from Step 7 (or if you already created it, reload nginx):

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Your site is now live at `https://venturekeep.yourdomain.com`.

---

## Step 10: Verify Everything

```bash
# App container running?
docker ps

# Postgres healthy?
docker exec venturekeep-db pg_isready -U venturekeep

# Both containers on the network?
docker network inspect venturekeep-net --format '{{range .Containers}}{{.Name}} {{end}}'

# Nginx serving?
curl -I https://yourdomain.com

# Check app logs
docker logs --tail 50 venturekeep-app
```

---

## Updating the App

When you push new code, switch to the venturekeep account (`sudo su - venturekeep`):

```bash
cd ~/venturekeep
git pull origin main
docker build -t venturekeep:latest .
docker stop venturekeep-app && docker rm venturekeep-app
docker run -d \
  --name venturekeep-app \
  --restart unless-stopped \
  --network venturekeep-net \
  --env-file ~/venturekeep/.env.production \
  -p 127.0.0.1:8000:8000 \
  venturekeep:latest
```

Migrations run automatically on container start. Downtime is ~10 seconds.

---

## Database Backups

Set up a daily cron job as the **venturekeep** user (`sudo su - venturekeep`):

```bash
mkdir -p ~/venturekeep-data/backups

crontab -e
# Add these lines:
0 3 * * * docker exec venturekeep-db pg_dump -U venturekeep venturekeep | gzip > ~/venturekeep-data/backups/venturekeep-$(date +\%Y\%m\%d).sql.gz
0 4 * * * find ~/venturekeep-data/backups -name "*.sql.gz" -mtime +30 -delete
```

To restore from a backup:

```bash
gunzip -c ~/venturekeep-data/backups/venturekeep-20260326.sql.gz | \
  docker exec -i venturekeep-db psql -U venturekeep venturekeep
```

---

## Troubleshooting

**Container crash-looping (created X ago, up for Y seconds):** Run `docker logs venturekeep-app` — the error is usually a database connection failure or migration error.

**"Connection timed out" / "Connection refused" to database:** The containers aren't on the same Docker network. Verify both are on `venturekeep-net`: `docker network inspect venturekeep-net`. The DATABASE_URL host must be `venturekeep-db` (the container name), not `localhost` or `172.17.0.1`.

**502 Bad Gateway from Nginx:** The app container isn't running or isn't bound to port 8000. Check `docker ps` and `docker logs venturekeep-app`.

**Certbot fails:** DNS hasn't propagated yet. Wait and retry. Check with `dig yourdomain.com`.

**Alembic migration fails:** Check `docker logs venturekeep-app` for the specific error. Postgres enum types are stricter than SQLite — migrations that work locally may need fixes for production. To retry migrations after a code fix: rebuild the image and restart the container.

**Empty `docker logs` output:** The container may be restarting too fast. Use `docker logs -f venturekeep-app` to follow in real time, or `docker run --rm -it --network venturekeep-net --env-file ~/venturekeep/.env.production venturekeep:latest bash` to get a shell inside the image and debug manually.
