import { trackEvent } from './script.js';

let portfolioChartInstance = null;
let popupChartInstance = null;
let fullPortfolioData = null;
let investmentData = null;
let currentChartView = 'capital';

function formatTerm(months) {
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
    initializePage();
});

async function initializePage() {
    showLoader();
    try {
        investmentData = JSON.parse(localStorage.getItem('investmentData'));
        const cachedPortfolio = JSON.parse(localStorage.getItem('calculatedPortfolio'));

        if (!investmentData) {
            throw new Error('Данные о цели не найдены в localStorage.');
        }

        if (cachedPortfolio) {
            console.log("Используются кэшированные данные из localStorage.");
            fullPortfolioData = cachedPortfolio;
        } else {
            console.log("Нет кэша, рассчитывается новый портфель с бэкенда.");
            const API_URL = `${window.location.origin}/api/calculate`;
            const termInMonthsFromStorage = investmentData.term_months || investmentData.term;
            const requestBody = {
                ...investmentData,
                term: null,
                term_months: termInMonthsFromStorage
            };
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`API запрос завершился со статусом ${response.status}`);
            }
            fullPortfolioData = await response.json();
        }

        if (!fullPortfolioData || !fullPortfolioData.composition) {
             throw new Error('Получена неверная структура данных портфеля.');
        }

        renderPage(fullPortfolioData, investmentData);
        trackEvent('page_view_portfolio', { goal: investmentData.goal });

        if (!localStorage.getItem('hasSeenFundsInfoPopup')) {
            const fundsPopup = document.getElementById('funds-info-popup');
            if(fundsPopup) {
                fundsPopup.classList.add('active');
            }
        }

    } catch (error) {
        console.error("Ошибка инициализации страницы портфеля:", error);
        showError('Не удалось загрузить данные портфеля. Пожалуйста, попробуйте собрать его заново.');
    } finally {
        hideLoader();
    }
}

