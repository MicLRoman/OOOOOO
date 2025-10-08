import pandas as pd
import sqlite3
import os

def load_user_registrations(db_path):
    """Загружает данные о регистрациях из SQLite."""
    try:
        with sqlite3.connect(db_path, uri=True) as conn:
            df = pd.read_sql_query("SELECT user_id, username FROM users", conn)
            df['user_id'] = df['user_id'].astype(str)
        return df
    except Exception as e:
        print(f"Ошибка при чтении файла portfolio_bot.db: {e}")
        return pd.DataFrame(columns=['user_id', 'username'])

def load_product_events(json_path):
    """Загружает и обрабатывает события из JSON-файла."""
    try:
        df = pd.read_json(json_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)
        df = df[df['userId'] != 'unknown_user'].copy()
        df['userId'] = df['userId'].astype(str)
        return df
    except Exception as e:
        print(f"Ошибка при чтении файла events_dump.json: {e}")
        return pd.DataFrame()

def get_unique_users_for_event(df, event_name):
    """Возвращает множество уникальных user_id для конкретного события."""
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

def safe_division(numerator, denominator):
    """Безопасное деление."""
    return numerator / denominator if denominator > 0 else 0

def calculate_funnel_for_snapshot(events_df, registrations_df, cutoff_time_utc):
    """Рассчитывает метрики воронки для среза по времени."""
    
    filtered_events = events_df[events_df['timestamp'] < cutoff_time_utc].copy()
    
    registered_users_set = set(registrations_df['user_id'])
    
    activation_users = get_unique_users_for_event(filtered_events, 'page_view_portfolio')
    intent_users = get_unique_users_for_event(filtered_events, 'click_confirm_portfolio')
    final_users = get_unique_users_for_event(filtered_events, 'page_view_final')
    
    counts = {
        "Регистрация в боте / Заход в Mini App": len(registered_users_set),
        "Активация (создали портфель)": len(activation_users),
        "Намерение (подтвердили портфель)": len(intent_users),
        "Удержание (дошли до покупки)": len(final_users)
    }
    
    crs = {
        "Регистрация в боте / Заход в Mini App": 1.0,
        "Активация (создали портфель)": safe_division(counts["Активация (создали портфель)"], counts["Регистрация в боте / Заход в Mini App"]),
        "Намерение (подтвердили портфель)": safe_division(counts["Намерение (подтвердили портфель)"], counts["Активация (создали портфель)"]),
        "Удержание (дошли до покупки)": safe_division(counts["Удержание (дошли до покупки)"], counts["Намерение (подтвердили портфель)"])
    }
    
    return counts, crs

def create_excel_report(db_path, json_path, output_filename="report.xlsx"):
    """Создает XLSX отчет с анализом воронки и юнит-экономики."""
    
    registrations_df = load_user_registrations(db_path)
    events_df = load_product_events(json_path)
    
    if registrations_df.empty or events_df.empty:
        print("Не удалось загрузить данные, отчет не будет создан.")
        return

    cutoffs_utc = {
        "22.09.2025 08:00": pd.Timestamp('2025-09-22 05:00:00+00:00'),
        "23.09.2025 08:00": pd.Timestamp('2025-09-23 05:00:00+00:00'),
        "24.09.2025 08:00": pd.Timestamp('2025-09-24 05:00:00+00:00')
    }
    
    funnel_stages = [
        "Регистрация в боте / Заход в Mini App",
        "Активация (создали портфель)",
        "Намерение (подтвердили портфель)",
        "Удержание (дошли до покупки)"
    ]
    
    final_df = pd.DataFrame({"Этап": funnel_stages})
    
    last_snapshot_counts = {}

    for date_str, cutoff in cutoffs_utc.items():
        counts, crs = calculate_funnel_for_snapshot(events_df, registrations_df, cutoff)
        final_df[f"{date_str} (Кол-во)"] = [counts.get(stage, 0) for stage in funnel_stages]
        final_df[f"{date_str} (CR)"] = [crs.get(stage, 0) for stage in funnel_stages]
        if cutoff == max(cutoffs_utc.values()):
             last_snapshot_counts = counts

    # --- Юнит-экономика и доп. метрики ---
    all_time_registered_users = set(registrations_df['user_id'])
    all_time_acquisition_users = get_unique_users_for_event(events_df, 'page_view_main')
    not_entered_count = len(all_time_registered_users - all_time_acquisition_users)
    
    cpc = 32.33 
    
    acquisition_count = last_snapshot_counts.get("Регистрация в боте / Заход в Mini App", 0)
    total_spend = cpc * acquisition_count
    final_customer_count = last_snapshot_counts.get("Удержание (дошли до покупки)", 0)
    
    cac = safe_division(total_spend, final_customer_count) if final_customer_count > 0 else "Нет клиентов"

    unit_economics_data = {
        "Метрика": [
            "Стоимость клика (CPC)",
            "Кол-во привлеченных пользователей (Acquisition)",
            "Общие расходы на привлечение",
            "Кол-во клиентов (дошли до покупки)",
            "Стоимость привлечения клиента (CAC)",
            "Зарегистрировались, но не зашли в Mini App"
        ],
        "Значение": [
            cpc,
            acquisition_count,
            total_spend,
            final_customer_count,
            cac,
            not_entered_count
        ]
    }
    unit_economics_df = pd.DataFrame(unit_economics_data)
    
    with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, sheet_name='Воронка', index=False)
        unit_economics_df.to_excel(writer, sheet_name='Юнит-экономика', index=False)

        workbook = writer.book
        funnel_sheet = writer.sheets['Воронка']
        unit_sheet = writer.sheets['Юнит-экономика']

        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
        percent_format = workbook.add_format({'num_format': '0.0%'})
        currency_format = workbook.add_format({'num_format': '#,##0.00 ₽'})

        for col_num, value in enumerate(final_df.columns.values):
            funnel_sheet.write(0, col_num, value, header_format)
            if '(CR)' in value:
                funnel_sheet.set_column(col_num, col_num, 15, percent_format)
            elif '(Кол-во)' in value:
                 funnel_sheet.set_column(col_num, col_num, 15)
            else:
                 funnel_sheet.set_column(col_num, col_num, 45)
        
        for col_num, value in enumerate(unit_economics_df.columns.values):
            unit_sheet.write(0, col_num, value, header_format)
        
        unit_sheet.set_column('A:A', 45)
        unit_sheet.set_column('B:B', 20)
        
        unit_sheet.write('B2', cpc, currency_format)
        unit_sheet.write('B4', total_spend, currency_format)
        if isinstance(cac, (int, float)):
             unit_sheet.write('B6', cac, currency_format)


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    DB_PATH = os.path.join(script_dir, "portfolio_bot.db")
    JSON_PATH = os.path.join(script_dir, "events_dump.json")
    
    if os.path.exists(DB_PATH) and os.path.exists(JSON_PATH):
        create_excel_report(DB_PATH, JSON_PATH)
        print("Отчет 'report.xlsx' успешно создан.")
    else:
        print(f"Не найдены файлы данных. Проверьте пути:\nDB: {DB_PATH}\nJSON: {JSON_PATH}")

