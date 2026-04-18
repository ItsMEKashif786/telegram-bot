# Telegram Bot for Dawateislami India

A Telegram bot that provides daily Hadees Shareef, weekly Risala (Hindi & Urdu), Darood Sharif collection, and donation features.

## Features

- 📜 Daily Hadees Shareef
- 📖 Weekly Risala (Hindi & Urdu)
- 🤲 Darood Sharif Collection
- 💝 Donation system with UPI QR
- 👥 Subscriber management
- ⚙️ Admin panel for management

## Requirements

- Python 3.8+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telegram_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - Copy `config_server.py` to `config.py`
   - Update `BOT_TOKEN` with your Telegram bot token
   - Update `ADMIN_ID` with your Telegram user ID

4. Run the bot:
   ```bash
   python bot.py
   ```

## Configuration

Edit `config.py` with your settings:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = YOUR_ADMIN_ID_HERE
UPI_ID = "your-upi@id"
```

## Deployment on fps.ms Server

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions on deploying to fps.ms server.

## Project Structure

- `bot.py` - Main bot application
- `config.py` - Configuration settings
- `database.py` - SQLite database operations
- `scraper.py` - Web scraping for booklets
- `upi_qr.py` - UPI QR code generation
- `requirements.txt` - Python dependencies

## License

This project is for Dawateislami India community use.