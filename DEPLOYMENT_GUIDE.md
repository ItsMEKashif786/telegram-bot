# Deployment Guide for fps.ms Server

## Prerequisites
1. SSH access to fps.ms server
2. Python 3.8+ installed
3. Git installed (optional)

## Step 1: Upload Files to Server

### Option A: Using SCP (Secure Copy)
```bash
# From your local machine
scp -r ./* user@fps.ms:/path/to/telegram_bot/
```

### Option B: Using Git
```bash
# On server
git clone <your-repo-url> telegram_bot
cd telegram_bot
```

## Step 2: Install Dependencies

```bash
cd /path/to/telegram_bot
pip3 install -r requirements.txt
```

If pip3 is not available, install it first:
```bash
sudo apt update
sudo apt install python3-pip
```

## Step 3: Configure the Bot

### Update Configuration
The original `config.py` has hardcoded Ubuntu paths. You have two options:

**Option 1: Use the server-ready config**
```bash
# Backup original config
mv config.py config_original.py
# Use server-ready config
mv config_server.py config.py
```

**Option 2: Manually edit config.py**
Edit `config.py` and change these lines:
```python
# Change from:
DB_PATH = "/home/ubuntu/telegram_bot/bot_data.db"
DATA_DIR = "/home/ubuntu/telegram_bot/data"

# To (use absolute path):
DB_PATH = "/path/to/your/telegram_bot/bot_data.db"
DATA_DIR = "/path/to/your/telegram_bot/data"
```

## Step 4: Test the Bot

```bash
cd /path/to/telegram_bot
python3 bot.py
```

If you see errors, check:
1. **ModuleNotFoundError**: Install missing packages with `pip3 install <package-name>`
2. **PermissionError**: Ensure you have write permissions to the bot directory
3. **Database errors**: The bot will create `bot_data.db` automatically

## Step 5: Set Up as a Service (Optional but Recommended)

### Create Systemd Service File
Create `/etc/systemd/system/telegram_bot.service`:

```ini
[Unit]
Description=Telegram Bot for Dawateislami India
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME  # Change to your fps.ms username
WorkingDirectory=/path/to/telegram_bot
ExecStart=/usr/bin/python3 /path/to/telegram_bot/bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=telegram-bot

[Install]
WantedBy=multi-user.target
```

### Enable and Start the Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram_bot.service
sudo systemctl start telegram_bot.service
```

### Check Service Status
```bash
sudo systemctl status telegram_bot.service
sudo journalctl -u telegram_bot.service -f  # Follow logs
```

## Step 6: Troubleshooting Common Issues

### 1. "Module not found" errors
```bash
pip3 install python-telegram-bot pytz requests pillow qrcode
```

### 2. Permission denied for database
```bash
chmod 755 /path/to/telegram_bot
touch /path/to/telegram_bot/bot_data.db
chmod 666 /path/to/telegram_bot/bot_data.db
```

### 3. Service won't start
Check logs:
```bash
sudo journalctl -u telegram_bot.service --no-pager -n 50
```

### 4. Bot token invalid
Ensure your BOT_TOKEN in config.py is correct.

### 5. Port/firewall issues
The bot uses Telegram API (port 443/80), no inbound ports needed.

## Step 7: Maintenance

### Update the bot
```bash
cd /path/to/telegram_bot
git pull  # if using git
# Or upload new files via SCP
sudo systemctl restart telegram_bot.service
```

### View logs
```bash
sudo journalctl -u telegram_bot.service --since "1 hour ago"
```

### Stop/Start/Restart
```bash
sudo systemctl stop telegram_bot.service
sudo systemctl start telegram_bot.service
sudo systemctl restart telegram_bot.service
```

## Important Notes for fps.ms Server

1. **Username**: Replace `ubuntu` with your actual fps.ms username
2. **Python path**: Check with `which python3` and update service file
3. **Directory permissions**: Ensure your user has write access
4. **Database location**: The bot will create `bot_data.db` in the bot directory
5. **Data directory**: The `data/` folder will be created automatically for storing images

## Quick Test Command
```bash
cd /path/to/telegram_bot && python3 -c "from config import BOT_TOKEN; print('Bot token configured:', BOT_TOKEN[:10] + '...')"
```

If this works, your configuration is correct!