
# Streamlit Bot Dashboard

## Overview
A secure web-based control panel for managing Telegram bots on your Linux server. Accessible at https://mystrotamer.com/admin with full systemd integration, secure authentication, and Nginx reverse-proxy.

## Features
- Multi-bot detection inside /apps/
- Start/Stop/Restart systemd services
- Journalctl logs viewer
- Chat ID fetcher
- Streamlit-based UI (dark theme)
- Protected via Nginx Basic Auth
- Auto-start via systemd service

## Nginx Configuration
Add inside your HTTPS server block:

```
location /admin/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://127.0.0.1:8501/;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Systemd Service
File: `/etc/systemd/system/streamlit_dashboard.service`

```
[Unit]
Description=Telegram Bot Dashboard (Streamlit)
After=network.target

[Service]
User=tamer
WorkingDirectory=/home/tamer/telegram_bot
ExecStart=/home/tamer/telegram_bot/.venv/bin/streamlit run apps/dashboard/streamlit_app.py --server.port=8501 --server.address=127.0.0.1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Access Dashboard
Visit:
```
https://mystrotamer.com/admin
```
Use your Nginx htpasswd credentials.
