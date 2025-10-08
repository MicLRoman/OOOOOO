import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import datetime

# --- Функции для загрузки и обработки данных ---

@st.cache_data
def load_user_registrations(db_path):
    """Загружает данные о регистрациях из SQLite."""
    try:
        with sqlite3.connect(db_path, uri=True) as conn:
            df = pd.read_sql_query("SELECT user_id, username FROM users", conn)
            df['user_id'] = df['user_id'].astype(str)
        return df
    except Exception as e:
        st.error(f"Ошибка при чтении файла portfolio_bot.db: {e}")
        return pd.DataFrame(columns=['user_id', 'username'])

@st.cache_data
def load_product_events(json_path):
    """Загружает и обрабатывает события из JSON-файла."""
    try:
        df = pd.read_json(json_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        if df['timestamp'].dt.tz is None:
             df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        else:
             df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        df.dropna(subset=['timestamp'], inplace=True)
        df = df[df['userId'] != 'unknown_user'].copy()
        df['userId'] = df['userId'].astype(str)
        return df
    except Exception as e:
        st.error(f"Ошибка при чтении файла events_dump.json: {e}")
        return pd.DataFrame()

# --- Функции-хелперы ---
def get_unique_users_for_event(df, event_name):
    if df.empty: return set()
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

def safe_division(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0

# --- Основная часть приложения ---

st.set_page_config(page_title="Главная | Аналитика", layout="wide", initial_sidebar_state="expanded")

st.title("📊 Сводный дашборд")
st.markdown("Ключевые метрики, воронка и общая активность.")

# --- Загрузка и предварительная фильтрация данных ---
DB_PATH = "portfolio_bot.db"
JSON_PATH = "events_dump.json"

if 'data_loaded' not in st.session_state:
    if os.path.exists(DB_PATH) and os.path.exists(JSON_PATH):
        
        registrations_df_full = load_user_registrations(DB_PATH)
        events_df_full = load_product_events(JSON_PATH)

        EXCLUDED_USERNAMES = ['MichaeLR_f', 'MichaeLR_s', 'GlYuchD', 'zzlaaatrr', 'neestyy']
        registrations_df = registrations_df_full[~registrations_df_full['username'].isin(EXCLUDED_USERNAMES)].copy()

        included_user_ids = set(registrations_df['user_id'])
        GLOBAL_START_DATE = pd.Timestamp("2025-09-23 00:00:00", tz='UTC')
        events_df = events_df_full[
            (events_df_full['userId'].isin(included_user_ids)) &
            (events_df_full['timestamp'] >= GLOBAL_START_DATE)
        ].copy()

        # Сохраняем обработанные данные в сессию для использования на других страницах
        st.session_state['registrations_df'] = registrations_df
        st.session_state['events_df'] = events_df
        st.session_state['registrations_df_full'] = registrations_df_full # Для поиска
        st.session_state['events_df_full'] = events_df_full # Для поиска
        st.session_state['data_loaded'] = True
        
    else:
        st.error("❌ Необходимые файлы данных не найдены!")
        st.info(f"Убедитесь, что файлы `{DB_PATH}` и `{JSON_PATH}` лежат в той же папке, что и скрипт.")
        st.stop()

# Загружаем данные из сессии
registrations_df = st.session_state['registrations_df']
events_df = st.session_state['events_df']

# --- БОКОВАЯ ПАНЕЛЬ С ФИЛЬТРАМИ ---
st.sidebar.header("Фильтры")

if not events_df.empty:
    min_ts = events_df['timestamp'].min()
    max_ts = events_df['timestamp'].max()

    filter_type = st.sidebar.radio("Выберите тип фильтра:", ("Общий период", "Суточный срез (с 8:00 МСК)"))

    if filter_type == "Суточный срез (с 8:00 МСК)":
        selected_date = st.sidebar.date_input("Дата для среза", value=max_ts.date() - datetime.timedelta(days=1), min_value=min_ts.date(), max_value=max_ts.date())
        start_datetime = pd.Timestamp(datetime.datetime.combine(selected_date, datetime.time(5,0)), tz='UTC') 
        end_datetime = start_datetime + datetime.timedelta(days=1)
    else:
        period = st.sidebar.radio("Выберите период:", ("Все время", "Последние 24 часа", "Последние 7 дней", "Последние 30 дней"))
        if period == "Последние 24 часа":
            start_datetime = max_ts - datetime.timedelta(hours=24)
        elif period == "Последние 7 дней":
            start_datetime = max_ts - datetime.timedelta(days=7)
        elif period == "Последние 30 дней":
            start_datetime = max_ts - datetime.timedelta(days=30)
        else:
            start_datetime = min_ts
        end_datetime = max_ts
    
    st.sidebar.write(f"**Анализ за период:**")
    st.sidebar.info(f"С: {start_datetime.strftime('%Y-%m-%d %H:%M')} UTC\n\nПо: {end_datetime.strftime('%Y-%m-%d %H:%M')} UTC")

    mask = (events_df['timestamp'] >= start_datetime) & (events_df['timestamp'] < end_datetime)
    filtered_events_df = events_df.loc[mask]
    st.session_state['filtered_events_df'] = filtered_events_df # Сохраняем для других страниц
else:
    st.warning("Нет данных для анализа.")
    st.stop()

# --- Расчеты и отображение ---
registered_users = set(registrations_df['user_id'])
all_intent_users = get_unique_users_for_event(events_df, 'click_confirm_portfolio')
all_final_users = get_unique_users_for_event(events_df, 'page_view_final')
acquisition_users_period = get_unique_users_for_event(filtered_events_df, 'page_view_main')
activation_users_period = get_unique_users_for_event(filtered_events_df, 'page_view_portfolio')
intent_users_period = get_unique_users_for_event(filtered_events_df, 'click_confirm_portfolio')
final_users_period = get_unique_users_for_event(filtered_events_df, 'page_view_final')

st.header("Сводная информация и продуктовая воронка")
st.subheader("Ключевые метрики (общие)")
metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Зарегистрировались в боте (с учетом фильтров)", f"{len(registered_users)} 👤")
metric_col2.metric("CR: Регистрация -> Подтверждение", f"{safe_division(len(all_intent_users), len(registered_users)):.2f}%")
metric_col3.metric("CR: Регистрация -> Финал", f"{safe_division(len(all_final_users), len(registered_users)):.2f}%")

st.subheader(f"Продуктовая воронка (за выбранный период)")
funnel_data = {'Этап': ['Привлечение', 'Активация', 'Намерение', 'Удержание'],
               'Пользователи': [len(acquisition_users_period), len(activation_users_period), len(intent_users_period), len(final_users_period)]}
funnel_df = pd.DataFrame(funnel_data)
base_for_cr = len(acquisition_users_period)
if base_for_cr > 0:
    funnel_df['CR от Привлечения'] = funnel_df['Пользователи'].apply(lambda x: (x / base_for_cr) * 100)
    funnel_df['Этап с CR'] = funnel_df.apply(lambda row: f"{row['Этап']} | CR: {row['CR от Привлечения']:.1f}%", axis=1)
else:
    funnel_df['Этап с CR'] = funnel_df['Этап']

fig_funnel = px.funnel(funnel_df, x='Пользователи', y='Этап с CR', title="Воронка от входа в приложение до покупки")
st.plotly_chart(fig_funnel, use_container_width=True)

st.divider()

st.header("🕒 Почасовая активность пользователей")
st.markdown("Гистограмма показывает количество **уникальных** пользователей, заходивших в Mini App (`page_view_main`) в каждый час.")
page_views_df = filtered_events_df[filtered_events_df['eventName'] == 'page_view_main'].copy()
if not page_views_df.empty:
    page_views_df['date_hour'] = page_views_df['timestamp'].dt.floor('H')
    hourly_activity = page_views_df.groupby('date_hour')['userId'].nunique().rename('Уникальные пользователи')
    if not hourly_activity.empty:
        full_time_range = pd.date_range(start=start_datetime.floor('H'), end=end_datetime.ceil('H'), freq='H')
        hourly_activity = hourly_activity.reindex(full_time_range, fill_value=0)
    st.bar_chart(hourly_activity, height=600)
else:
    st.info("Нет данных о посещениях ('page_view_main') для анализа активности.")

