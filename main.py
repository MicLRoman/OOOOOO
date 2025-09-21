# -*- coding: utf-8 -*-
# Этот файл должен находиться в КОРНЕВОЙ папке проекта

import telebot
import firebase_admin
from firebase_admin import credentials, firestore
import json
from threading import Thread
from flask import Flask, request

# --- Импорты из нашего пакета portfolio_bot ---
from portfolio_bot import config
from portfolio_bot.database.repository import CombinedRepository
from portfolio_bot.domain.calculator import PortfolioCalculator
from portfolio_bot.handlers.start import register_start_handler
from portfolio_bot.handlers.about import register_about_handler
from portfolio_bot.handlers.admin import register_admin_handlers

# --- Форматирование срока ---
def format_term_in_months(months):
    if not isinstance(months, (int, float)) or months <= 0:
        return "Неопределённый срок"
    
    months = int(months)
    years = round(months / 12, 1)
    if years.is_integer():
        years = int(years)

    last_digit = months % 10
    last_two_digits = months % 100

    if last_two_digits in [11, 12, 13, 14]:
        month_str = "месяцев"
    elif last_digit == 1:
        month_str = "месяц"
    elif last_digit in [2, 3, 4]:
        month_str = "месяца"
    else:
        month_str = "месяцев"
    
    return f"{months} {month_str} (~{years} г.)"

# --- Инициализация Firebase ---
db = None
try:
    cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK успешно инициализирован.")
except Exception as e:
    print(f"⚠️ Ошибка инициализации Firebase: {e}")

# --- ИНИЦИАЛИЗАЦИЯ БЭКЕНД-ЛОГИКИ ---
repository = CombinedRepository()
calculator = PortfolioCalculator(repository)
bot = telebot.TeleBot(config.BOT_TOKEN)
print("Бот инициализирован...")

# --- Логика форматирования и отправки сообщения ---
def format_and_send_portfolio(user_id, final_data):
    try:
        investment_data = final_data.get('investmentData', {})
        portfolio_data = final_data.get('portfolioData', {})
        
        goal = investment_data.get('goal', 'grow')
        monthly_contribution = portfolio_data.get('monthly_contribution', 0)
        term_months = portfolio_data.get('term_months')
        formatted_term = format_term_in_months(term_months)
        
        contribution_text = ""
        if monthly_contribution > 0:
            contribution_text = f"Ежемесячное пополнение: *{monthly_contribution:,.0f} ₽*\n"

        strategy_name = portfolio_data.get('strategy_name', 'Не определена')
        expected_return = portfolio_data.get('expected_annual_return', 0)
        composition = portfolio_data.get('composition', [])
        initial_amount = portfolio_data.get('initial_amount', 0)

        composition_items = []
        for item in composition:
            percentage = item.get('percentage', 0)
            amount_in_rubles = initial_amount * (percentage / 100.0)
            line = (
                f"▫️ *{item.get('fund_name', 'Неизвестный актив')}* "
                f"({percentage:.0f}%) — *~{amount_in_rubles:,.0f} ₽*"
            )
            composition_items.append(line)
        composition_text = "\n".join(composition_items)

        forecast = portfolio_data.get('forecast', {})
        forecast_min = forecast.get('min', [0])[0]
        forecast_avg = forecast.get('avg', [0])[0]
        forecast_max = forecast.get('max', [0])[0]
        
        response_text = ""
        
        if goal == 'dream':
            dream_amount = investment_data.get('dreamAmount', 0)
            response_text = (
                f"🎯 *Ваша цель: Накопить на мечту*\n"
                f"Сумма цели: *{dream_amount:,.0f} ₽*\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\n"
                f"{contribution_text}"
                f"Срок: *{formatted_term}*\n"
                f"📈 *Прогноз итогового капитала*\n"
                f"• В худшем случае: *~{forecast_min:,.0f} ₽*\n"
                f"• Базовый прогноз: *~{forecast_avg:,.0f} ₽*\n"
                f"• В лучшем случае: *~{forecast_max:,.0f} ₽*\n"
                f"*{strategy_name} (~{expected_return}% годовых)*\n"
                f"*Состав портфеля:*\n"
                f"{composition_text}"
            )
        elif goal == 'passive':
            passive_income = investment_data.get('passiveIncome', 0)
            avg_income = portfolio_data.get('monthly_income_forecast', [0])[0]
            min_income = (forecast_min * (18.0 / 100)) / 12
            max_income = (forecast_max * (18.0 / 100)) / 12
            response_text = (
                f"🏝️ *Ваша цель: Пассивный доход*\n"
                f"Желаемый доход: *{passive_income:,.0f} ₽/мес*\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\n"
                f"{contribution_text}"
                f"Срок накопления: *{formatted_term}*\n"
                f"📈 *Прогноз пассивного дохода в месяц*\n"
                f"• В худшем случае: *~{min_income:,.0f} ₽*\n"
                f"• Базовый прогноз: *~{avg_income:,.0f} ₽*\n"
                f"• В лучшем случае: *~{max_income:,.0f} ₽*\n"
                f"*{strategy_name} (~{expected_return}% годовых)*\n"
                f"*Состав портфеля:*\n"
                f"{composition_text}"
            )
        else: # goal == 'grow'
            response_text = (
                f"💰 *Ваша цель: Приумножить капитал*\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\n"
                f"{contribution_text}"
                f"Срок: *{formatted_term}*\n"
                f"📈 *Прогноз роста капитала*\n"
                f"• В худшем случае: *~{forecast_min:,.0f} ₽*\n"
                f"• Базовый прогноз: *~{forecast_avg:,.0f} ₽*\n"
                f"• В лучшем случае: *~{forecast_max:,.0f} ₽*\n"
                f"*{strategy_name} (~{expected_return}% годовых)*\n"
                f"*Состав портфеля:*\n"
                f"{composition_text}"
            )

        bot.send_message(user_id, response_text, parse_mode='Markdown')

    except Exception as e:
        print(f"Критическая ошибка при отправке сообщения: {e}")
        bot.send_message(user_id, "К сожалению, произошла непредвиденная ошибка при обработке вашего портфеля.")

# --- Обработчик для Web App Data (старый, остается для обратной совместимости) ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    final_data = json.loads(message.web_app_data.data)
    format_and_send_portfolio(message.chat.id, final_data)

# --- Регистрация команд бота ---
register_start_handler(bot, repository)
register_about_handler(bot)
register_admin_handlers(bot, db, config.APP_ID, config.ADMIN_IDS)
print("Обработчики команд зарегистрированы.")

# --- ВНУТРЕННИЙ СЕРВЕР ДЛЯ ПРИЕМА ЗАПРОСОВ ОТ API_SERVER ---
internal_app = Flask(__name__)

@internal_app.route('/send_portfolio', methods=['POST'])
def send_portfolio_from_api():
    try:
        data = request.json
        user_id = data.get('userId')
        portfolio_summary = data.get('portfolioSummary')
        if not user_id or not portfolio_summary:
            return "Missing data", 400
        
        format_and_send_portfolio(user_id, portfolio_summary)
        return "OK", 200
    except Exception as e:
        print(f"Ошибка в /send_portfolio: {e}")
        return "Internal Server Error", 500

# --- Запуск бота и сервера ---
if __name__ == '__main__':
    print("Запускаем внутренний сервер для API в отдельном потоке...")
    # Запускаем Flask на порту 8080
    internal_server_thread = Thread(target=lambda: internal_app.run(port=8080, debug=False))
    internal_server_thread.daemon = True
    internal_server_thread.start()
    
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)

