import streamlit as st
import pandas as pd

# --- Функции-хелперы ---
def get_first_event_per_user(df, event_name):
    if df.empty or event_name not in df['eventName'].unique():
        return pd.DataFrame()
    events = df[df['eventName'] == event_name].sort_values('timestamp')
    return events.drop_duplicates(subset=['userId'], keep='first')

def get_unique_users_for_event(df, event_name):
    if df.empty: return set()
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

def safe_division(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0

st.set_page_config(page_title="Психографический портрет", layout="wide")
st.title("🧠 Психографический портрет")
st.markdown("Анализ ответов пользователей из опроса.")

if 'filtered_events_df' not in st.session_state or st.session_state['filtered_events_df'].empty:
    st.warning("Данные для анализа отсутствуют. Пожалуйста, выберите период на главной странице.")
    st.stop()

filtered_events_df = st.session_state['filtered_events_df']
intent_users_period = get_unique_users_for_event(filtered_events_df, 'click_confirm_portfolio')

first_surveys = get_first_event_per_user(filtered_events_df, 'submit_survey')
if not first_surveys.empty:
    tab1, tab2 = st.tabs(["Общее распределение", "Конверсия по сегментам"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Тест Канемана")
            kahneman_data = first_surveys['eventData'].apply(lambda x: x.get('kahnemanChoice')).value_counts()
            st.bar_chart(kahneman_data)
            st.subheader("Опыт инвестирования")
            exp_data = first_surveys['eventData'].apply(lambda x: x.get('experience')).value_counts()
            st.bar_chart(exp_data)
        with col2:
            st.subheader("Возраст")
            age_data = first_surveys['eventData'].apply(lambda x: x.get('age')).value_counts()
            st.bar_chart(age_data)
            st.subheader("Чем занимаетесь")
            activities_list = first_surveys['eventData'].apply(lambda x: x.get('activities', [])).explode().dropna()
            activities_data = activities_list.value_counts()
            st.bar_chart(activities_data)
    with tab2:
        st.subheader("Конверсия в намерение по сегментам")
        survey_users_df = first_surveys[['userId', 'eventData']].copy()
        survey_users_df['age'] = survey_users_df['eventData'].apply(lambda x: x.get('age'))
        survey_users_df['experience'] = survey_users_df['eventData'].apply(lambda x: x.get('experience'))
        
        age_groups = survey_users_df.groupby('age')['userId'].apply(set).reset_index(name='user_set')
        age_groups['total'] = age_groups['user_set'].apply(len)
        age_groups['converted'] = age_groups['user_set'].apply(lambda x: len(x.intersection(intent_users_period)))
        age_groups['cr'] = age_groups.apply(lambda row: safe_division(row['converted'], row['total']), axis=1)
        st.markdown("**По возрасту**")
        st.dataframe(age_groups[['age', 'total', 'converted', 'cr']].style.format({'cr': '{:.1f}%'}), use_container_width=True)

        exp_groups = survey_users_df.groupby('experience')['userId'].apply(set).reset_index(name='user_set')
        exp_groups['total'] = exp_groups['user_set'].apply(len)
        exp_groups['converted'] = exp_groups['user_set'].apply(lambda x: len(x.intersection(intent_users_period)))
        exp_groups['cr'] = exp_groups.apply(lambda row: safe_division(row['converted'], row['total']), axis=1)
        st.markdown("**По опыту**")
        st.dataframe(exp_groups[['experience', 'total', 'converted', 'cr']].style.format({'cr': '{:.1f}%'}), use_container_width=True)
else:
    st.info("Нет данных из опросов для построения портрета.")
