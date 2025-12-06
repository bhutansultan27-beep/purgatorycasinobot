# Deploy Casino Bot on External Server (Webdock/Plisio)

## Files to Upload
Upload these files to your server:
- `main.py`
- `webhook_server.py`
- `database.py`
- `casino_data.json`
- `requirements.txt`

## Server Setup

### 1. Install Python 3.10+
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Create project directory
```bash
mkdir -p /opt/casino-bot
cd /opt/casino-bot
# Upload your files here
```

### 3. Install dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Set environment variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export ADMIN_IDS="your_telegram_user_id"
export PLISIO_API_KEY="your_plisio_secret_key"
export LTC_USD_RATE="100"
```

Or create a `.env` file and source it.

### 5. Run the bot
```bash
python3 main.py
```

## Run as a Service (24/7)

Create systemd service file:
```bash
sudo nano /etc/systemd/system/casino-bot.service
```

Add this content:
```ini
[Unit]
Description=Antaria Casino Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/casino-bot
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="ADMIN_IDS=your_admin_id"
Environment="COINREMITTER_API_KEY=your_key"
Environment="COINREMITTER_PASSWORD=your_password"
Environment="LTC_REQUIRED_CONFIRMATIONS=3"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable casino-bot
sudo systemctl start casino-bot
```

Check status:
```bash
sudo systemctl status casino-bot
```

View logs:
```bash
journalctl -u casino-bot -f
```

## Webhook Setup (for deposits)

Your webhook URL will be:
```
http://YOUR_SERVER_IP:5000/webhook/deposit
```

Configure this URL in your CoinRemitter dashboard.

If you have a domain, use nginx to proxy port 5000 with HTTPS.
