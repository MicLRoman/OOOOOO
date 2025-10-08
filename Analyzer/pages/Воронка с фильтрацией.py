import streamlit as st
import pandas as pd
import plotly.express as px

# --- Функции-хелперы (дублируем для независимости страницы) ---
def get_unique_users_for_event(df, event_name):
    if df.empty: return set()
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

def safe_division(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0

st.set_page_config(page_title="Воронка по сегментам", layout="wide")
st.title("Воронка по сегментам")
st.markdown("Здесь вы можете отфильтровать пользователей по их ответам в опросе и посмотреть, как это влияет на метрики и воронку.")

# --- Проверка наличия данных в сессии ---
if 'events_df' not in st.session_state or 'registrations_df' not in st.session_state:
    st.warning("Данные для анализа отсутствуют. Пожалуйста, выберите период на главной странице.")
    st.stop()

# --- Загрузка данных из сессии ---
# Используем полные, но уже очищенные от тестовых юзеров и старых дат данные
events_df = st.session_state['events_df']
registrations_df = st.session_state['registrations_df']
# Используем данные, отфильтрованные по времени на главной странице
filtered_events_df_by_time = st.session_state['filtered_events_df']


# --- ФИЛЬТРЫ ПО ОПРОСУ В БОКОВОЙ ПАНЕЛИ ---
st.sidebar.header("Фильтры по сегментам")

# 1. Находим всех пользователей, кто проходил опрос
survey_events = events_df[events_df['eventName'] == 'submit_survey'].copy()
if survey_events.empty:
    st.warning("Нет данных из опросов для фильтрации.")
    st.stop()

# 2. Извлекаем данные из eventData для фильтров
survey_events['age'] = survey_events['eventData'].apply(lambda x: x.get('age'))
survey_events['experience'] = survey_events['eventData'].apply(lambda x: x.get('experience'))
survey_events['kahnemanChoice'] = survey_events['eventData'].apply(lambda x: x.get('kahnemanChoice'))
survey_events['activities'] = survey_events['eventData'].apply(lambda x: x.get('activities', []))

# 3. Создаем виджеты для фильтрации
selected_ages = st.sidebar.multiselect(
    "Возраст",
    options=survey_events['age'].dropna().unique(),
    default=[]
)
selected_experiences = st.sidebar.multiselect(
    "Опыт",
    options=survey_events['experience'].dropna().unique(),
    default=[]
)
selected_kahneman = st.sidebar.multiselect(
    "Тест Канемана",
    options=survey_events['kahnemanChoice'].dropna().unique(),
    default=[]
)
all_activities = survey_events.explode('activities')['activities'].dropna().unique()
selected_activities = st.sidebar.multiselect(
    "Деятельность",
    options=all_activities,
    default=[]
)

# 4. Фильтруем пользователей по выбранным критериям
users_in_segment = survey_events.copy()
if selected_ages:
    users_in_segment = users_in_segment[users_in_segment['age'].isin(selected_ages)]
if selected_experiences:
    users_in_segment = users_in_segment[users_in_segment['experience'].isin(selected_experiences)]
if selected_kahneman:
    users_in_segment = users_in_segment[users_in_segment['kahnemanChoice'].isin(selected_kahneman)]
if selected_activities:
    users_in_segment = users_in_segment[users_in_segment['activities'].apply(lambda x: any(item in selected_activities for item in x))]

segment_user_ids = set(users_in_segment['userId'].unique())

st.sidebar.info(f"Найдено пользователей в сегменте: {len(segment_user_ids)}")

# --- Фильтруем основные данные по выбранному сегменту ---
registrations_df_segment = registrations_df[registrations_df['user_id'].isin(segment_user_ids)]
filtered_events_df_segment = filtered_events_df_by_time[filtered_events_df_by_time['userId'].isin(segment_user_ids)]


# --- Отображение данных для сегмента ---
if filtered_events_df_segment.empty and segment_user_ids:
     st.warning("В выбранном сегменте есть пользователи, но у них нет событий за выбранный на главной странице период времени.")
elif not segment_user_ids:
    st.warning("Ни один пользователь не соответствует выбранным критериям фильтрации.")
else:
    # --- Расчет воронки для сегмента ---
    acquisition_users = get_unique_users_for_event(filtered_events_df_segment, 'page_view_main')
    activation_users = get_unique_users_for_event(filtered_events_df_segment, 'page_view_portfolio')
    intent_users = get_unique_users_for_event(filtered_events_df_segment, 'click_confirm_portfolio')
    final_users = get_unique_users_for_event(filtered_events_df_segment, 'page_view_final')
    
    st.header("Результаты для выбранного сегмента")
    
    st.subheader("Продуктовая воронка")
    funnel_data = {
        'Этап': ['Привлечение (зашли в Mini App)', 'Активация (создали портфель)', 'Намерение (подтвердили портфель)', 'Удержание (дошли до покупки)'],
        'Пользователи': [len(acquisition_users), len(activation_users), len(intent_users), len(final_users)]
    }
    funnel_df = pd.DataFrame(funnel_data)
    
    base_for_cr = len(acquisition_users)
    if base_for_cr > 0:
        funnel_df['CR от Привлечения'] = funnel_df['Пользователи'].apply(lambda x: (x / base_for_cr) * 100)
        funnel_df['Этап с CR'] = funnel_df.apply(
            lambda row: f"{row['Этап']} | CR: {row['CR от Привлечения']:.1f}%", axis=1
        )
    else:
        funnel_df['Этап с CR'] = funnel_df['Этап']

    fig_funnel = px.funnel(funnel_df, x='Пользователи', y='Этап с CR', title="Воронка от входа в приложение до покупки для сегмента")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # --- Почасовая активность для сегмента ---
    st.header("🕒 Почасовая активность пользователей в сегменте")
    page_views_df = filtered_events_df_segment[filtered_events_df_segment['eventName'] == 'page_view_main'].copy()
    if not page_views_df.empty:
        page_views_df['date_hour'] = page_views_df['timestamp'].dt.floor('H')
        hourly_activity = page_views_df.groupby('date_hour')['userId'].nunique().rename('Уникальные пользователи')
        
        if not hourly_activity.empty:
            start_datetime = st.session_state.get('start_datetime', page_views_df['timestamp'].min())
            end_datetime = st.session_state.get('end_datetime', page_views_df['timestamp'].max())
            full_time_range = pd.date_range(start=start_datetime.floor('H'), end=end_datetime.ceil('H'), freq='H')
            hourly_activity = hourly_activity.reindex(full_time_range, fill_value=0)

        st.bar_chart(hourly_activity, height=600)
    else:
        st.info("Нет данных о посещениях ('page_view_main') для анализа активности в этом сегменте.")
