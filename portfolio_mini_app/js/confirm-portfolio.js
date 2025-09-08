import { trackEvent } from './script.js';

document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_confirm_portfolio');

    // --- ИЗМЕНЕНИЕ: Теперь мы читаем полный рассчитанный портфель ---
    const portfolioData = JSON.parse(localStorage.getItem('calculatedPortfolio'));
    
    if (!portfolioData || !portfolioData.forecast) {
        document.querySelector('.container').innerHTML = '<h1>Данные о портфеле не найдены.</h1><p>Пожалуйста, вернитесь и соберите портфель заново.</p><a href="index.html" class="btn btn-main">На главную</a>';
        return;
    }

    // --- ИЗМЕНЕНИЕ: Расчеты берем напрямую из forecast ---
    const forecast = portfolioData.forecast;
    const initialAmount = portfolioData.initial_amount;

    // Берем последние значения из массивов прогноза
    const maxTotal = forecast.max[forecast.max.length - 1];
    const avgTotal = forecast.avg[forecast.avg.length - 1];
    const minTotal = forecast.min[forecast.min.length - 1];

    document.getElementById('final-max-profit').textContent = `+${(maxTotal - initialAmount).toLocaleString('ru-RU')} ₽`;
    document.getElementById('final-avg-profit').textContent = `+${(avgTotal - initialAmount).toLocaleString('ru-RU')} ₽`;
    document.getElementById('final-min-profit').textContent = `+${(minTotal - initialAmount).toLocaleString('ru-RU')} ₽`;
    
    // --- ИЗМЕНЕНИЕ: Обновляем логику отправки данных в Telegram ---
    const convertBtn = document.getElementById('convert-to-real-btn');
    const hedgeCheckbox = document.getElementById('hedge-risk-checkbox');
    
    if (convertBtn) {
        convertBtn.addEventListener('click', () => {
            const surveyData = JSON.parse(localStorage.getItem('surveyData')) || {};

            // Отправляем полное событие конверсии в аналитику
            trackEvent('click_convert_to_real', {
                hedge_risk_selected: hedgeCheckbox ? hedgeCheckbox.checked : false,
                ...portfolioData, // Добавляем все данные о портфеле
                user_survey_data: surveyData
            });
            
            // --- ИЗМЕНЕНИЕ: Просто переходим на финальную страницу ---
            window.location.href = 'final.html';

        });
    }

    // Добавляем обработчик для кнопки "Вернуться к портфелю"
    const backBtn = document.getElementById('back-to-portfolio-btn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.location.href = 'portfolio.html';
        });
    }
});

