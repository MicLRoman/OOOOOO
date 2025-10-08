import streamlit as st
import pandas as pd
import plotly.express as px

# --- Функции-хелперы (дублируем для независимости страницы) ---
def get_first_event_per_user(df, event_name):
    if df.empty or event_name not in df['eventName'].unique():
        return pd.DataFrame()
    events = df[df['eventName'] == event_name].sort_values('timestamp')
    return events.drop_duplicates(subset=['userId'], keep='first')

def get_unique_users_for_event(df, event_name, event_data_filter=None):
    if df.empty: return set()
    subset = df[df['eventName'] == event_name]
    if event_data_filter:
        mask = subset['eventData'].apply(lambda d: isinstance(d, dict) and all(d.get(k) == v for k, v in event_data_filter.items()))
        subset = subset[mask]
    return set(subset['userId'].dropna().unique())

def safe_division(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0

st.set_page_config(page_title="Анализ гипотез", layout="wide")
st.title("🧐 Анализ гипотез")

# --- Проверка наличия данных в сессии ---
if 'filtered_events_df' not in st.session_state or st.session_state['filtered_events_df'].empty:
    st.warning("Данные для анализа отсутствуют. Пожалуйста, выберите период на главной странице.")
    st.stop()

# --- Загрузка данных из сессии ---
filtered_events_df = st.session_state['filtered_events_df']
registrations_df = st.session_state['registrations_df']

# --- Пересчет множеств пользователей для текущей страницы ---
activation_users_period = get_unique_users_for_event(filtered_events_df, 'page_view_portfolio')
intent_users_period = get_unique_users_for_event(filtered_events_df, 'click_confirm_portfolio')
final_users_period = get_unique_users_for_event(filtered_events_df, 'page_view_final')

# --- БЛОКИ АНАЛИЗА ---
with st.container(border=True):
    st.subheader("Влияние выбора цели на конверсию в намерение")
    first_goal_choices = get_first_event_per_user(filtered_events_df, 'select_goal_on_main')
    if not first_goal_choices.empty:
        first_goal_choices['goal'] = first_goal_choices['eventData'].apply(lambda x: x.get('goal'))
        goal_stats = {}
        for goal in first_goal_choices['goal'].dropna().unique():
            goal_users = set(first_goal_choices[first_goal_choices['goal'] == goal]['userId'])
            converted_users = len(intent_users_period.intersection(goal_users))
            goal_stats[goal] = {'total': len(goal_users), 'converted': converted_users, 'cr': safe_division(converted_users, len(goal_users))}
        goal_df = pd.DataFrame(goal_stats).T.sort_values('cr', ascending=False)
        st.dataframe(goal_df.style.format({'cr': '{:.1f}%'}), use_container_width=True)
    else:
        st.info("Нет данных о выборе цели.")

with st.container(border=True):
    st.subheader("Анализ Риск-профиля")
    first_risk_choices = get_first_event_per_user(filtered_events_df, 'auto_selection_risk_selected')
    if not first_risk_choices.empty:
        first_risk_choices['riskProfile'] = first_risk_choices['eventData'].apply(lambda x: x.get('riskProfile'))
        col1, col2 = st.columns([1,2])
        with col1:
            st.markdown("**Распределение по риск-профилям**")
            risk_dist = first_risk_choices['riskProfile'].value_counts()
            st.dataframe(risk_dist)
        with col2:
            st.markdown("**Конверсия в намерение по риск-профилю**")
            risk_stats = {}
            for profile in first_risk_choices['riskProfile'].dropna().unique():
                risk_users = set(first_risk_choices[first_risk_choices['riskProfile'] == profile]['userId'])
                converted_users = len(intent_users_period.intersection(risk_users))
                risk_stats[profile] = {'total_users': len(risk_users), 'converted_users': converted_users, 'intent_cr': safe_division(converted_users, len(risk_users))}
            risk_df = pd.DataFrame(risk_stats).T.sort_values('intent_cr', ascending=False)
            st.dataframe(risk_df.style.format({'intent_cr': '{:.1f}%'}), use_container_width=True)
    else:
        st.info("Нет данных о выборе риск-профиля.")

with st.container(border=True):
    st.subheader("Влияние использования редактора портфеля")
    edit_users = get_unique_users_for_event(filtered_events_df, 'click_edit_portfolio')
    if len(activation_users_period) > 0:
        activated_but_not_edited = activation_users_period - edit_users
        adoption_rate = safe_division(len(edit_users), len(activation_users_period))
        cr_with_edit = safe_division(len(intent_users_period.intersection(edit_users)), len(edit_users))
        cr_without_edit = safe_division(len(intent_users_period.intersection(activated_but_not_edited)), len(activated_but_not_edited))
        col1, col2, col3 = st.columns(3)
        col1.metric("Adoption Rate редактора", f"{adoption_rate:.1f}%")
        col2.metric("CR в намерение С редактированием", f"{cr_with_edit:.1f}%")
        col3.metric("CR в намерение БЕЗ редактирования", f"{cr_without_edit:.1f}%", delta=f"{cr_with_edit - cr_without_edit:.1f}%")

        with st.expander("Показать пользователей, использовавших редактор"):
            if edit_users:
                edit_users_df = registrations_df[registrations_df['user_id'].isin(edit_users)].copy()
                edit_users_df['Дошел до покупки'] = edit_users_df['user_id'].isin(final_users_period)
                st.dataframe(edit_users_df[['user_id', 'username', 'Дошел до покупки']], use_container_width=True)
            else:
                st.info("Нет пользователей, использовавших редактор.")
    else:
        st.info("Нет данных об активации для расчета влияния редактора.")

with st.container(border=True):
    st.subheader("Анализ фичей доверия: 'Похожие портфели'")
    similar_view_users = get_unique_users_for_event(filtered_events_df, 'switch_portfolio_view', {'view': 'similar'})
    if len(activation_users_period) > 0:
        activated_not_used_similar = activation_users_period - similar_view_users
        adoption_rate = safe_division(len(similar_view_users), len(activation_users_period))
        cr_with_similar = safe_division(len(intent_users_period.intersection(similar_view_users)), len(similar_view_users))
        cr_without_similar = safe_division(len(intent_users_period.intersection(activated_not_used_similar)), len(activated_not_used_similar))
        col1, col2, col3 = st.columns(3)
        col1.metric("Adoption Rate 'Похожих портфелей'", f"{adoption_rate:.1f}%")
        col2.metric("CR в намерение С просмотром", f"{cr_with_similar:.1f}%")
        col3.metric("CR в намерение БЕЗ просмотра", f"{cr_without_similar:.1f}%", delta=f"{cr_with_similar - cr_without_similar:.1f}%")

        with st.expander("Показать пользователей, смотревших похожие портфели"):
            if similar_view_users:
                similar_users_df = registrations_df[registrations_df['user_id'].isin(similar_view_users)].copy()
                similar_users_df['Дошел до покупки'] = similar_users_df['user_id'].isin(final_users_period)
                st.dataframe(similar_users_df[['user_id', 'username', 'Дошел до покупки']], use_container_width=True)
            else:
                st.info("Нет пользователей, смотревших похожие портфели.")
    else:
        st.info("Нет данных об активации для расчета влияния фичи 'Похожие портфели'.")
