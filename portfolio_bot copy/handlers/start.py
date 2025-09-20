# portfolio_bot/handlers/start.py
from telebot import TeleBot
from telebot.types import Message, CallbackQuery
# --- ИЗМЕНЕНИЕ: Импортируем репозиторий ---
from ..database.repository import CombinedRepository
from ..keyboards.inline import create_main_menu_keyboard
from ..handlers.messages import MESSAGES

def send_welcome_message(bot: TeleBot, message: Message, repository: CombinedRepository):
    """
    Отправляет приветственное сообщение и добавляет/обновляет пользователя в БД.
    """
    # --- ИЗМЕНЕНИЕ: Получаем все данные пользователя ---
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = message.from_user.username or "N/A" # Получаем username или N/A

    # --- ИЗМЕНЕНИЕ: Используем новый метод для добавления/обновления пользователя ---
    # Этот метод сохраняет и user_id, и username
    repository.add_or_update_user(user_id, username)

    # Остальная логика без изменений
    welcome_text = MESSAGES['welcome'].format(name=user_name)
    keyboard = create_main_menu_keyboard()
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='html')


def back_to_main_menu(bot: TeleBot, call: CallbackQuery):
    """
    Возвращает в главное меню по нажатию кнопки.
    """
    user_name = call.from_user.first_name
    welcome_text = MESSAGES['welcome'].format(name=user_name)
    keyboard = create_main_menu_keyboard()

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode='html'
        )
    except Exception as e:
        # Игнорируем ошибку, если сообщение не изменилось
        if 'message is not modified' not in str(e):
            print(f"Ошибка при возврате в главное меню: {e}")


def register_start_handler(bot: TeleBot, repository: CombinedRepository):
    """Регистрирует обработчики для команды /start и возврата в меню."""
    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        send_welcome_message(bot, message, repository)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
    def handle_back_to_main(call):
        back_to_main_menu(bot, call)

