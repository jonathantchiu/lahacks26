# SentinelAI Deploy — Vultr + GoDaddy + Let's Encrypt

Three files do the work:

| file | purpose |
|------|---------|
| `setup.sh` | one-time bootstrap on a fresh Ubuntu 22.04/24.04 box |
| `sentinelai.service` | systemd unit running uvicorn under user `sentinel` |
| `nginx.conf` | reverse proxy: `:80` → `:8000`, with WebSocket upgrade |
| `deploy.sh` | pull latest, reinstall deps, restart service |

## Phase 5 runbook (Sat ~9–11 AM)

### 0. Provision Vultr (one-time, do FIRST — credits take a few minutes to approve)

1. https://www.vultr.com/ → "Deploy New Server"
2. Cloud Compute → **Regular Performance** is fine for the API box (the GPU box is Sartaj's)
3. OS: **Ubuntu 22.04 LTS** (or 24.04)
4. Region: **Los Angeles** (closest to LA Hacks venue)
5. Size: $6/mo (1 vCPU / 1 GB) is enough for the API; bump to $12 if you want headroom
6. Note the **public IPv4** address.

### 1. Buy a domain on GoDaddy (~5 min)

1. https://www.godaddy.com/ — use the MLH coupon if you can find it
2. Pick something memorable: `sentinelai.live`, `seenotable.com`, etc.
3. After purchase: **DNS → Manage Records**
   - Add an `A` record:  `Host: @`  → `Value: <Vultr IP>`  → `TTL: 600`
   - Add an `A` record:  `Host: www` → `Value: <Vultr IP>` → `TTL: 600`
4. DNS propagation usually < 5 min; verify with `dig +short yourdomain.com`.

### 2. Bootstrap the box

SSH in as root:

```bash
ssh root@<vultr-ip>
```

Then either pipe the script in directly:

```bash
curl -fsSL https://raw.githubusercontent.com/jonathantchiu/lahacks26/claude/crazy-visvesvaraya-1e66df/infrastructure/setup.sh \
  | bash -s -- \
      https://github.com/jonathantchiu/lahacks26.git \
      claude/crazy-visvesvaraya-1e66df \
      yourdomain.com
```

…or scp the file over and run `sudo ./setup.sh ... yourdomain.com`.

`setup.sh` will:
- install Python 3.11, ffmpeg, nginx, certbot, system libs cv2 needs
- create the `sentinel` user, clone the repo to `/opt/sentinelai`, install deps
- copy the systemd unit + nginx site
- reload nginx and start firewall rules (if ufw is available)

### 3. Fill in `.env`

```bash
sudo -u sentinel nano /opt/sentinelai/backend/.env
```

Paste:
```
MONGODB_URI=...        # same string you used locally
MONGODB_DB=sentinelai
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...
```

⚠️  Whitelist this Vultr IP in **MongoDB Atlas → Network Access** (or set `0.0.0.0/0` for the hackathon).

### 4. Start the service

```bash
sudo systemctl start sentinelai
sudo journalctl -u sentinelai -f          # watch the logs
curl http://127.0.0.1:8000/health         # should print {"status":"ok",...}
```

### 5. Issue the HTTPS cert

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Pick "redirect HTTP → HTTPS" when prompted.  Certbot rewrites
`/etc/nginx/sites-available/sentinelai` to listen on `:443` and renew
itself.  Verify:

```bash
curl https://yourdomain.com/health
```

### 6. Hand the URL off to Jonny

Tell him to point his frontend `.env` at:

```
VITE_API_URL=https://yourdomain.com
VITE_WS_URL=wss://yourdomain.com
```

and redeploy his frontend.

## Re-deploying after every commit

On the Vultr box:

```bash
sudo bash /opt/sentinelai/infrastructure/deploy.sh
```

Pulls latest, reinstalls deps, restarts the service, prints status,
and curls `/health`.

## Useful one-liners

```bash
# Tail logs
sudo journalctl -u sentinelai -f

# Restart only the app (no git pull)
sudo systemctl restart sentinelai

# Test nginx config without reloading
sudo nginx -t

# Show stream_manager state
curl https://yourdomain.com/health

# Force-renew cert
sudo certbot renew --dry-run
```

## Troubleshooting

- **MongoDB connection refused**: Atlas IP allowlist. Add the Vultr IP or `0.0.0.0/0`.
- **WebSocket 101 → 502**: ensure nginx has the `Upgrade`/`Connection` headers (the `nginx.conf` here does).
- **OpenCV can't open a stream URL**: Linux wheels handle https/MP4 fine; the macOS issue from local dev does **not** apply on Vultr. RTSP and MJPEG should both Just Work.
- **certbot failed**: DNS not propagated yet. Wait 5 min, `dig +short yourdomain.com` should return the Vultr IP.
- **Port 80/443 unreachable**: Vultr firewall is open by default but `ufw` may not be. `sudo ufw status`; if active, `sudo ufw allow 'Nginx Full'`.
