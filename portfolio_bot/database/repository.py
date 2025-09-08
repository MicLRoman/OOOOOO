# portfolio_bot/database/repository.py
import sqlite3
import os
# Используем относительный импорт, так как находимся в одном пакете
from .funds_data import ALL_FUNDS, STRATEGY_TEMPLATES

# Определяем путь к папке для данных внутри пакета portfolio_bot
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, "portfolio_bot.db")

class CombinedRepository:
    """
    Единый репозиторий, который объединяет работу с:
    1. Базой данных пользователей (SQLite).
    2. Статическими данными о фондах и стратегиях (из funds_data.py).
    """
    def __init__(self):
        self._init_db()

    # --- Методы для работы с SQLite (пользователи) ---

    def _init_db(self):
        """Инициализирует БД и создает/обновляет таблицы."""
        os.makedirs(DATA_DIR, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Создаем таблицу, если ее нет
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            ''')
            # Пытаемся добавить колонку username для обратной совместимости
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
            except sqlite3.OperationalError:
                # Колонка уже существует, ничего страшного
                pass
            conn.commit()

    def add_or_update_user(self, user_id: int, username: str):
        """Добавляет нового пользователя или обновляет username существующего."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone() is None:
                # Пользователя нет, вставляем новую запись
                cursor.execute(
                    "INSERT INTO users (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
                print(f"Новый пользователь добавлен в SQLite: {user_id} (@{username})")
            else:
                # Пользователь есть, обновляем его username
                cursor.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?",
                    (username, user_id)
                )
                print(f"Username обновлен для пользователя: {user_id} (@{username})")
            conn.commit()


    # --- Методы для работы со статическими данными ---

    def get_all_funds(self) -> list:
        """Возвращает список всех доступных фондов."""
        print("[РЕПОЗИТОРИЙ] Запрошены все фонды.")
        return ALL_FUNDS

    def get_strategy_template(self, risk_profile: str) -> dict:
        """Возвращает шаблон стратегии по названию риск-профиля."""
        print(f"[РЕПОЗИТОРИЙ] Запрошен шаблон для '{risk_profile}'.")
        return STRATEGY_TEMPLATES.get(risk_profile)