function renderPage(portfolioData, invData) {
    const container = document.querySelector('.container');
    const termInMonths = portfolioData.term_months || (portfolioData.term * 12);
    const formattedTerm = formatTerm(termInMonths);

    const contribution = portfolioData.monthly_contribution || 0;

    let summaryItemsHtml = '';
    const goalNames = {
        grow: 'Приумножить капитал',
        dream: 'Накопить на мечту',
        passive: 'Создать пассивный доход'
    };

    if (invData.goal === 'dream') {
        summaryItemsHtml = `
            <div class="info-item">
                <span class="label">Сумма цели</span>
                <span class="value">${invData.dreamAmount.toLocaleString('ru-RU')} ₽</span>
            </div>
            <div class="info-item">
                <span class="label">Начальный взнос</span>
                <span class="value">${portfolioData.initial_amount.toLocaleString('ru-RU')} ₽</span>
            </div>
        `;
    } else if (invData.goal === 'passive') {
        summaryItemsHtml = `
            <div class="info-item">
                <span class="label">Желаемый доход</span>
                <span class="value">${invData.passiveIncome.toLocaleString('ru-RU')} ₽/мес</span>
            </div>
             <div class="info-item">
                <span class="label">Начальный взнос</span>
                <span class="value">${portfolioData.initial_amount.toLocaleString('ru-RU')} ₽</span>
            </div>
        `;
    } else {
         summaryItemsHtml = `
            <div class="info-item">
                <span class="label">Сумма инвестиций</span>
                <span class="value">${portfolioData.initial_amount.toLocaleString('ru-RU')} ₽</span>
            </div>
        `;
    }

    if (contribution > 0) {
        summaryItemsHtml += `
            <div class="info-item">
                <span class="label">Ежемесячное пополнение</span>
                <span class="value">${contribution.toLocaleString('ru-RU')} ₽</span>
            </div>
        `;
    }
    
    const worstCaseProfit = portfolioData.forecast.min[portfolioData.forecast.min.length - 1] - portfolioData.initial_amount;
    const bestCaseProfit = portfolioData.forecast.max[portfolioData.forecast.max.length - 1] - portfolioData.initial_amount;
    summaryItemsHtml += `
        <div class="info-item">
            <span class="label">Срок</span>
            <span class="value">${formattedTerm}</span>
        </div>
        <div class="info-item">
            <span class="label">Стратегия</span>
            <span class="value">${portfolioData.strategy_name}</span>
        </div>
        <div class="info-item guaranteed-income">
            <span class="label">Доход в лучшем / худшем сценарии: </span><span class="value">${bestCaseProfit > 0 ? '+' : ''}${bestCaseProfit.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽ / ${worstCaseProfit > 0 ? '+' : ''}${worstCaseProfit.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽</span>
        </div>
    `;


    let goalSpecificInfoHtml = '';
    const finalCapitalAvg = portfolioData.forecast.avg[portfolioData.forecast.avg.length - 1];

    if (invData.goal === 'passive') {
        const finalIncome = portfolioData.monthly_income_forecast[portfolioData.monthly_income_forecast.length - 1];
        goalSpecificInfoHtml = `
            <div class="goal-summary-card">
                <p>Прогноз капитала через <strong>${formattedTerm}</strong> по серднему, наиболее вероятному сценарию, составит ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong></p>
                <p>Это позволит получать пассивный доход <strong>~${Math.round(finalIncome).toLocaleString('ru-RU')} ₽</strong> в месяц.</p>
            </div>
        `;
    } else if (invData.goal === 'dream') {
        const dreamAmount = invData.dreamAmount;
        const isGoalReached = finalCapitalAvg >= dreamAmount;
        const statusText = isGoalReached
            ? `Согласно серднему, наиболее вероятному сценарию, прогнозу, вы <strong>достигнете своей цели</strong>. Ваш капитал может составить ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>.`
            : `Согласно серднему, наиболее вероятному сценарию, прогнозу, для достижения цели вам может не хватить ~<strong>${Math.round(dreamAmount - finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>. Попробуйте изменить риск или срок в редакторе.`;

        goalSpecificInfoHtml = `
            <div class="goal-summary-card">
                <p>Ваша цель — накопить <strong>${dreamAmount.toLocaleString('ru-RU')} ₽</strong> за <strong>${formattedTerm}</strong>.</p>
                <p>${statusText}</p>
            </div>
        `;
    } else {
        const profit = finalCapitalAvg - portfolioData.initial_amount;
        goalSpecificInfoHtml = `
            <div class="goal-summary-card">
                 <p>Согласно серднему, наиболее вероятному сценарию, прогнозу, через <strong>${formattedTerm}</strong> ваш капитал может вырасти до ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>.</p>
                 <p>Потенциальный доход может составить <strong>+${Math.round(profit).toLocaleString('ru-RU')} ₽</strong>.</p>
            </div>
        `;
    }
    
    let switcherButtonsHtml = '<button class="switcher-btn active" data-view="capital">График успеха</button>';
    if (invData.goal === 'passive') {
        switcherButtonsHtml += '<button class="switcher-btn" data-view="income">Месячный доход</button>';
    }
    switcherButtonsHtml += '<button class="switcher-btn" data-view="similar">Похожие портфели</button>';

    const chartViewSwitcherHtml = `
        <div class="view-switcher" id="portfolio-view-switcher">
            ${switcherButtonsHtml}
        </div>
    `;

    container.innerHTML = `
        <div class="portfolio-header">
             <h1 class="page-title">
                Ваш портфель
                <button class="help-btn" id="funds-info-help-btn">?</button>
            </h1>
        </div>

        <div class="portfolio-card">
            <details class="portfolio-section-toggle" open>
                <summary class="portfolio-section-header">
                    <h3>${goalNames[invData.goal]}</h3>
                    <span class="toggle-icon">▼</span>
                </summary>
                <div class="portfolio-section-content">
                    ${summaryItemsHtml}
                </div>
            </details>
            <details class="portfolio-section-toggle">
                <summary class="portfolio-section-header">
                    <h3>Активы в портфеле</h3>
                    <span class="toggle-icon">▼</span>
                </summary>
                <div class="portfolio-section-content assets-list">
                    ${portfolioData.composition.map(asset => `
                        <div class="asset-item">
                            <span class="asset-name">${asset.fund_name}</span>
                            <span class="asset-percent">${asset.percentage.toFixed(0)}%</span>
                        </div>
                    `).join('')}
                </div>
            </details>
        </div>
        
        <div class="main-actions">
            <button class="btn btn-secondary" id="edit-portfolio-btn">Редактировать</button>
            <button class="btn btn-main" id="confirm-portfolio-btn">Подтвердить портфель</button>
        </div>
        
        ${goalSpecificInfoHtml}
        ${chartViewSwitcherHtml}

        <div class="spacer"></div>

        <div class="content-views">
            <div id="chart-view" class="view active">
                <div class="chart-container">
                    <div class="chart-wrapper">
                        <canvas id="performance-chart"></canvas>
                    </div>
                    <div id="chart-legend" class="chart-legend"></div>
                </div>
            </div>

            <div id="similar-view" class="view">
                <div class="similar-container">
                    <h3>Примеры похожих портфелей</h3>
                    <p class="similar-subtitle">Это анонимные примеры портфелей других пользователей с похожими целями и риск-профилем.</p>
                    <div class="slider-container" id="similar-slider">
                    </div>
                </div>
            </div>
        </div>

        <div class="restart-section">
            <button class="btn btn-secondary" id="restart-btn">Начать сначала</button>
        </div>

        <div id="funds-info-popup" class="popup-overlay">
            <div class="popup-content">
                <button class="popup-close" id="close-funds-popup-btn">&times;</button>
                <h3>Ваши деньги работают на экономику</h3>
                <img src="img/factory.jpg" alt="Промышленный пейзаж" class="popup-image">
                <p>Мы не покупаем акции отдельных компаний. Вместо этого мы вложили ваши деньги в фонды, которые включают в себя сотни крупнейших российских предприятий. Это значит, что ваши активы подкреплены всей экономикой страны, что делает вложения более надежными.</p>
                <button class="btn btn-main" id="confirm-funds-popup-btn">Всё понятно!</button>
            </div>
        </div>

        <div id="change-goal-popup" class="popup-overlay">
            <div class="popup-content">
                <button class="popup-close" id="cancel-change-goal-btn">&times;</button>
                <h3>Смена цели</h3>
                <p>Чтобы изменить тип цели, необходимо начать подбор заново. Это нужно, чтобы мы могли предложить вам наиболее подходящую стратегию.</p>
                <div class="button-group popup-buttons">
                    <button class="btn btn-main" id="restart-from-popup-btn">Начать заново</button>
                    <button class="btn btn-secondary" id="cancel-change-goal-btn-2">Отмена</button>
                </div>
            </div>
        </div>
    `;

    // ИСПРАВЛЕНИЕ: Вызываем setupEventListeners здесь, после отрисовки
    setupEventListeners();
    initializeChart(portfolioData, invData);
    initializeSimilarPortfoliosSlider();
}

