import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Функции-хелперы (дублируем для независимости страницы) ---
def get_unique_users_for_event(df, event_name):
    if df.empty: return set()
    return set(df[df['eventName'] == event_name]['userId'].dropna().unique())

def safe_division(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0

st.set_page_config(page_title="Бенчмарки", layout="wide")
st.title("Сравнение с бенчмарком и Unit-экономика")

# --- Проверка наличия данных в сессии ---
if 'filtered_events_df' not in st.session_state or 'registrations_df' not in st.session_state:
    st.warning("Данные для анализа отсутствуют. Пожалуйста, выберите период на главной странице.")
    st.stop()

# --- Загрузка данных из сессии ---
filtered_events_df = st.session_state['filtered_events_df']
registrations_df = st.session_state['registrations_df']
events_df = st.session_state['events_df'] 

# --- Расчет фактических данных по воронке ---
registered_users = set(registrations_df['user_id'])
acquisition_users = get_unique_users_for_event(filtered_events_df, 'page_view_main')
activation_users = get_unique_users_for_event(filtered_events_df, 'page_view_portfolio')
intent_users = get_unique_users_for_event(filtered_events_df, 'click_confirm_portfolio')
final_users = get_unique_users_for_event(filtered_events_df, 'page_view_final')

# --- Расширение воронки на основе бенчмарков ---
st.header("Расширенная воронка продаж")

# Бенчмарки
BENCHMARK_CR_FINAL_TO_GU = 23.8  # Предоставлено вами
BENCHMARK_CR_GU_TO_APP = 28.6     # Рассчитано из photo_2...49.jpg
BENCHMARK_CR_APP_TO_PURCHASE = 96.0 # Рассчитано из photo_1...49.jpg

# Прогнозные значения
num_gu_registrations = len(final_users) * (BENCHMARK_CR_FINAL_TO_GU / 100)
num_applications = num_gu_registrations * (BENCHMARK_CR_GU_TO_APP / 100)
num_purchases = num_applications * (BENCHMARK_CR_APP_TO_PURCHASE / 100)

# Данные для таблицы и графика
funnel_data = {
    'Этап': [
        '1. Зашли в Mini App (Привлечение)', 
        '2. Создали портфель (Активация)', 
        '3. Подтвердили портфель (Намерение)', 
        '4. Дошли до покупки (Финал)', 
        '5. Регистрация в ГУ (Прогноз)',
        '6. Оформили заявку (Прогноз)', 
        '7. Купили (Прогноз)'
    ],
    'Пользователи': [
        len(acquisition_users), 
        len(activation_users), 
        len(intent_users), 
        len(final_users), 
        num_gu_registrations,
        num_applications, 
        num_purchases
    ]
}
funnel_df = pd.DataFrame(funnel_data)
funnel_df['Пользователи'] = funnel_df['Пользователи'].round(1)

total_registered = len(registered_users)
funnel_df['CR от Регистрации'] = funnel_df['Пользователи'].apply(lambda x: safe_division(x, total_registered))

st.dataframe(
    funnel_df.style.format({'Пользователи': '{:.2f}', 'CR от Регистрации': '{:.2f}%'}),
    use_container_width=True
)

with st.expander("Показать формулы и логику расчета воронки"):
    st.markdown("""
    **Логика расчета прогнозных значений:**
    - Мы берем количество пользователей, дошедших до этапа **'Финал'** (`page_view_final`), и последовательно применяем к ним бенчмарк-конверсии.
    
    **1. Прогноз по Регистрациям в ГУ:**
    - **Бенчмарк CR (Финал -> Регистрация ГУ):** `23.8%` (указано вами).
    - **Формула:** """)
    st.latex(r'''
    \text{Кол-во ГУ} = \text{Пользователи 'Финал'} \times 23.8\%
    ''')
    st.markdown(f"**Расчет:** `{len(final_users)} * 0.238 = {num_gu_registrations:.2f}`")

    st.markdown("""
    **2. Прогноз по Заявкам:**
    - **Бенчмарк CR (ГУ -> Заявка):** `28.6%` (рассчитано как среднее из `photo_2_..._49.jpg`).
    - **Формула:** """)
    st.latex(r'''
    \text{Кол-во заявок} = \text{Прогнозное кол-во ГУ} \times 47.0\%
    ''')
    st.markdown(f"**Расчет:** `{num_gu_registrations:.2f} * 0.47 = {num_applications:.2f}`")

    st.markdown("""
    **3. Прогноз по Покупкам (Клиентам):**
    - **Бенчмарк CR (Заявка -> Покупка):** `96.0%` (из строки 'Paid performance' в `photo_1_..._49.jpg`).
    - **Формула:** """)
    st.latex(r'''
    \text{Кол-во покупок} = \text{Прогнозное кол-во заявок} \times 96.0\%
    ''')
    st.markdown(f"**Расчет:** `{num_applications:.2f} * 0.96 = {num_purchases:.2f}`")
    
st.divider()

# --- Unit-экономика ---
st.header("Unit-экономика")

# Расчет альтернативной стоимости рекламы
benchmark_cpc_for_ad_spend = 33
ad_spend_from_cpc = benchmark_cpc_for_ad_spend * len(registered_users)

ad_spend = st.number_input(
    "Стоимость рекламы, ₽", 
    value=7000, 
    key="ad_spend_input",
    help=f"Вы можете подставить сюда расчетное значение, основанное на бенчмарке CPC (33 ₽) и общем кол-ве регистраций в боте. Расчетное значение: {ad_spend_from_cpc:,.0f} ₽ (33 ₽ * {len(registered_users)} регистраций)"
)

# Расчеты
cpr = (ad_spend / total_registered) if total_registered > 0 else 0
cpa = (ad_spend / num_applications) if num_applications > 0 else 0
cac = (ad_spend / num_purchases) if num_purchases > 0 else 0

# Расчет бенчмарков по вашим формулам
benchmark_cpr_avg = ((47758/1107) + (63612/1300) + (132589/2412) + (75246/2194)) / 4
benchmark_cpa_avg = (15919 + 63612 + 22098 + 10749) / 4
benchmark_cac_avg = ((47758/2) + (63612/2) + (132589/1) + (75246/1)) / 4

col1, col2 = st.columns(2)

with col1:
    st.subheader("Наши показатели (Прогноз)")
    st.metric(label="Стоимость регистрации (CPR)", value=f"{cpr:,.2f} ₽")
    st.metric(label="Стоимость заявки (CPA)", value=f"{cpa:,.2f} ₽")
    st.metric(label="Стоимость клиента (CAC)", value=f"{cac:,.2f} ₽")

with col2:
    st.subheader("Бенчмарки")
    st.metric(label="Средний CPC (визита) по бенчмарку", value=f"{benchmark_cpr_avg:,.2f} ₽")
    st.metric(label="Средний CPA (заявки) по бенчмарку", value=f"{benchmark_cpa_avg:,.2f} ₽")
    st.metric(label="Средний CAC (клиента) по бенчмарку", value=f"{benchmark_cac_avg:,.2f} ₽")

with st.expander("Показать формулы и логику расчета Unit-экономики"):
    st.markdown("""
    **1. Наша стоимость регистрации (CPR - Cost Per Registration):**
    - **Формула:**
    """)
    st.latex(r'''
    \text{CPR} = \frac{\text{Стоимость рекламы}}{\text{Кол-во регистраций в боте}}
    ''')
    st.markdown(f"**Расчет:** `{cpr:,.2f} ₽ = {ad_spend} ₽ / {total_registered}`")

    st.markdown("""
    **2. Наша стоимость заявки (CPA):**
    - **Формула:**
    """)
    st.latex(r'''
    \text{CPA} = \frac{\text{Стоимость рекламы}}{\text{Прогнозное кол-во заявок}}
    ''')
    st.markdown(f"**Расчет:** `{cpa:,.2f} ₽ = {ad_spend} ₽ / {num_applications:.2f}`")

    st.markdown("""
    **3. Наша стоимость клиента (CAC):**
    - **Формула:**
    """)
    st.latex(r'''
    CAC = \frac{\text{Стоимость рекламы}}{\text{Прогнозное кол-во клиентов}}
    ''')
    st.markdown(f"**Расчет:** `{cac:,.2f} ₽ = {ad_spend} ₽ / {num_purchases:.2f}`")

    st.markdown("---")

    st.markdown("""
    **4. Средний CPC (стоимость визита) по бенчмарку:**
    - **Источник:** `photo_2_..._49.jpg`.
    - **Формула:**
    """)
    st.latex(r'''
    \text{Средний CPC} = \frac{\sum (\text{Расход} / \text{Визиты})}{N}
    ''')
    st.markdown(f"**Расчет:** `((47758/1107) + ... + (75246/2194)) / 4 = {benchmark_cpr_avg:,.2f} ₽`")

    st.markdown("""
    **5. Средний CPA (стоимость заявки) по бенчмарку:**
    - **Источник:** `photo_2_..._49.jpg`, столбец "CPA ГУ".
    - **Формула:**
    """)
    st.latex(r'''
    \text{Средний CPA} = \frac{\text{Сумма всех CPA ГУ}}{N}
    ''')
    st.markdown(f"**Расчет:** `(15919 + 63612 + 22098 + 10749) / 4 = {benchmark_cpa_avg:,.2f} ₽`")

    st.markdown("""
    **6. Средний CAC (стоимость клиента) по бенчмарку:**
    - **Источник:** `photo_2_..._49.jpg`.
    - **Формула:**
    """)
    st.latex(r'''
    \text{Средний CAC} = \frac{\sum (\text{Расход} / \text{Продажи})}{N}
    ''')
    st.markdown(f"**Расчет:** `((47758/2) + ... + (75246/1)) / 4 = {benchmark_cac_avg:,.2f} ₽`")

