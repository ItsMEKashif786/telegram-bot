#!/bin/bash

# Deployment script for fps.ms server
# Usage: ./deploy.sh /path/to/telegram_bot

set -e

echo "=== Telegram Bot Deployment Script ==="

if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/telegram_bot"
    echo "Example: $0 /home/user/telegram_bot"
    exit 1
fi

BOT_DIR="$1"
echo "Deploying to: $BOT_DIR"

# Create directory if it doesn't exist
mkdir -p "$BOT_DIR"

echo "1. Installing dependencies..."
pip3 install -r requirements.txt || {
    echo "Failed to install dependencies. Trying with pip..."
    pip install -r requirements.txt
}

echo "2. Setting up configuration..."
if [ -f "config_server.py" ]; then
    if [ -f "$BOT_DIR/config.py" ]; then
        echo "Backing up existing config.py..."
        cp "$BOT_DIR/config.py" "$BOT_DIR/config.py.backup"
    fi
    cp config_server.py "$BOT_DIR/config.py"
    echo "Server-ready config copied."
else
    echo "Warning: config_server.py not found. Using original config.py..."
fi

echo "3. Copying bot files..."
cp bot.py "$BOT_DIR/"
cp database.py "$BOT_DIR/"
cp scraper.py "$BOT_DIR/"
cp upi_qr.py "$BOT_DIR/"
cp requirements.txt "$BOT_DIR/"

echo "4. Setting permissions..."
chmod +x "$BOT_DIR/bot.py"
chmod 755 "$BOT_DIR"

echo "5. Creating data directory..."
mkdir -p "$BOT_DIR/data"
chmod 777 "$BOT_DIR/data"

echo "6. Testing configuration..."
cd "$BOT_DIR"
python3 -c "
try:
    from config import BOT_TOKEN, ADMIN_ID
    print('✓ Config loaded successfully')
    print(f'  Bot token: {BOT_TOKEN[:10]}...')
    print(f'  Admin ID: {ADMIN_ID}')
except Exception as e:
    print(f'✗ Config error: {e}')
    exit(1)
"

echo ""
echo "=== Deployment Complete ==="
echo "Next steps:"
echo "1. Test the bot: cd $BOT_DIR && python3 bot.py"
echo "2. Set up as service: see DEPLOYMENT_GUIDE.md"
echo "3. Check logs if any errors occur"
echo ""
echo "To run manually:"
echo "  cd $BOT_DIR"
echo "  python3 bot.py"