function setupEventListeners() {
    document.getElementById('edit-portfolio-btn').addEventListener('click', () => {
        trackEvent('click_edit_portfolio');
        localStorage.setItem('calculatedPortfolio', JSON.stringify(fullPortfolioData));
        window.location.href = 'edit-portfolio.html';
    });
    
    document.getElementById('funds-info-help-btn').addEventListener('click', () => {
        document.getElementById('funds-info-popup').classList.add('active');
    });

    document.getElementById('restart-btn').addEventListener('click', () => {
        trackEvent('click_restart_portfolio');
        localStorage.clear();
        window.location.href = 'index.html';
    });

    document.getElementById('confirm-portfolio-btn').addEventListener('click', () => {
        trackEvent('click_confirm_portfolio');
        localStorage.setItem('calculatedPortfolio', JSON.stringify(fullPortfolioData));
        window.location.href = 'confirm-portfolio.html';
    });
    
    const sectionToggles = document.querySelectorAll('.portfolio-section-toggle');
    sectionToggles.forEach(toggle => {
        toggle.addEventListener('toggle', (event) => {
            const headerText = toggle.querySelector('h3').textContent.toLowerCase();
            let sectionName = 'unknown';
            if (headerText.includes('капитал') || headerText.includes('мечту') || headerText.includes('доход')) {
                sectionName = 'summary';
            } else if (headerText.includes('активы')) {
                sectionName = 'assets';
            }
            
            trackEvent('toggle_portfolio_section', { 
                section: sectionName,
                state: event.target.open ? 'opened' : 'closed' 
            });
        });
    });

    
    const changeGoalTrigger = document.querySelector('.portfolio-section-header');
    if (changeGoalTrigger) {
        changeGoalTrigger.style.cursor = 'pointer';
        changeGoalTrigger.addEventListener('click', (e) => {
             if (e.target.classList.contains('toggle-icon')) {
                return;
             }
             if (localStorage.getItem('goalChangePopupShown') !== 'true') {
                document.getElementById('change-goal-popup').classList.add('active');
                localStorage.setItem('goalChangePopupShown', 'true');
             }
        });
    }

    document.getElementById('restart-from-popup-btn').addEventListener('click', () => {
        trackEvent('confirm_restart_from_popup');
        localStorage.clear();
        window.location.href = 'index.html';
    });

    const closePopup = () => document.getElementById('change-goal-popup').classList.remove('active');
    document.getElementById('cancel-change-goal-btn').addEventListener('click', closePopup);
    document.getElementById('cancel-change-goal-btn-2').addEventListener('click', closePopup);

    const fundsPopup = document.getElementById('funds-info-popup');
    if (fundsPopup) {
        const closeButtons = fundsPopup.querySelectorAll('#close-funds-popup-btn, #confirm-funds-popup-btn');
        const closeFundsPopup = () => {
            fundsPopup.classList.remove('active');
            localStorage.setItem('hasSeenFundsInfoPopup', 'true');
            trackEvent('close_funds_info_popup');
        };
        closeButtons.forEach(btn => btn.addEventListener('click', closeFundsPopup));
        fundsPopup.addEventListener('click', (e) => {
            if (e.target === fundsPopup) {
                closeFundsPopup();
            }
        });
    }

    const viewSwitcher = document.getElementById('portfolio-view-switcher');
    if (viewSwitcher) {
        viewSwitcher.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') return;

            const selectedView = e.target.dataset.view;
            if (selectedView === currentChartView) return;

            viewSwitcher.querySelector('.active').classList.remove('active');
            e.target.classList.add('active');
            
            currentChartView = selectedView;
            trackEvent('switch_portfolio_view', { view: currentChartView });

            const chartView = document.getElementById('chart-view');
            const similarView = document.getElementById('similar-view');

            if (selectedView === 'similar') {
                chartView.classList.remove('active');
                similarView.classList.add('active');
            } else {
                similarView.classList.remove('active');
                chartView.classList.add('active');
                updateChart(fullPortfolioData, investmentData);
            }
        });
    }
}

