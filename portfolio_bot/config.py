# portfolio_bot/config.py

# Загружаем переменные окружения из файла .env

# --- Основные настройки ---
# Токен вашего бота от @BotFather
BOT_TOKEN = "8353031245:AAEAoHDIXjEGrf5DnrMKCuOaJftr9Q5Oj-U"
# 8353031245:AAEAoHDIXjEGrf5DnrMKCuOaJftr9Q5Oj-U

# ID администраторов бота (через запятую в .env) 
ADMIN_IDS_STR = "6534859645, 1265245994, 1556788691"
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# --- URL-адреса ---
# URL вашего Mini App (обязательно HTTPS)
# Этот адрес будет использоваться и для Mini App, и для API.
WEB_APP_BASE_URL = "https://portfolio-yes.ru" # <-- ЗАМЕНИТЕ НА ВАШ АДРЕС NGROK

# URL для кнопки в Telegram будет корневым
MINI_APP_URL = WEB_APP_BASE_URL

FIREBASE_CREDENTIALS_PATH = "firebase_credentials.json"
APP_ID = "portfolio-v0" 