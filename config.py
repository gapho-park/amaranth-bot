import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Amaranth 10 Settings
    AMARANTH_USER_ID = os.getenv('AMARANTH_USER_ID', 'gapho')
    AMARANTH_PASSWORD = os.getenv('AMARANTH_PASSWORD')
    AMARANTH_URL = os.getenv('AMARANTH_URL', 'https://portal.rapportlabs.kr/#/login')

    # Bot Settings
    BOT_HEADLESS = os.getenv('BOT_HEADLESS', 'false').lower() == 'true'
    BOT_SLOW_MO = int(os.getenv('BOT_SLOW_MO', '500'))
    BOT_TIMEOUT = 30000  # 30 seconds

    # Paths
    DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', './downloads')
    
    # Google Sheets Settings
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'service_account.json')
    _raw_url = os.getenv('GOOGLE_SHEET_URL', '')
    # Remove query params and fragments to get clean URL
    GOOGLE_SHEET_URL = _raw_url.split('?')[0].split('#')[0] if _raw_url else None
    GOOGLE_SHEET_TAB = os.getenv('GOOGLE_SHEET_TAB', 'Sheet1')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

def validate_config():
    if not Config.AMARANTH_PASSWORD:
        raise ValueError('❌ AMARANTH_PASSWORD environment variable is not set.')
    return True