function initializeSimilarPortfoliosSlider() {
    const sliderContainer = document.getElementById('similar-slider');
    if (!sliderContainer) return;

    const similarPortfolios = [
        { title: "Накопления на отпуск", desc: "Пользователь копит 300 000 ₽ за 2 года.", term: 2, risk: "Умеренный", profit: 45000 },
        { title: "Первый взнос на ипотеку", desc: "Цель — 1 500 000 ₽ за 5 лет.", term: 5, risk: "Агрессивный", profit: 850000 },
        { title: "Финансовая подушка", desc: "Создание резерва в 500 000 ₽ без спешки.", term: 3, risk: "Консервативный", profit: 60000 }
    ];

    let slidesHtml = '';
    similarPortfolios.forEach(p => {
        slidesHtml += `
            <div class="slide">
                <h4>${p.title}</h4>
                <p class="slide-desc">${p.desc}</p>
                <div class="slide-details">
                    <span>Срок: <strong>${p.term} г.</strong></span>
                    <span>Риск: <strong>${p.risk}</strong></span>
                    <span>Доход: <strong>~${p.profit.toLocaleString('ru-RU')} ₽</strong></span>
                </div>
            </div>`;
    });
    
    sliderContainer.innerHTML = `
        <button class="slider-arrow prev">‹</button>
        <div class="slider-wrapper">
            <div class="slider-track">${slidesHtml}</div>
        </div>
        <button class="slider-arrow next">›</button>
    `;

    const track = sliderContainer.querySelector('.slider-track');
    const slides = Array.from(track.children);
    const nextButton = sliderContainer.querySelector('.slider-arrow.next');
    const prevButton = sliderContainer.querySelector('.slider-arrow.prev');
    let currentIndex = 0;

    const updateSlider = () => {
        track.style.transform = `translateX(-${currentIndex * 100}%)`;
        prevButton.disabled = currentIndex === 0;
        nextButton.disabled = currentIndex === slides.length - 1;
    };

    nextButton.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
            updateSlider();
        }
    });

    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateSlider();
        }
    });
    
    updateSlider();
}


function initializeChart(portfolioData, invData) {
    const canvas = document.getElementById('performance-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (portfolioChartInstance) portfolioChartInstance.destroy();

    portfolioChartInstance = new Chart(ctx, {
        type: 'line', data: {},
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { 
                y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k ₽' } }, 
                x: { title: { display: true, text: 'Месяцы' } } 
            },
            plugins: { legend: { display: false }, tooltip: { enabled: true } }
        }
    });

    updateChart(portfolioData, invData);
}

function updateChart(portfolioData, invData) {
    if (!portfolioChartInstance) return;
    const chartData = generateChartData(portfolioData, invData);
    portfolioChartInstance.data = chartData.data;
    portfolioChartInstance.options.scales.y.ticks.callback = value => (value / 1000) + 'k ₽';
    portfolioChartInstance.options.scales.y.title.text = chartData.yTitle;
    portfolioChartInstance.update();
    updateChartLegend(portfolioChartInstance, invData, currentChartView);
}

