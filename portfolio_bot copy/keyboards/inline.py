# portfolio_bot/keyboards/inline.py
from telebot import types
from portfolio_bot import config

def create_main_menu_keyboard():
    """
    Создает главную клавиатуру с кнопками "Создать портфель" и "О боте".
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для запуска Mini App
    mini_app_button = types.InlineKeyboardButton(
        text="🚀 Сформировать портфель",
        web_app=types.WebAppInfo(url=config.MINI_APP_URL)
    )
    
    # Кнопка для получения информации о боте
    about_button = types.InlineKeyboardButton(
        text="ℹ️ О боте",
        callback_data="about"
    )

    keyboard.add(mini_app_button, about_button)
    return keyboard

def create_back_to_main_menu_keyboard():
    """
    Создает клавиатуру с одной кнопкой 'Назад в главное меню'.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    back_button = types.InlineKeyboardButton(
        text="⬅️ Назад в главное меню",
        callback_data="back_to_main_menu"
    )
    
    keyboard.add(back_button)
    return keyboard

