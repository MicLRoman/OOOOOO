import pandas as pd
import os
import matplotlib.pyplot as plt
import datetime

# --- Конфигурация ---
# Убедитесь, что у вас установлена библиотека matplotlib: pip install matplotlib
JSON_PATH = "events_dump.json"

def analyze_editor_usage(json_path):
    """
    Загружает данные о событиях, фильтрует по использованию редактора за 24 сентября,
    выводит результат в консоль и строит почасовой график.
    """
    # Проверка наличия файла
    if not os.path.exists(json_path):
        print(f"❌ Ошибка: Файл {json_path} не найден.")
        return

    try:
        # Загрузка данных
        df = pd.read_json(json_path)
        print("✅ Файл успешно загружен.")

        # Преобразование таймстемпа для корректной сортировки
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)

        # --- ФИЛЬТР ПО ДАТЕ ---
        target_date = datetime.date(2025, 9, 24)
        df = df[df['timestamp'].dt.date == target_date]
        print(f"\n🔍 Применен фильтр по дате: {target_date.strftime('%Y-%m-%d')}\n")
        
        # Фильтрация по нужному событию
        editor_events_df = df[df['eventName'] == 'click_edit_portfolio'].copy()
        
        print("\n--- Анализ использования редактора портфеля ---\n")

        if editor_events_df.empty:
            print(f"🔴 События 'click_edit_portfolio' за {target_date.strftime('%Y-%m-%d')} не найдены.")
        else:
            count = len(editor_events_df)
            unique_users = editor_events_df['userId'].nunique()
            
            print(f"✅ Найдено событий 'click_edit_portfolio': {count}")
            print(f"✅ Уникальных пользователей, заходивших в редактор: {unique_users}\n")
            
            # Сортировка по времени для удобства
            editor_events_df = editor_events_df.sort_values('timestamp')
            
            # Вывод релевантных колонок
            display_df = editor_events_df[['timestamp', 'userId', 'platform', 'url']]
            print("Детализация по событиям:")
            print(display_df.to_string())

            # --- Создание и отображение графика ---
            print("\n📈 Создание графика...")
            
            # Агрегация данных по часам для выбранного дня
            editor_events_df['hour'] = editor_events_df['timestamp'].dt.hour
            hourly_counts = editor_events_df.groupby('hour').size()
            
            # Создаем полный диапазон часов (0-23) для полноты графика
            all_hours = pd.RangeIndex(start=0, stop=24, step=1)
            hourly_counts = hourly_counts.reindex(all_hours, fill_value=0)

            plt.style.use('dark_background') # Используем темный стиль для наглядности
            fig, ax = plt.subplots(figsize=(12, 7))
            
            hourly_counts.plot(kind='bar', ax=ax, color='#66b3ff')
            
            # Настройка графика
            ax.set_title(f"Активность использования редактора по часам за {target_date.strftime('%d %B %Y')}", fontsize=16)
            ax.set_xlabel('Час дня', fontsize=12)
            ax.set_ylabel('Количество кликов на "Редактировать"', fontsize=12)
            plt.xticks(rotation=0, ha='center')
            plt.tight_layout() # Автоматически подбирает отступы
            
            print("✅ График готов. Пожалуйста, посмотрите в появившемся окне.")
            plt.show()

    except Exception as e:
        print(f"❌ Произошла ошибка при обработке файла: {e}")

# --- Запуск анализа ---
if __name__ == "__main__":
    analyze_editor_usage(JSON_PATH)

