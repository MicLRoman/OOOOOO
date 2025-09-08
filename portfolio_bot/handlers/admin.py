from telebot import TeleBot
from datetime import datetime, timedelta
from collections import Counter
from io import BytesIO
import json

# --- Хелперы для анализа ---
def get_unique_users_for_event(docs, event_name):
    """Возвращает множество уникальных user_id для конкретного события."""
    return set(
        doc.to_dict().get('userId') for doc in docs 
        if doc.to_dict().get('eventName') == event_name
    )

def safe_division(numerator, denominator):
    """Безопасное деление для расчета конверсий."""
    return (numerator / denominator * 100) if denominator > 0 else 0

# --- Основная функция регистрации обработчиков ---
def register_admin_handlers(bot: TeleBot, db, app_id, admin_ids):

    @bot.message_handler(commands=['get_db_events'])
    def get_db_dump(message):
        """Отправляет все события из Firestore в виде JSON файла."""
        if message.from_user.id not in admin_ids: return
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return
        try:
            bot.send_message(message.chat.id, "⏳ Собираю все события... Это может занять некоторое время.")
            
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            docs = events_ref.stream()
            
            all_events = []
            for doc in docs:
                event_data = doc.to_dict()
                # Конвертируем timestamp в строку, если это объект datetime
                if 'timestamp' in event_data and hasattr(event_data['timestamp'], 'isoformat'):
                    event_data['timestamp'] = event_data['timestamp'].isoformat()
                all_events.append(event_data)

            if not all_events:
                bot.send_message(message.chat.id, "Событий пока нет.")
                return

            json_data = json.dumps(all_events, indent=2, ensure_ascii=False).encode('utf-8')
            file_stream = BytesIO(json_data)
            file_stream.name = 'events.json'

            bot.send_document(message.chat.id, file_stream, caption=f"✅ Готово! Выгружено {len(all_events)} событий.")

        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при выгрузке базы данных: {e}")

    # --- НОВЫЙ, МОЩНЫЙ ОТЧЕТ ---
    @bot.message_handler(commands=['get_report'], func=lambda message: message.from_user.id in admin_ids)
    def get_full_report(message):
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return

        try:
            bot.send_message(message.chat.id, "⏳ Собираю данные и готовлю отчет за последние 7 дней...")
            # Получаем данные за последнюю неделю
            start_date = datetime.utcnow() - timedelta(days=7)
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            query = events_ref.where('timestamp', '>=', start_date)
            docs = list(query.stream())
            
            if not docs:
                bot.reply_to(message, "За последние 7 дней не было событий для анализа.")
                return

            # --- 1. Гипотеза: Пользователи заинтересованы в продукте ---
            main_page_users = get_unique_users_for_event(docs, 'page_view_main')
            auto_selection_users = get_unique_users_for_event(docs, 'click_auto_selection')
            cr_main_to_constructor = safe_division(len(auto_selection_users), len(main_page_users))
            
            h1_report = (
                f"Гипотеза 1: Пользователи заинтересованы в продукте\n"
                f"  - CR с главной в конструктор: *{cr_main_to_constructor:.1f}%* ({len(auto_selection_users)} из {len(main_page_users)})\n"
            )

            # --- 2. Гипотеза: Пользователям важна персонализация ---
            portfolio_view_users = get_unique_users_for_event(docs, 'page_view_portfolio')
            edit_click_users = get_unique_users_for_event(docs, 'click_edit_portfolio')
            save_edit_users = get_unique_users_for_event(docs, 'click_save_portfolio_edit')
            edit_adoption_rate = safe_division(len(edit_click_users), len(portfolio_view_users))
            save_rate = safe_division(len(save_edit_users), len(edit_click_users))

            h2_report = (
                f"Гипотеза 2: Персонализация важна\n"
                f"  - Переход в редактор: *{edit_adoption_rate:.1f}%* ({len(edit_click_users)} из {len(portfolio_view_users)})\n"
                f"  - Сохраняют изменения: *{save_rate:.1f}%* ({len(save_edit_users)} из {len(edit_click_users)})\n"
            )

            # --- 3. Гипотеза: Люди предпочитают обучаться на практике ---
            demo_clicks = len([d for d in docs if d.to_dict().get('eventName') == 'click_demo_portfolio'])
            auto_clicks = len([d for d in docs if d.to_dict().get('eventName') == 'click_auto_selection'])

            h3_report = (
                f"Гипотеза 3: Обучение на практике\n"
                f"  - Выбор пути: Автоподбор ({auto_clicks}) vs Демо ({demo_clicks})\n"
            )

            # --- 4 & 5. Гипотезы: Фичи доверия (История и Соц. доказательство) ---
            history_clicks = len([d for d in docs if d.to_dict().get('eventName') == 'switch_chart_mode' and d.to_dict().get('eventData', {}).get('mode') != 'future'])
            similar_clicks = len([d for d in docs if d.to_dict().get('eventName') == 'switch_portfolio_view' and d.to_dict().get('eventData', {}).get('view') == 'similar'])
            
            h45_report = (
                f"Гипотезы 4/5: Фичи доверия\n"
                f"  - Смотрят историю графика: *{history_clicks}* раз\n"
                f"  - Смотрят похожие портфели: *{similar_clicks}* раз\n"
            )
            
            # --- 6. Гипотеза: "Покрытие рисков" стимулирует к конверсии ---
            final_conversion_events = [d.to_dict() for d in docs if d.to_dict().get('eventName') == 'click_convert_to_real']
            total_conversions = len(final_conversion_events)
            hedge_selected_conversions = sum(1 for e in final_conversion_events if e.get('eventData', {}).get('hedge_risk_selected'))
            hedge_adoption_rate = safe_division(hedge_selected_conversions, total_conversions)

            h6_report = (
                f"Гипотеза 6: Покрытие рисков\n"
                f"  - Выбирают опцию 'покрыть риск': *{hedge_adoption_rate:.1f}%* ({hedge_selected_conversions} из {total_conversions})\n"
            )
            
            # --- ОБЩАЯ ВОРОНКА КОНВЕРСИИ ---
            confirm_page_users = get_unique_users_for_event(docs, 'page_view_confirm_portfolio')
            final_conversion_users = get_unique_users_for_event(docs, 'click_convert_to_real')
            full_cr = safe_division(len(final_conversion_users), len(main_page_users))
            
            funnel_report = (
                f"🏁 *ОБЩАЯ ВОРОНКА (за 7 дней)*\n"
                f"  - 1. Увидели гл. экран: *{len(main_page_users)}*\n"
                f"  - 2. Начали автоподбор: *{len(auto_selection_users)}* ({safe_division(len(auto_selection_users), len(main_page_users)):.1f}%)\n"
                f"  - 3. Увидели портфель: *{len(portfolio_view_users)}* ({safe_division(len(portfolio_view_users), len(auto_selection_users)):.1f}%)\n"
                f"  - 4. Перешли к подтверждению: *{len(confirm_page_users)}* ({safe_division(len(confirm_page_users), len(portfolio_view_users)):.1f}%)\n"
                f"  - 5. *Сконвертировались*: *{len(final_conversion_users)}* ({safe_division(len(final_conversion_users), len(confirm_page_users)):.1f}%)\n"
                f"  - *Итоговая конверсия*: *{full_cr:.2f}%*\n"
            )
            
            # --- АНАЛИЗ АУДИТОРИИ КОНВЕРСИЙ ---
            if final_conversion_events:
                surveyed_events = [e for e in final_conversion_events if e.get('eventData', {}).get('user_age') is not None]
                if surveyed_events:
                    ages = Counter(e['eventData']['user_age'] for e in surveyed_events).most_common()
                    experiences = Counter(e['eventData']['user_experience'] for e in surveyed_events).most_common()
                    all_activities = [act for e in surveyed_events if 'user_activities' in e['eventData'] for act in e['eventData']['user_activities']]
                    activities_counts = Counter(all_activities).most_common()

                    def format_counter(counter_list):
                        return ", ".join([f"'{k}': {v}" for k, v in counter_list]) if counter_list else "Нет данных"

                    survey_report = (
                        f"🕵️ *ПОРТРЕТ КОНВЕРСИИ (по данным опроса)*\n"
                        f"  - Возраст: `{format_counter(ages)}`\n"
                        f"  - Опыт: `{format_counter(experiences)}`\n"
                        f"  - Деятельность: `{format_counter(activities_counts)}`\n"
                    )
                else:
                    survey_report = "🕵️ *ПОРТРЕТ КОНВЕРСИИ*\n  - Пользователи, прошедшие опрос и сконвертировавшиеся, отсутствуют.\n"
            else:
                survey_report = "🕵️ *ПОРТРЕТ КОНВЕРСИИ*\n  - Пока нет данных для анализа.\n"

            # --- Сборка и отправка итогового сообщения ---
            full_report_text = (
                f"📊 *Аналитический отчет за 7 дней*\n\n"
                f"{h1_report}\n"
                f"{h2_report}\n"
                f"{h3_report}\n"
                f"{h45_report}\n"
                f"{h6_report}\n"
                f"---\n"
                f"{funnel_report}\n"
                f"---\n"
                f"{survey_report}"
            )
            
            bot.reply_to(message, full_report_text, parse_mode='Markdown')

        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при создании отчета: {e}")

    # === НОВАЯ КОМАНДА ДЛЯ ОЧИСТКИ БАЗЫ ДАННЫХ ===
    @bot.message_handler(commands=['clear_db'], func=lambda message: message.from_user.id in admin_ids)
    def clear_database(message):
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return

        # Защита от случайного удаления
        if "confirm" not in message.text.lower():
            bot.reply_to(
                message,
                "🛑 *ВНИМАНИЕ!* Это действие необратимо удалит все события из базы данных.\n"
                "Для подтверждения, пожалуйста, отправьте команду еще раз в формате:\n"
                "`/clear_db confirm`",
                parse_mode='Markdown'
            )
            return

        try:
            bot.reply_to(message, "⏳ Начинаю очистку базы данных... Это может занять некоторое время.")
            
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            docs = events_ref.stream()
            
            deleted_count = 0
            batch = db.batch()
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1
                # Отправляем батч каждые 500 документов
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = db.batch()
            
            # Отправляем оставшиеся документы
            if deleted_count % 500 != 0:
                 batch.commit()

            success_message = f"✅ *База данных успешно очищена.*\nУдалено документов: *{deleted_count}*"
            bot.reply_to(message, success_message, parse_mode='Markdown')

        except Exception as e:
            bot.reply_to(message, f"❌ Произошла ошибка при очистке базы данных: {e}")