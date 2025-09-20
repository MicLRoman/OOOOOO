# portfolio_bot/handlers/about.py
from telebot import TeleBot
from telebot.types import CallbackQuery
# Исправленный абсолютный импорт
from portfolio_bot.keyboards.inline import create_back_to_main_menu_keyboard
from portfolio_bot.handlers.messages import MESSAGES

def show_about_menu(bot: TeleBot, call: CallbackQuery):
    """
    Показывает информацию о проекте.
    """
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=MESSAGES['about'],
        reply_markup=create_back_to_main_menu_keyboard(),
        parse_mode='html'
    )

def register_about_handler(bot: TeleBot):
    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_callback_handler(call):
        show_about_menu(bot, call)

