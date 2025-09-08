# -*- coding: utf-8 -*-
# Этот файл должен находиться в КОРНЕВОЙ папке проекта

import telebot
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- Импорты из нашего пакета portfolio_bot ---
from portfolio_bot import config
from portfolio_bot.database.repository import CombinedRepository
from portfolio_bot.domain.calculator import PortfolioCalculator
from portfolio_bot.handlers.start import register_start_handler
from portfolio_bot.handlers.about import register_about_handler
from portfolio_bot.handlers.admin import register_admin_handlers

# --- Инициализация Firebase Admin SDK ---
db = None
try:
    cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK успешно инициализирован.")
except Exception as e:
    print(f"⚠️ Ошибка инициализации Firebase: {e}")
    print("-> Админские функции (например, /get_stats) будут недоступны.")

# --- ИНИЦИАЛИЗАЦИЯ БЭКЕНД-ЛОГИКИ ---
repository = CombinedRepository()
calculator = PortfolioCalculator(repository)

# --- Инициализация бота ---
bot = telebot.TeleBot(config.BOT_TOKEN)
print("Бот инициализирован...")

# --- ИЗМЕНЕНИЕ: Обработчик стал более надежным ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """
    Получает от фронтенда ГОТОВЫЙ объект портфеля и формирует из него сообщение.
    """
    try:
        data_str = message.web_app_data.data
        print(f"Получены данные из Web App: {data_str}")
        
        calculated_portfolio = json.loads(data_str)

        # Безопасно получаем данные с помощью .get()
        amount = calculated_portfolio.get('initial_amount', 0)
        term = calculated_portfolio.get('term', 0)
        strategy_name = calculated_portfolio.get('strategy_name', 'Не определена')
        expected_return = calculated_portfolio.get('expected_annual_return', 0)
        composition = calculated_portfolio.get('composition', [])

        # Формируем состав портфеля для сообщения
        composition_text = "\n".join([
            # Используем .get() для каждого элемента, чтобы избежать ошибок
            f"▫️ *{item.get('fund_name', 'Неизвестный актив')}* ({item.get('percentage', 0):.0f}%)"
            for item in composition
        ])

        response_text = (
            f"✅ *Ваш портфель готов!*\n\n"
            f"Сумма: *{amount:,} ₽*\n"
            f"Срок: *{term} лет*\n\n"
            f"Стратегия: *{strategy_name}*\n"
            f"Ожидаемая годовая доходность: *~{expected_return}%*\n\n"
            f"*Состав портфеля:*\n{composition_text}"
        )
        bot.send_message(message.chat.id, response_text, parse_mode='Markdown')

    except Exception as e:
        print(f"Критическая ошибка обработки данных из Web App: {e}")
        bot.send_message(message.chat.id, "К сожалению, произошла непредвиденная ошибка при обработке вашего портфеля.")

# --- Регистрация всех обработчиков ---
register_start_handler(bot, repository)
register_about_handler(bot)
register_admin_handlers(bot, db, config.APP_ID, config.ADMIN_IDS)
print("Обработчики команд зарегистрированы.")

# --- Запуск бота ---
if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
3.
bot.polling(none_stop=True)

