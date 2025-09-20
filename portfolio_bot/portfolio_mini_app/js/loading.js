import { trackEvent } from './script.js';

document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_loading');

    const TOTAL_TIME = 90; // 90 секунд = 1.5 минуты
    let timeLeft = TOTAL_TIME;
    let redirectTimer = null;
    let timerInterval = null;

    const timerTextEl = document.getElementById('timer-text');
    const timerProgressEl = document.getElementById('timer-progress');
    const circleLength = 2 * Math.PI * 45; // 2 * PI * r (радиус 45 из SVG)

    // Функция для перехода на следующую страницу
    const redirectToPortfolio = () => {
        if (redirectTimer) clearTimeout(redirectTimer);
        if (timerInterval) clearInterval(timerInterval);
        window.location.href = 'portfolio.html';
    };

    // Функция для обновления таймера каждую секунду
    const updateTimer = () => {
        timeLeft--;

        // Обновляем текстовое значение
        if (timerTextEl) {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerTextEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // Обновляем круговой прогресс-бар
        if (timerProgressEl) {
            const progress = (TOTAL_TIME - timeLeft) / TOTAL_TIME;
            const offset = circleLength * (1 - progress);
            timerProgressEl.style.strokeDashoffset = offset;
        }

        if (timeLeft <= 0) {
            redirectToPortfolio();
        }
    };

    // Инициализация таймера при загрузке
    if (timerProgressEl) {
        timerProgressEl.style.strokeDasharray = circleLength;
        timerProgressEl.style.strokeDashoffset = circleLength;
    }
    // Первый вызов, чтобы сразу отобразить 1:30
    const initialMinutes = Math.floor(timeLeft / 60);
    const initialSeconds = timeLeft % 60;
    if (timerTextEl) {
       timerTextEl.textContent = `${initialMinutes}:${initialSeconds.toString().padStart(2, '0')}`;
    }
    
    // Запускаем таймеры
    redirectTimer = setTimeout(redirectToPortfolio, TOTAL_TIME * 1000);
    timerInterval = setInterval(updateTimer, 1000);

    // Назначаем обработчик на кнопку "Отправить"
    const submitBtn = document.getElementById('submit-survey-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', () => handleSubmitSurvey(redirectToPortfolio));
    }
});

// Функция сбора и отправки данных опроса
function handleSubmitSurvey(redirectCallback) {
    const age = document.querySelector('input[name="age"]:checked');
    const experience = document.querySelector('input[name="experience"]:checked');
    const psychotype = document.querySelector('input[name="psychotype"]:checked');
    const activities = document.querySelectorAll('input[name="activity"]:checked');

    if (!age || !experience || !psychotype || activities.length === 0) {
        Telegram.WebApp.showAlert('Пожалуйста, ответьте на все вопросы.');
        return;
    }

    const surveyData = {
        age: age.value,
        experience: experience.value,
        kahnemanChoice: psychotype.value, // Используем ключ kahnemanChoice для консистентности с аналитикой
        activities: Array.from(activities).map(cb => cb.value)
    };

    trackEvent('submit_survey', surveyData);
    localStorage.setItem('surveyData', JSON.stringify(surveyData));

    if (typeof redirectCallback === 'function') {
        redirectCallback();
    }
}
