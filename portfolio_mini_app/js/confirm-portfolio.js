import { trackEvent } from './script.js';

/**
 * Форматирует срок из месяцев в строку "36 месяцев (~3 г.)".
 */
function formatTerm(months) {
    if (!months || isNaN(months)) return '';
    months = parseInt(months, 10);
    let monthText;
    if (months % 10 === 1 && months % 100 !== 11) {
        monthText = 'месяц';
    } else if ([2, 3, 4].includes(months % 10) && ![12, 13, 14].includes(months % 100)) {
        monthText = 'месяца';
    } else {
        monthText = 'месяцев';
    }
    const years = (months / 12).toFixed(1);
    const formattedYears = years.endsWith('.0') ? years.slice(0, -2) : years;
    return `${months} ${monthText} (~${formattedYears} г.)`;
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        trackEvent('page_view_confirm_portfolio');

        const investmentData = JSON.parse(localStorage.getItem('investmentData'));
        const portfolioData = JSON.parse(localStorage.getItem('calculatedPortfolio'));
        
        if (!portfolioData || !portfolioData.forecast || !Array.isArray(portfolioData.forecast.avg) || !investmentData) {
            document.querySelector('.container').innerHTML = '<h1>Данные о портфеле не найдены.</h1><p>Пожалуйста, вернитесь и соберите портфель заново.</p><a href="index.html" class="btn btn-main">На главную</a>';
            return;
        }

        renderPageContent(investmentData, portfolioData);
        
        const convertBtn = document.getElementById('convert-to-real-btn');
        if (convertBtn) {
            convertBtn.addEventListener('click', () => {
                trackEvent('click_confirm_on_confirm_page');

                // Если мы в Telegram, отправляем уведомление через API
                if (window.Telegram.WebApp.initData) {
                    sendNotification(investmentData, portfolioData);
                }
                
                // В любом случае переходим на финальную страницу
                window.location.href = 'final.html';
            });
        }
    } catch (e) {
        console.error("Критическая ошибка на странице подтверждения:", e);
        document.querySelector('.container').innerHTML = `<h1>Произошла ошибка</h1><p>Не удалось отобразить страницу. Попробуйте начать заново.</p><a href="index.html" class="btn btn-main">На главную</a>`;
    }
});

/**
 * Отправляет данные портфеля на бэкенд для уведомления пользователя.
 */
async function sendNotification(investmentData, portfolioData) {
    try {
        const userId = window.Telegram.WebApp.initDataUnsafe?.user?.id;
        if (!userId) {
            console.warn("Не удалось получить ID пользователя для отправки уведомления.");
            return;
        }

        const leanPortfolioData = {
            ...portfolioData,
            forecast: {
                min: [portfolioData.forecast.min.slice(-1)[0]],
                avg: [portfolioData.forecast.avg.slice(-1)[0]],
                max: [portfolioData.forecast.max.slice(-1)[0]]
            },
            deposit_forecast: null, 
            forecast_without_contribution: null
        };
        if (portfolioData.monthly_income_forecast) {
            leanPortfolioData.monthly_income_forecast = [portfolioData.monthly_income_forecast.slice(-1)[0]];
        }
        
        const payload = {
            userId: userId,
            portfolioSummary: {
                investmentData: investmentData,
                portfolioData: leanPortfolioData
            }
        };

        // Отправляем запрос на наш API сервер, который перенаправит его боту
        await fetch(`${window.location.origin}/api/notify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

    } catch (error) {
        console.error("Ошибка при отправке фонового уведомления:", error);
        // Не блокируем пользователя, даже если уведомление не удалось отправить
    }
}


/**
 * Отображает весь контент страницы в зависимости от цели пользователя.
 */
function renderPageContent(investmentData, portfolioData) {
    const titleEl = document.getElementById('confirm-title');
    const summaryCardEl = document.getElementById('final-summary-card');
    const format = (num) => (num || 0).toLocaleString('ru-RU', { maximumFractionDigits: 0 });

    const termInMonths = portfolioData.term_months || (portfolioData.term * 12);
    const formattedTerm = formatTerm(termInMonths);

    let title = '';
    let summaryHTML = '';

    const totalInvested = portfolioData.initial_amount + ((portfolioData.monthly_contribution || 0) * termInMonths);

    switch (investmentData.goal) {
        case 'dream':
            title = 'Цель: Накопить на мечту';
            const finalAvgCapital = portfolioData.forecast.avg.slice(-1)[0];
            const isGoalReached = finalAvgCapital >= investmentData.dreamAmount;
            const statusClass = isGoalReached ? 'status-success' : 'status-fail';
            const statusText = isGoalReached 
                ? `вы достигнете цели!` 
                : `до цели не хватит ~${format(investmentData.dreamAmount - finalAvgCapital)} ₽`;

            summaryHTML = `
                <p>Ваша цель — накопить <strong>${format(investmentData.dreamAmount)} ₽</strong> за <strong>${formattedTerm}</strong>.</p>
                <p>Начав с <strong>${format(portfolioData.initial_amount)} ₽</strong>, по среднему прогнозу, <span class="${statusClass}">${statusText}</span></p>
            `;
            break;
        
        case 'passive':
            title = 'Цель: Пассивный доход';
            const finalAvgIncome = portfolioData.monthly_income_forecast.slice(-1)[0];
            summaryHTML = `
                <p>Вы хотите получать <strong>${format(investmentData.passiveIncome)} ₽/мес</strong>.</p>
                <p>Через <strong>${formattedTerm}</strong>, начав с <strong>${format(portfolioData.initial_amount)} ₽</strong>, ваш пассивный доход составит <strong>~${format(finalAvgIncome)} ₽/мес</strong>.</p>
            `;
            break;

        default: // 'grow'
            title = 'Цель: Приумножить капитал';
            const avgProfit = portfolioData.forecast.avg.slice(-1)[0] - totalInvested;
            summaryHTML = `
                <p>Вы инвестируете <strong>${format(portfolioData.initial_amount)} ₽</strong> на срок <strong>${formattedTerm}</strong>.</p>
                <p>Средний прогнозируемый доход составит <strong>+${format(avgProfit)} ₽</strong>.</p>
            `;
            break;
    }

    titleEl.textContent = title;
    summaryCardEl.innerHTML = summaryHTML;

    // Расчет и отображение доходности
    const forecast = portfolioData.forecast;
    const maxTotal = forecast.max.slice(-1)[0];
    const avgTotal = forecast.avg.slice(-1)[0];
    const minTotal = forecast.min.slice(-1)[0];

    const formatProfit = (value) => {
        const profit = value - totalInvested;
        const sign = profit > 0 ? '+' : '';
        return `${sign}${format(profit)} ₽`;
    };

    document.getElementById('final-max-profit').textContent = formatProfit(maxTotal);
    document.getElementById('final-avg-profit').textContent = formatProfit(avgTotal);
    document.getElementById('final-min-profit').textContent = formatProfit(minTotal);
}

