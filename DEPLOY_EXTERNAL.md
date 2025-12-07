# Deploy Casino Bot on Webdock Server using FileZilla

## Step 1: Files to Upload via FileZilla

Connect to your Webdock server with FileZilla and upload these files to `/opt/casino-bot/`:

**Required files:**
- `main.py` - Main bot code
- `blackjack.py` - Blackjack game logic
- `webhook_server.py` - Webhook for deposits
- `database.py` - Database utilities
- `requirements.txt` - Python dependencies

**Optional (only if you have them):**
- `casino_data.json` - Existing user data (will be created automatically if missing)

## Step 2: Connect via SSH to Your Webdock Server

Open terminal/SSH and connect to your server:
```bash
ssh root@YOUR_SERVER_IP
```

## Step 3: Install Python and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv -y

# Navigate to your bot folder
cd /opt/casino-bot

# Install required Python packages
pip3 install aiohttp python-telegram-bot APScheduler
```

## Step 4: Set Up Environment Variables

Create a startup script:
```bash
nano /opt/casino-bot/start_bot.sh
```

Paste this content (replace with your actual values):
```bash
#!/bin/bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
export ADMIN_IDS="YOUR_TELEGRAM_USER_ID"
export PLISIO_API_KEY="YOUR_PLISIO_API_KEY"

cd /opt/casino-bot
python3 main.py
```

Make it executable:
```bash
chmod +x /opt/casino-bot/start_bot.sh
```

## Step 5: Run the Bot (Quick Test)

```bash
cd /opt/casino-bot
./start_bot.sh
```

If it starts without errors, press `Ctrl+C` to stop it.

## Step 6: Run 24/7 as a Service

Create a systemd service:
```bash
sudo nano /etc/systemd/system/casino-bot.service
```

Paste this (replace with your values):
```ini
[Unit]
Description=Gild Tesoro Casino Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/casino-bot
Environment="TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE"
Environment="ADMIN_IDS=YOUR_TELEGRAM_USER_ID"
Environment="PLISIO_API_KEY=YOUR_PLISIO_API_KEY"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable casino-bot
sudo systemctl start casino-bot
```

## Step 7: Useful Commands

**Check if bot is running:**
```bash
sudo systemctl status casino-bot
```

**View live logs:**
```bash
journalctl -u casino-bot -f
```

**Restart bot after changes:**
```bash
sudo systemctl restart casino-bot
```

**Stop the bot:**
```bash
sudo systemctl stop casino-bot
```

## Step 8: Webhook for Deposits (Optional)

If using Plisio for crypto deposits, your webhook URL is:
```
http://YOUR_SERVER_IP:5000/webhook/deposit
```

Make sure port 5000 is open on your server:
```bash
sudo ufw allow 5000
```

## Troubleshooting

**Bot won't start:**
- Check logs: `journalctl -u casino-bot -n 50`
- Verify all files are uploaded
- Make sure TELEGRAM_BOT_TOKEN is correct

**Permission errors:**
```bash
chmod 755 /opt/casino-bot/*.py
```

**Missing dependencies:**
```bash
pip3 install -r /opt/casino-bot/requirements.txt
```
