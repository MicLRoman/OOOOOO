# portfolio_bot/api_server.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Используем правильные импорты
from database.repository import CombinedRepository
from domain.calculator import PortfolioCalculator

# --- Инициализация бэкенд-логики ---
repository = CombinedRepository()
calculator = PortfolioCalculator(repository)

# Правильный расчет пути к папке с фронтендом
static_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'portfolio_mini_app'))

print("---")
print(f"✅ Сервер запущен. Рабочая директория: {os.getcwd()}")
print(f"✅ Путь к файлам фронтенда определен как: {static_folder_path}")
print("---")


# --- Создание Flask-приложения ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    """
    Отдает запрошенный файл из папки с фронтендом.
    """
    if not os.path.isdir(static_folder_path):
        return "Ошибка: Директория со статическими файлами не найдена.", 500
    
    file_path = os.path.join(static_folder_path, path)
    if not os.path.exists(file_path):
         return f"Файл не найден: {path}", 404

    # --- ИСПРАВЛЕНИЕ ОШИБКИ MIME TYPE ---
    # Явно указываем правильный MIME-тип для JavaScript файлов,
    # чтобы браузер не блокировал их загрузку.
    if path.endswith('.js'):
        return send_from_directory(static_folder_path, path, mimetype='application/javascript')
    
    # Для всех остальных файлов оставляем автоматическое определение
    return send_from_directory(static_folder_path, path)


@app.route('/api/calculate', methods=['POST'])
def calculate_portfolio_endpoint():
    """
    Точка входа (endpoint) для расчетов.
    """
    try:
        data = request.json
        print(f"Получен API-запрос на /api/calculate: {data}")
        
        result = calculator.calculate(
            risk_profile=data.get('riskProfile'),
            amount=int(data.get('amount')),
            term=int(data.get('term')),
            selected_funds=data.get('selected_funds')
        )
        return jsonify(result)

    except Exception as e:
        print(f"Произошла ошибка в /api/calculate: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/funds', methods=['GET'])
def get_all_funds_endpoint():
    """
    Endpoint для получения списка всех фондов.
    """
    try:
        all_funds = repository.get_all_funds()
        return jsonify(all_funds)
    except Exception as e:
        print(f"Произошла ошибка в /api/funds: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)

