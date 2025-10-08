import streamlit as st
import pandas as pd

# --- Функции-хелперы ---
def get_unique_users_for_event(df, event_name):
    if df.empty: return set()
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

st.set_page_config(page_title="Анализ пользователей", layout="wide")
st.title("👥 Анализ пользователей")
st.markdown("Сегментация по воронке и детальный просмотр пути пользователя.")

if 'data_loaded' not in st.session_state:
    st.warning("Пожалуйста, сначала загрузите данные на главной странице.")
    st.stop()

# --- Загрузка данных из сессии ---
registrations_df = st.session_state['registrations_df']
events_df = st.session_state['events_df']
registrations_df_full = st.session_state['registrations_df_full']
events_df_full = st.session_state['events_df_full']

# --- Сегментация ---
st.header("Сегментация пользователей по максимальному этапу (за все время)")

registered_users = set(registrations_df['user_id'])
all_acquisition_users = get_unique_users_for_event(events_df, 'page_view_main')
all_activation_users = get_unique_users_for_event(events_df, 'page_view_portfolio')
all_intent_users = get_unique_users_for_event(events_df, 'click_confirm_portfolio')
all_final_users = get_unique_users_for_event(events_df, 'page_view_final')

dropped_after_reg = registered_users - all_acquisition_users
dropped_after_acq = all_acquisition_users - all_activation_users
dropped_after_act = all_activation_users - all_intent_users
dropped_after_int = all_intent_users - all_final_users

tab_titles = [
    f"Только регистрация ({len(dropped_after_reg)})",
    f"Отвалились после привлечения ({len(dropped_after_acq)})",
    f"Отвалились после активации ({len(dropped_after_act)})",
    f"Отвалились после намерения ({len(dropped_after_int)})",
    f"Дошли до конца ({len(all_final_users)})"
]
tabs = st.tabs(tab_titles)
drop_off_sets = [dropped_after_reg, dropped_after_acq, dropped_after_act, dropped_after_int, all_final_users]

for i, tab in enumerate(tabs):
    with tab:
        user_subset_df = registrations_df[registrations_df['user_id'].isin(drop_off_sets[i])]
        st.dataframe(user_subset_df, use_container_width=True, height=400)

st.divider()

# --- Поиск по пользователю ---
st.header("🔍 Анализ конкретного пользователя")
username_to_find = st.text_input("Введите username для поиска (анализ по всем данным, без учета фильтров):")

if username_to_find:
    user_info = registrations_df_full[registrations_df_full['username'].str.lower() == username_to_find.lower()]
    if not user_info.empty:
        user_id = user_info['user_id'].iloc[0]
        username = user_info['username'].iloc[0]
        st.subheader(f"Отчет по пользователю: {username}")
        st.markdown(f"**User ID:** `{user_id}`")

        user_events = events_df_full[events_df_full['userId'] == user_id].sort_values('timestamp')
        if not user_events.empty:
            st.write(f"**Первая активность в продукте:** {user_events['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        else:
            st.write("**Первая активность в продукте:** Не найдена")

        stage = "Только регистрация"
        if user_id in all_acquisition_users: stage = "Привлечение (зашел в Mini App)"
        if user_id in all_activation_users: stage = "Активация (создал портфель)"
        if user_id in all_intent_users: stage = "Намерение (подтвердил портфель)"
        if user_id in all_final_users: stage = "Удержание (дошел до покупки)"
        st.write(f"**Максимальный этап воронки:** {stage}")

        st.markdown("---")
        st.write("#### Данные опроса")
        survey_event = user_events[user_events['eventName'] == 'submit_survey'].tail(1)
        if not survey_event.empty: st.json(survey_event['eventData'].iloc[0])
        else: st.info("Пользователь не проходил опрос.")

        st.write("#### Сформированный портфель (последний)")
        build_event = user_events[user_events['eventName'] == 'confirm_all_and_build'].tail(1)
        if not build_event.empty: st.json(build_event['eventData'].iloc[0])
        else: st.info("Пользователь не создавал портфель.")
    else:
        st.error("Пользователь с таким username не найден в базе данных регистраций.")
