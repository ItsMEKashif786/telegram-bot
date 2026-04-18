import os

# Bot Token
BOT_TOKEN = "8677144168:AAHacg3p_JIWyQyJyRh2V7iu-nLlFuiGIoc"

# Admin Chat ID (hardcoded)
ADMIN_ID = 5958336964

# UPI Details
UPI_ID = "kashif-28@ptyes"

# Website URLs
BASE_URL = "https://dawateislamiindia.org"
BOOKLET_URL = "https://dawateislamiindia.org/weekly-booklet"
PANEL_BASE_URL = "https://panel.dawateislamiindia.org/"

# Database path - using relative path
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, "bot_data.db")

# Data directory for photos etc
DATA_DIR = os.path.join(current_dir, "data")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)