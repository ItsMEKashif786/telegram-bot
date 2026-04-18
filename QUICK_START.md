# Quick Start: Deploy to fps.ms via GitHub

## Step 1: Fix File Names (Important!)
The original files have double dots. Rename them:
```bash
ren bot..py bot.py
ren config..py config.py
ren database..py database.py
ren scraper..py scraper.py
ren upi_qr..py upi_qr.py
ren telegram_bot..service telegram_bot.service
```

Or on Linux/Mac:
```bash
mv bot..py bot.py
mv config..py config.py
mv database..py database.py
mv scraper..py scraper.py
mv upi_qr..py upi_qr.py
mv telegram_bot..service telegram_bot.service
```

## Step 2: Set Up GitHub

1. **Run the setup script**:
   ```bash
   chmod +x github_setup.sh
   ./github_setup.sh
   ```

2. **Follow the prompts** to enter your GitHub username and email

3. **Create repository on GitHub.com**:
   - Go to https://github.com/new
   - Name: `telegram-bot`
   - DO NOT initialize with README, .gitignore, or license

4. **Push to GitHub** (commands shown by script):
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/telegram-bot.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Deploy to fps.ms Server

### Option A: Using GitHub Clone (Recommended)
On your fps.ms server:
```bash
git clone https://github.com/YOUR_USERNAME/telegram-bot.git
cd telegram-bot

# Install dependencies
pip3 install -r requirements.txt

# Use server-ready config
mv config_server.py config.py

# Test the bot
python3 bot.py
```

### Option B: Using fps.ms Startup Options
1. Upload the entire project folder to fps.ms
2. Use the startup command:
   ```
   cd /path/to/telegram_bot && python3 bot.py
   ```
3. Or use the deploy.sh script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh /path/to/deployment
   ```

## Step 4: Run as Service (Optional)

Create `/etc/systemd/system/telegram_bot.service`:
```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegram_bot
ExecStart=/usr/bin/python3 /path/to/telegram_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram_bot.service
sudo systemctl start telegram_bot.service
```

## Files Created for Deployment:

1. **`requirements.txt`** - Python dependencies
2. **`config_server.py`** - Server-ready configuration
3. **`DEPLOYMENT_GUIDE.md`** - Detailed deployment instructions
4. **`deploy.sh`** - Automated deployment script
5. **`github_setup.sh`** - GitHub setup script
6. **`.gitignore`** - Git ignore file
7. **`README.md`** - Project documentation

## Troubleshooting:

1. **"Module not found"**: Run `pip3 install -r requirements.txt`
2. **Permission errors**: Ensure write access to bot directory
3. **GitHub push fails**: Check your GitHub token/credentials
4. **Bot won't start**: Check `python3 bot.py` for error messages

## Need Help?
Check `DEPLOYMENT_GUIDE.md` for comprehensive troubleshooting and advanced configuration.