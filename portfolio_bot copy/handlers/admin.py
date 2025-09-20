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
        if doc.to_dict().get('eventName') == event_name and doc.to_dict().get('userId')
    )

def safe_division(numerator, denominator):
    """Безопасное деление для расчета конверсий в процентах."""
    return (numerator / denominator * 100) if denominator > 0 else 0

def get_docs_by_event(docs, event_name):
    """Возвращает список словарей для конкретного события."""
    return [
        doc.to_dict() for doc in docs 
        if doc.to_dict().get('eventName') == event_name
    ]

def get_users_by_event_data(docs, event_name, data_key):
    """
    Группирует user_id по значению в eventData.
    Возвращает словарь: { 'значение': {id1, id2}, ... }
    """
    user_groups = {}
    for doc in docs:
        event = doc.to_dict()
        if event.get('eventName') == event_name:
            event_data = event.get('eventData', {})
            key_value = event_data.get(data_key)
            user_id = event.get('userId')
            if key_value and user_id:
                if key_value not in user_groups:
                    user_groups[key_value] = set()
                user_groups[key_value].add(user_id)
    return user_groups

# --- Основная функция регистрации обработчиков ---
def register_admin_handlers(bot: TeleBot, db, app_id, admin_ids):

    @bot.message_handler(commands=['get_db_events'])
    def get_db_dump(message):
        # (этот обработчик остается без изменений)
        if message.from_user.id not in admin_ids: return
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return
        try:
            bot.send_message(message.chat.id, "⏳ Собираю все события...")
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            docs = events_ref.stream()
            all_events = []
            for doc in docs:
                event_data = doc.to_dict()
                if 'timestamp' in event_data and hasattr(event_data['timestamp'], 'isoformat'):
                    event_data['timestamp'] = event_data['timestamp'].isoformat()
                all_events.append(event_data)
            if not all_events:
                bot.send_message(message.chat.id, "Событий пока нет.")
                return
            json_data = json.dumps(all_events, indent=2, ensure_ascii=False).encode('utf-8')
            file_stream = BytesIO(json_data)
            file_stream.name = 'events_dump.json'
            bot.send_document(message.chat.id, file_stream, caption=f"✅ Выгружено {len(all_events)} событий.")
        except Exception as e:
            bot.reply_to(message, f"Ошибка при выгрузке: {e}")


    @bot.message_handler(commands=['get_report'], func=lambda message: message.from_user.id in admin_ids)
    def get_full_report(message):
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return

        try:
            bot.send_message(message.chat.id, "⏳ Собираю данные и готовлю отчет за последние 7 дней...")
            start_date = datetime.utcnow() - timedelta(days=7)
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            query = events_ref.where('timestamp', '>=', start_date)
            docs = list(query.stream())
            
            if not docs:
                bot.reply_to(message, "За последние 7 дней не было событий для анализа.")
                return

            # --- 1. ОСНОВНАЯ ВОРОНКА ---
            acquisition_users = get_unique_users_for_event(docs, 'page_view_main')
            activation_users = get_unique_users_for_event(docs, 'page_view_portfolio')
            intent_users = get_unique_users_for_event(docs, 'click_confirm_portfolio')

            funnel_report = (
                f"📊 *ОСНОВНАЯ ВОРОНКА ПРОДУКТА (за 7 дней)*\n\n"
                f"1️⃣ *Привлечение (Acquisition)*\n"
                f"   └ Увидел главный экран: *{len(acquisition_users)}* чел.\n\n"
                f"2️⃣ *Активация (Activation)*\n"
                f"   └ Успешно создал план: *{len(activation_users)}* чел.\n"
                f"   └ CR1 (в Активацию): *{safe_division(len(activation_users), len(acquisition_users)):.1f}%*\n\n"
                f"3️⃣ *Намерение (Intent)*\n"
                f"   └ Нажал «Подтвердить»: *{len(intent_users)}* чел.\n"
                f"   └ CR2 (в Намерение): *{safe_division(len(intent_users), len(activation_users)):.1f}%*\n\n"
                f"📈 *Итоговая конверсия (сквозная):* *{safe_division(len(intent_users), len(acquisition_users)):.2f}%*\n"
            )

            # --- 2. АНАЛИЗ ГИПОТЕЗ ---
            
            # --- Гипотеза: Выбор цели ---
            goal_user_groups = get_users_by_event_data(docs, 'select_goal_on_main', 'goal')
            goal_popularity = "\n".join([f"   - {g}: {len(u)} чел." for g, u in goal_user_groups.items()]) or "   - Нет данных"
            goal_influence = "\n".join([f"   - {g}: *{safe_division(len(intent_users.intersection(u)), len(u)):.1f}%*" for g, u in goal_user_groups.items()]) or "   - Нет данных"

            # --- Гипотеза: Слайдер риска ---
            risk_user_groups = get_users_by_event_data(docs, 'auto_selection_risk_selected', 'riskProfile')
            risk_popularity = "\n".join([f"   - {r}: {len(u)} чел." for r, u in risk_user_groups.items()]) or "   - Нет данных"
            risk_influence = "\n".join([f"   - {r}: *{safe_division(len(intent_users.intersection(u)), len(u)):.1f}%*" for r, u in risk_user_groups.items()]) or "   - Нет данных"

            # --- Гипотеза: Персонализация (Редактор) ---
            edit_users = get_unique_users_for_event(docs, 'click_edit_portfolio')
            editor_adoption_rate = safe_division(len(edit_users), len(activation_users))
            users_who_did_not_edit = activation_users - edit_users
            cr_with_edit = safe_division(len(intent_users.intersection(edit_users)), len(edit_users))
            cr_without_edit = safe_division(len(intent_users.intersection(users_who_did_not_edit)), len(users_who_did_not_edit))
            
            # --- Гипотеза: Фичи доверия ---
            view_switch_events = get_docs_by_event(docs, 'switch_portfolio_view')
            users_who_used_similar = {e.get('userId') for e in view_switch_events if e.get('eventData', {}).get('view') == 'similar' and e.get('userId')}
            users_who_did_not_use_similar = activation_users - users_who_used_similar
            similar_adoption_rate = safe_division(len(users_who_used_similar), len(activation_users))
            cr_with_similar = safe_division(len(intent_users.intersection(users_who_used_similar)), len(users_who_used_similar))
            cr_without_similar = safe_division(len(intent_users.intersection(users_who_did_not_use_similar)), len(users_who_did_not_use_similar))

            hypothesis_report = (
                f"🧐 *АНАЛИЗ ГИПОТЕЗ*\n\n"
                f"*Выбор цели:*\n"
                f"  *Популярность:* Распределение по целям\n{goal_popularity}\n"
                f"  *Влияние (Intent CR):*\n{goal_influence}\n\n"
                f"*Слайдер риска:*\n"
                f"  *Популярность:* Распределение по риск-профилям\n{risk_popularity}\n"
                f"  *Влияние (Intent CR):*\n{risk_influence}\n\n"
                f"*Персонализация (Редактор):*\n"
                f"  *Популярность (Adoption Rate):* *{editor_adoption_rate:.1f}%* пользователей зашли в редактор.\n"
                f"  *Влияние (Intent CR):*\n"
                f"     - С редактированием: *{cr_with_edit:.1f}%*\n"
                f"     - Без редактирования: *{cr_without_edit:.1f}%*\n\n"
                f"*Фичи доверия («Похожие портфели»):*\n"
                f"  *Популярность (Adoption Rate):* *{similar_adoption_rate:.1f}%* пользователей посмотрели фичу.\n"
                f"  *Влияние (Intent CR):*\n"
                f"     - Использовали фичу: *{cr_with_similar:.1f}%*\n"
                f"     - НЕ использовали: *{cr_without_similar:.1f}%*\n"
            )

            # --- 3. АНАЛИЗ ОПРОСА (включая психографику) ---
            survey_events = get_docs_by_event(docs, 'submit_survey')
            def format_survey_counter(data_key):
                items = [e.get('eventData', {}).get(data_key) for e in survey_events if e.get('eventData', {}).get(data_key)]
                if not items: return "   - Нет данных"
                # Обработка списков (для activities)
                if isinstance(items[0], list):
                    items = [item for sublist in items for item in sublist]
                counts = Counter(items)
                return "\n".join([f"   - {k}: {v} чел." for k, v in counts.most_common()])
            
            survey_report = (
                f"🧠 *ПСИХОГРАФИЧЕСКИЙ ПОРТРЕТ*\n\n"
                f"*Тест Канемана:*\n{format_survey_counter('kahnemanChoice')}\n\n"
                f"*Возраст:*\n{format_survey_counter('age')}\n\n"
                f"*Опыт инвестирования:*\n{format_survey_counter('experience')}\n\n"
                f"*Чем занимаетесь:*\n{format_survey_counter('activities')}\n"
            )

            # --- Сборка и отправка итогового сообщения ---
            full_report_text = f"{funnel_report}\n---\n{hypothesis_report}\n---\n{survey_report}"
            
            bot.reply_to(message, full_report_text, parse_mode='Markdown')

        except Exception as e:
            import traceback
            traceback.print_exc()
            bot.reply_to(message, f"Произошла ошибка при создании отчета: {e}")

    # (команда /clear_db остается без изменений)
    @bot.message_handler(commands=['clear_db'], func=lambda message: message.from_user.id in admin_ids)
    def clear_database(message):
        if not db:
            bot.reply_to(message, "⚠️ База данных недоступна.")
            return
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
            bot.reply_to(message, "⏳ Начинаю очистку базы данных...")
            events_ref = db.collection(f'artifacts/{app_id}/public/data/events')
            docs = events_ref.stream()
            deleted_count = 0
            batch = db.batch()
            for doc in docs:
                batch.delete(doc.reference)
                deleted_count += 1
                if deleted_count % 500 == 0:
                    batch.commit()
                    batch = db.batch()
            if deleted_count % 500 != 0:
                 batch.commit()
            success_message = f"✅ *База данных успешно очищена.*\nУдалено документов: *{deleted_count}*"
            bot.reply_to(message, success_message, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Произошла ошибка при очистке: {e}")

