# Deployment (native VPS, no Docker)

A from-scratch deployment on a single Ubuntu/Debian VPS: systemd-managed uvicorn, Nginx as the
TLS-terminating reverse proxy and static-file server, native PostgreSQL, and the MCP server
spawned on demand rather than run as its own service. Nothing here requires Docker - see
`docs/local-development.md` for the equivalent native local setup, and the root `README.md` for
why Docker was never made a prerequisite. An optional Docker packaging is out of scope for this
pass (Optional-tier per the project plan); everything below works without it.

This is a template, not a script: every `<PLACEHOLDER>` in the files under
`infrastructure/deploy/` needs a real value for your VPS before use. Read it end to end once
before running anything - a few steps (creating the systemd user, the database role) are
one-time and easy to get wrong in the wrong order.

## 1. Provision the VPS

- Ubuntu 22.04+ or Debian 12+, a non-root user with `sudo`, a domain name pointed at the VPS's IP
  (an A/AAAA record - required for Let's Encrypt).
- Open only 22 (SSH), 80, and 443 in the firewall. The backend listens on `127.0.0.1:8000` only -
  never expose it directly to the internet; Nginx is the only public entry point to the app.

```bash
sudo apt update && sudo apt install -y postgresql postgresql-contrib nginx git curl build-essential
curl -LsSf https://astral.sh/uv/install.sh | sh          # uv (pins Python for you)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
sudo apt install -y certbot python3-certbot-nginx
```

## 2. Create a dedicated deploy user and database role

Run the app as its own unprivileged user, never as `root` and never as your personal login.

```bash
sudo adduser --system --group --home /opt/copilot <DEPLOY_USER>
sudo -u postgres createuser <DEPLOY_USER>  # or a separate DB role name - your choice
sudo -u postgres createdb -O <DEPLOY_USER> copilot_prod
sudo -u postgres psql -c "ALTER USER <DEPLOY_USER> WITH PASSWORD '<STRONG_GENERATED_PASSWORD>';"
```

## 3. Clone, build, and configure

```bash
sudo -u <DEPLOY_USER> git clone <YOUR_REPO_URL> /opt/copilot/app
cd /opt/copilot/app
sudo -u <DEPLOY_USER> uv sync                 # installs every workspace package into .venv
sudo -u <DEPLOY_USER> cp .env.example .env    # then edit .env - see below
```

Fill in `.env` (mode `600`, owned by `<DEPLOY_USER>`, **never committed** - see `.gitignore`):

- `DATABASE_URL` / `TEST_DATABASE_URL` — point at `copilot_prod` (a prod deployment does not run
  its test suite against itself; set `TEST_DATABASE_URL` to a throwaway value or leave the
  variable present but unused).
- `JWT_SECRET_KEY` — `python -c "import secrets; print(secrets.token_urlsafe(48))"`. A fresh value
  per environment; rotating it invalidates every issued token.
- `CORS_ALLOWED_ORIGINS` — same-origin deployment (Nginx serves both the SPA and `/api/`, per
  `infrastructure/deploy/nginx.conf`) means the browser never makes a cross-origin request, so
  this can stay at its default; only change it if the frontend is ever hosted on a different
  origin from the API.
- `HF_TOKEN`, `HF_MODEL`, `URLHAUS_AUTH_KEY` — optional; see `docs/local-development.md`.

Build the ML model artifact, apply migrations, and build the frontend:

```bash
sudo -u <DEPLOY_USER> uv run copilot-ml data build
sudo -u <DEPLOY_USER> uv run copilot-ml train
cd backend && sudo -u <DEPLOY_USER> uv run alembic upgrade head && cd ..
cd frontend && sudo -u <DEPLOY_USER> npm install && sudo -u <DEPLOY_USER> npm run build && cd ..
```

`frontend/dist` is what Nginx serves as static files - rebuild and it takes effect immediately,
no service restart needed for frontend-only changes.

## 4. systemd service (backend)

```bash
sudo cp infrastructure/deploy/copilot-backend.service /etc/systemd/system/
sudo $EDITOR /etc/systemd/system/copilot-backend.service   # fill in every <PLACEHOLDER>
sudo systemctl daemon-reload
sudo systemctl enable --now copilot-backend
sudo systemctl status copilot-backend                      # should be active (running)
journalctl -u copilot-backend -f                            # tail logs
```

Read the comments in the unit file about `--workers 1`: the in-memory rate limiter and the
knowledge base's local-mode Qdrant index are both single-process by design (see ADR-0002 and the
plan's "Redis: Optional" decision) - a second uvicorn worker would either not share rate-limit
state or fail to start outright. Scale by adding a second VPS behind a load balancer if this ever
becomes a real constraint, not by raising `--workers`.

The MCP server needs no systemd unit: `mode=deep` analyses spawn `copilot-mcp` as a short-lived
stdio subprocess per request and it exits when the analysis finishes (ADR-0005). Nothing to keep
running, restart, or monitor separately.

## 5. Nginx + TLS

```bash
sudo cp infrastructure/deploy/nginx.conf /etc/nginx/sites-available/copilot
sudo $EDITOR /etc/nginx/sites-available/copilot   # fill in <YOUR_DOMAIN> and <REPO_PATH>
sudo ln -s /etc/nginx/sites-available/copilot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d <YOUR_DOMAIN>             # obtains the cert and rewrites the TLS block
```

Certbot's systemd timer (`certbot.timer`, installed with the package) renews automatically; no
cron entry needed.

Visit `https://<YOUR_DOMAIN>` — the dashboard should load, and `https://<YOUR_DOMAIN>/api/v1/...`
should reach the backend through the proxy.

## 6. Backups

```bash
sudo cp infrastructure/deploy/backup-db.sh /opt/copilot/app/infrastructure/deploy/
sudo chmod +x /opt/copilot/app/infrastructure/deploy/backup-db.sh
sudo -u <DEPLOY_USER> crontab -e
# add: 0 3 * * * /usr/bin/env bash /opt/copilot/app/infrastructure/deploy/backup-db.sh
```

Only the Postgres database is backed up - the vector indexes (`.qdrant`, `.qdrant-mcp`) are
derived, rebuildable from `knowledge-base/` (already in git), not source of truth (ADR-0002).

## 7. Deploying an update

```bash
cd /opt/copilot/app
sudo -u <DEPLOY_USER> git pull
sudo -u <DEPLOY_USER> uv sync
cd backend && sudo -u <DEPLOY_USER> uv run alembic upgrade head && cd ..
cd frontend && sudo -u <DEPLOY_USER> npm install && sudo -u <DEPLOY_USER> npm run build && cd ..
sudo systemctl restart copilot-backend
```

Frontend-only changes need only the `frontend/` steps and no restart; backend or migration
changes need the restart.

## Deploy checklist

- [ ] `.env` is mode `600`, owned by `<DEPLOY_USER>`, not inside the git working tree's tracked
      files (`git status` shows nothing from it)
- [ ] `DATABASE_URL` points at `copilot_prod`, not a dev/test database
- [ ] `JWT_SECRET_KEY` is a fresh, generated value - not copied from a local `.env`
- [ ] `systemctl status copilot-backend` shows `active (running)`, and `GET /health/ready`
      through Nginx returns 200
- [ ] `sudo nginx -t` passes and the site is reachable over HTTPS with a valid certificate
- [ ] The deploy checklist's own backup step has actually run once and produced a `.sql.gz` file
      in `COPILOT_BACKUP_DIR`
- [ ] `HF_TOKEN`/`URLHAUS_AUTH_KEY` are either set (if reports/threat-intel/`mode=deep` should
      work) or their absence is an accepted, understood tradeoff for this deployment
