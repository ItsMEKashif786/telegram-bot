#!/bin/bash

# fps.ms Deployment Script
# Run this on your fps.ms server to deploy the Telegram bot

set -e

echo "=== fps.ms Telegram Bot Deployment ==="
echo "Repository: https://github.com/ItsMEKashif786/telegram-bot"

# Default deployment directory
DEPLOY_DIR="${1:-/home/$USER/telegram_bot}"

echo "Deploying to: $DEPLOY_DIR"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt update && sudo apt install -y git
fi

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Installing python3..."
    sudo apt update && sudo apt install -y python3 python3-pip
fi

# Clone or update repository
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "$DEPLOY_DIR"
    git pull origin master
else
    echo "Cloning repository..."
    git clone https://github.com/ItsMEKashif786/telegram-bot.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Configure for server
echo "Configuring for server..."
if [ -f "config_server.py" ]; then
    if [ -f "config.py" ]; then
        echo "Backing up existing config.py..."
        mv config.py config.py.backup
    fi
    cp config_server.py config.py
    echo "✓ Server configuration applied"
else
    echo "⚠ config_server.py not found, using existing config.py"
fi

# Create data directory
echo "Creating data directory..."
mkdir -p data
chmod 755 data

# Set permissions
echo "Setting permissions..."
chmod +x deploy.sh github_setup.sh

# Test configuration
echo "Testing configuration..."
python3 -c "
try:
    from config import BOT_TOKEN, ADMIN_ID
    print('✓ Configuration loaded successfully')
    print(f'  Bot Token: {BOT_TOKEN[:10]}...')
    print(f'  Admin ID: {ADMIN_ID}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    print('  Please check config.py')
"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "To start the bot:"
echo "  cd $DEPLOY_DIR"
echo "  python3 bot.py"
echo ""
echo "To run as a background service:"
echo "  sudo cp telegram_bot.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable telegram_bot.service"
echo "  sudo systemctl start telegram_bot.service"
echo ""
echo "Check service status:"
echo "  sudo systemctl status telegram_bot.service"
echo ""
echo "View logs:"
echo "  sudo journalctl -u telegram_bot.service -f"
echo ""
echo "Repository URL: https://github.com/ItsMEKashif786/telegram-bot"
echo "Deployment guide: $DEPLOY_DIR/DEPLOYMENT_GUIDE.md"