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

# --- НОВАЯ ФУНКЦИЯ: Форматирование срока в месяцах с правильными склонениями ---
def format_term_in_months(months):
    """Принимает количество месяцев и возвращает красивую строку."""
    if not isinstance(months, (int, float)) or months <= 0:
        return "Неопределенный срок"
    
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

# --- ИЗМЕНЕНИЕ: Обработчик полностью переработан для поддержки целей ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data_str = message.web_app_data.data
        final_data = json.loads(data_str)
        investment_data = final_data.get('investmentData', {})
        portfolio_data = final_data.get('portfolioData', {})
        
        goal = investment_data.get('goal', 'grow')
        monthly_contribution = portfolio_data.get('monthly_contribution', 0)
        term_months = portfolio_data.get('term_months')
        formatted_term = format_term_in_months(term_months)
        
        contribution_text = ""
        if monthly_contribution > 0:
            contribution_text = f"Ежемесячное пополнение: *{monthly_contribution:,.0f} ₽*\\n"

        strategy_name = portfolio_data.get('strategy_name', 'Не определена')
        expected_return = portfolio_data.get('expected_annual_return', 0)
        composition = portfolio_data.get('composition', [])
        
        composition_text = "\\n".join([
            f"▫️ *{item.get('fund_name', 'Неизвестный актив')}* ({item.get('percentage', 0):.0f}%)"
            for item in composition
        ])

        forecast = portfolio_data.get('forecast', {})
        forecast_min = forecast.get('min', [])[-1]
        forecast_avg = forecast.get('avg', [])[-1]
        forecast_max = forecast.get('max', [])[-1]
        initial_amount = portfolio_data.get('initial_amount', 0)
        
        # --- ИЗМЕНЕНИЕ: Получаем и форматируем вероятность ---
        probability = portfolio_data.get('goalAchievedProbability')
        probability_text = ""
        if probability is not None:
            # --- ИЗМЕНЕНИЕ: Более удачные формулировки ---
            if goal == 'grow':
                prob_label = "Вероятность, что капитал превысит вложения"
            else:
                prob_label = "Вероятность достижения цели"
            probability_text = f"_{prob_label}: *{probability}%*_\\n\\n"


        response_text = ""
        
        if goal == 'dream':
            dream_amount = investment_data.get('dreamAmount', 0)
            response_text = (
                f"🎯 *Ваша цель: Накопить на мечту*\\n\\n"
                f"Сумма цели: *{dream_amount:,.0f} ₽*\\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\\n"
                f"{contribution_text}"
                f"Срок: *{formatted_term}*\\n\\n"
                f"📈 *Прогноз итогового капитала*\\n"
                f"• В худшем случае: *~{forecast_min:,.0f} ₽*\\n"
                f"• Базовый прогноз: *~{forecast_avg:,.0f} ₽*\\n"
                f"• В лучшем случае: *~{forecast_max:,.0f} ₽*\\n"
                f"{probability_text}"
                f"*{strategy_name} (~{expected_return}% годовых)*\\n"
                f"{composition_text}"
            )
        elif goal == 'passive':
            passive_income = investment_data.get('passiveIncome', 0)
            min_income = (forecast_min * (18.0 / 100)) / 12
            avg_income = (forecast_avg * (18.0 / 100)) / 12
            max_income = (forecast_max * (18.0 / 100)) / 12
            response_text = (
                f"🏝️ *Ваша цель: Пассивный доход*\\n\\n"
                f"Желаемый доход: *{passive_income:,.0f} ₽/мес*\\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\\n"
                f"{contribution_text}"
                f"Срок накопления: *{formatted_term}*\\n\\n"
                f"📈 *Прогноз пассивного дохода в месяц*\\n"
                f"• В худшем случае: *~{min_income:,.0f} ₽*\\n"
                f"• Базовый прогноз: *~{avg_income:,.0f} ₽*\\n"
                f"• В лучшем случае: *~{max_income:,.0f} ₽*\\n"
                f"{probability_text}"
                f"*{strategy_name} (~{expected_return}% годовых)*\\n"
                f"{composition_text}"
            )
        else: # goal == 'grow'
            response_text = (
                f"💰 *Ваша цель: Приумножить капитал*\\n\\n"
                f"Первый взнос: *{initial_amount:,.0f} ₽*\\n"
                f"{contribution_text}"
                f"Срок: *{formatted_term}*\\n\\n"
                f"📈 *Прогноз роста капитала*\\n"
                f"• В худшем случае: *~{forecast_min:,.0f} ₽*\\n"
                f"• Базовый прогноз: *~{forecast_avg:,.0f} ₽*\\n"
                f"• В лучшем случае: *~{forecast_max:,.0f} ₽*\\n"
                f"{probability_text}"
                f"*{strategy_name} (~{expected_return}% годовых)*\\n"
                f"{composition_text}"
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
    bot.polling(none_stop=True)
