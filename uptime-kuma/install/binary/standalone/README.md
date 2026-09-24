# Uptime Kuma — binary (non-Docker) standalone

Uptime Kuma does **not** publish a prebuilt binary. The non-Docker install runs the Node.js server directly from source, kept alive by PM2.

## Requirements

- **Platform:** major Linux distros (Debian, Ubuntu, CentOS, Fedora, Arch), or Windows 10 (x64) / Windows Server 2012 R2 (x64) or higher.
- **Node.js** >= 20.4
- **Git**
- **PM2** (recommended) to run in the background.

## Install

```bash
git clone https://github.com/louislam/uptime-kuma.git
cd uptime-kuma
npm run setup
```

## Run

```bash
# Option 1 — foreground (quick test)
node server/server.js

# Option 2 (recommended) — background via PM2
npm install pm2 -g && pm2 install pm2-logrotate
pm2 start server/server.js --name uptime-kuma

# Start on boot
pm2 save && pm2 startup
```

Uptime Kuma listens on <http://localhost:3001>.

## Notes

- **Storage:** SQLite under `./data` (the repo working directory). Back it up.
- **Update:** `git pull && npm run setup`, then `pm2 restart uptime-kuma`.
- **Reverse proxy:** WebSocket-based — forward `Upgrade` and `Connection` headers.
- A community-maintained native Debian package (systemd service) exists but is unofficial.

Official source: [How to Install → Non-Docker](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install).