function updateChartLegend(chart, investmentData, currentChartView) {
    const legendContainer = document.getElementById('chart-legend');
    if (!legendContainer) return;

    const { datasets } = chart.data;
    let legendHTML = '';

    datasets.forEach(dataset => {
        const meta = chart.getDatasetMeta(chart.data.datasets.indexOf(dataset));
        if (meta.hidden || !dataset.data || dataset.data.length === 0) {
            return;
        }

        const lastValue = dataset.data[dataset.data.length - 1];
        const color = dataset.borderColor;
        let labelText = '';
        let valueText = Math.round(lastValue).toLocaleString('ru-RU') + ' ₽';
        let profitText = '';
        let isGoalLine = false;

        switch(dataset.label) {
            case 'Макс. доход': labelText = 'Макс. доход'; break;
            case 'Сред. доход': labelText = 'Сред. доход'; break;
            case 'Мин. доход': labelText = 'Мин. доход'; break;
            case 'Прогноз дохода': labelText = 'Прогноз дохода'; break;
            case 'Цель':
                isGoalLine = true;
                if (investmentData.goal === 'dream') {
                    labelText = 'Целевая сумма';
                } else if (investmentData.goal === 'passive') {
                    labelText = (currentChartView === 'income') ? 'Целевой доход' : 'Необходимая сумма';
                }
                break;
            default: return;
        }
        
         if (!isGoalLine && dataset.label !== 'Прогноз дохода' && investmentData.amount) {
            const totalInvested = investmentData.amount + ( (investmentData.monthlyContribution || 0) * (investmentData.term_months || 0) );
            const profit = lastValue - totalInvested;
            const sign = profit >= 0 ? '+' : '';
            const profitClass = profit < 0 ? 'loss' : 'gain';
            profitText = `<span class="${profitClass}">${sign}${Math.round(profit).toLocaleString('ru-RU')} ₽</span>`;
        }

        const lineStyle = isGoalLine ? `border-bottom: 2px dashed ${color};` : `background-color: ${color};`;

        legendHTML += `
            <div class="legend-item">
                <span class="legend-color" style="${lineStyle}"></span>
                <span class="legend-label">${labelText}</span>
                <span class="legend-value">${valueText}</span>
                <span class="legend-profit">${profitText}</span>
            </div>
        `;
    });

    legendContainer.innerHTML = legendHTML;
}

function generateChartData(portfolioData, invData) {
    const { forecast, goal_target_capital, monthly_income_forecast } = portfolioData;
    const isPassiveGoal = invData.goal === 'passive';
    const isIncomeView = isPassiveGoal && currentChartView === 'income';

    const datasets = [];
    let targetLineValue = null;
    let yTitle = 'Сумма капитала, ₽';

    if (isIncomeView) {
        yTitle = 'Месячный доход, ₽';
        datasets.push({ label: 'Прогноз дохода', data: monthly_income_forecast, borderColor: '#f8f9fa', tension: 0.1 });
        targetLineValue = invData.passiveIncome;
    } else {
        datasets.push({ label: 'Макс. доход', data: forecast.max, borderColor: '#28a745', tension: 0.1 });
        datasets.push({ label: 'Сред. доход', data: forecast.avg, borderColor: '#f8f9fa', tension: 0.1 });
        datasets.push({ label: 'Мин. доход', data: forecast.min, borderColor: '#dc3545', tension: 0.1 });

        if (invData.goal === 'dream') {
            targetLineValue = invData.dreamAmount;
        } else if (isPassiveGoal) {
            targetLineValue = goal_target_capital;
        }
    }

    if (targetLineValue) {
         datasets.push({
            label: 'Цель',
            data: Array.from({ length: forecast.labels.length }).fill(targetLineValue),
            borderColor: '#dc2626',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0
        });
    }
    
    return {
        data: { labels: forecast.labels, datasets },
        yTitle: yTitle
    };
}


function showLoader() {
    if (document.getElementById('page-loader')) return;
    const loaderOverlay = document.createElement('div');
    loaderOverlay.id = 'page-loader';
    loaderOverlay.innerHTML = `<div class="spinner"></div>`;
    loaderOverlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center; z-index: 10000;';
    
    const spinnerStyle = document.createElement('style');
    spinnerStyle.innerHTML = `
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #333;
            border-top-color: #dc2626;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(spinnerStyle);
    document.body.appendChild(loaderOverlay);
}

function hideLoader() {
    const loaderOverlay = document.getElementById('page-loader');
    if (loaderOverlay) {
        loaderOverlay.remove();
    }
}

function showError(message) {
    const container = document.querySelector('.container');
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh;">
                <h1 style="color: #dc2626; margin-bottom: 1rem;">Произошла ошибка</h1>
                <p style="color: #aaaaaa; margin-bottom: 2rem;">${message}</p>
                <a href="index.html" class="btn btn-main" style="text-decoration: none;">Начать сначала</a>
            </div>
        `;
    }
}

