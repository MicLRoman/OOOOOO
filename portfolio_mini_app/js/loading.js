import { trackEvent } from './script.js';

document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_loading');
    const submitBtn = document.getElementById('submit-survey-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmitSurvey);
    }
});

function handleSubmitSurvey() {
    // 1. Собираем данные из формы
    const age = document.querySelector('input[name="age"]:checked');
    const experience = document.querySelector('input[name="experience"]:checked');
    const activities = document.querySelectorAll('input[name="activity"]:checked');

    if (!age || !experience || activities.length === 0) {
        Telegram.WebApp.showAlert('Пожалуйста, ответьте на все вопросы.');
        return;
    }

    const surveyData = {
        age: age.value,
        experience: experience.value,
        activities: Array.from(activities).map(cb => cb.value)
    };

    // 2. Отправляем событие и сохраняем данные опроса
    trackEvent('submit_survey', surveyData);
    localStorage.setItem('surveyData', JSON.stringify(surveyData));

    // 3. Просто переходим на страницу портфеля. Расчет будет там.
    window.location.href = 'portfolio.html';
}

