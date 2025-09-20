import { trackEvent } from './script.js';

// --- Глобальное состояние и константы ---
let currentPortfolio = null;
let investmentData = null; 
let allFundsCache = null;
let isRecalculating = false;
let portfolioChartInstance = null;
let currentChartView = 'capital'; 
const tg = window.Telegram.WebApp;
const API_URL_CALCULATE = `${window.location.origin}/api/calculate`;
const API_URL_FUNDS = `${window.location.origin}/api/funds`;

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


// --- Инициализация ---
document.addEventListener('DOMContentLoaded', async () => {
    trackEvent('page_view_edit_portfolio');
    tg.MainButton.hide();
    document.body.innerHTML = '<div class="loading-indicator">Загружаем редактор...</div>';

    try {
        investmentData = JSON.parse(localStorage.getItem('investmentData'));
        const storedPortfolio = JSON.parse(localStorage.getItem('calculatedPortfolio'));
        
        if (!investmentData) throw new Error("Данные о цели не найдены в localStorage.");
        if (!storedPortfolio) throw new Error("Рассчитанный портфель не найден в localStorage.");

        currentPortfolio = storedPortfolio;
        currentPortfolio.term_months = currentPortfolio.term_months || currentPortfolio.term * 12;

        await fetchAllFunds();

        renderPage(); 
        initializePageLogic();

        if (!localStorage.getItem('hasSeenEditTutorial')) {
            showTutorial();
        }

    } catch (error) {
        console.error("❌ Ошибка инициализации редактора:", error);
        document.body.innerHTML = `<div class="error-message">${error.message}<br><a href="auto-selection.html">Начать заново</a></div>`;
    }
});


function renderPage() {
    document.body.innerHTML = `
    <div class="container">
        <div class="edit-header">
            <h1 class="page-title">Настройка портфеля</h1>
            <p class="page-subtitle">Отрегулируйте риск и срок, чтобы достичь своей цели.</p>
        </div>
        <details class="portfolio-card-toggle" id="portfolio-details" open>
            <summary class="portfolio-card-header">
                <div class="summary-main">
                    <h3 id="portfolio-strategy-title"></h3>
                    <div class="summary-details" id="summary-details"></div>
                </div>
                <span class="toggle-icon">▼</span>
            </summary>
            <div class="portfolio-card-content">
                <h4>Активы в портфеле</h4>
                <div class="assets-list" id="assets-list"></div>
            </div>
        </details>
        <div id="goal-summary-card-container"></div>
        <div id="chart-view-switcher-container"></div>
        <div class="risk-slider-container">
            <div class="slider-header">
                <label for="risk-slider">Уровень риска</label>
                <span id="risk-level-label"></span>
            </div>
            <input type="range" id="risk-slider" min="0" max="100" value="50">
            <div class="slider-labels"><span>Мин. риск</span><span>Выс. риск</span></div>
        </div>
        <div class="risk-slider-container">
            <div class="slider-header">
                <label for="term-slider">Срок инвестирования</label>
                <span id="term-level-label"></span>
            </div>
            <input type="range" id="term-slider" min="12" max="60" value="36">
            <div class="slider-labels"><span>1 год</span><span>5 лет</span></div>
        </div>
        <div class="chart-container">
            <div class="chart-wrapper"><canvas id="performance-chart"></canvas></div>
        </div>
        <div class="action-buttons">
            <button class="btn btn-secondary" id="reset-btn">Сбросить</button>
            <button class="btn btn-main" id="save-btn">Сохранить</button>
        </div>
    </div>
    <!-- Pop-up'ы -->
    <div id="tutorial-popup" class="popup-overlay">
        <div class="popup-content">
            <button class="popup-close" id="popup-close-tutorial">&times;</button>
            <h3>Добро пожаловать в редактор!</h3>
            <p>Здесь вы можете тонко настроить ваш портфель.</p>
            <ul class="tutorial-list">
                <li>Используйте <strong>слайдеры риска и срока</strong>, чтобы видеть, как меняется прогноз.</li>
                <li>Внутри карточки портфеля вы можете <strong>заменить один актив на другой</strong> из той же категории.</li>
            </ul>
            <button class="btn btn-main" id="start-tutorial-btn">Понятно</button>
        </div>
    </div>
    <div id="replace-asset-popup" class="popup-overlay">
        <div class="popup-content">
            <button class="popup-close" id="close-replace-popup">&times;</button>
            <h3 id="replace-popup-title">Заменить актив</h3>
            <div id="replacement-options" class="replacement-options-list"></div>
        </div>
    </div>`;
}

function initializePageLogic() {
    initializeChart();
    setupEventListeners();
    updateUIFromPortfolio(); 
}

function updateUIFromPortfolio() {
    updateCardDetails();
    updateGoalSummaryCard();
    updateChartViewSwitcher();
    updateRiskSlider();
    updateTermSlider();
    renderAssets();
    updateChart();
}

function updateCardDetails() {
    const termInMonths = currentPortfolio.term_months;
    document.getElementById('portfolio-strategy-title').textContent = `${sliderValueToRiskProfile(document.getElementById('risk-slider').value).label} портфель`;
    document.getElementById('summary-details').innerHTML = `
        <span>${currentPortfolio.initial_amount.toLocaleString('ru-RU')} ₽ • ${formatTerm(termInMonths)}</span>`;
}


function updateGoalSummaryCard() {
    const container = document.getElementById('goal-summary-card-container');
    const finalCapitalAvg = currentPortfolio.forecast.avg[currentPortfolio.forecast.avg.length - 1];
    const termText = formatTerm(currentPortfolio.term_months);
    let goalSpecificInfoHtml = '';

    if (investmentData.goal === 'passive') {
        const finalIncome = currentPortfolio.monthly_income_forecast[currentPortfolio.monthly_income_forecast.length - 1];
        goalSpecificInfoHtml = `<div class="goal-summary-card"><p>Прогноз капитала через <strong>${termText}</strong> составит ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong></p><p>Это позволит получать пассивный доход <strong>~${Math.round(finalIncome).toLocaleString('ru-RU')} ₽</strong> в месяц.</p></div>`;
    } else if (investmentData.goal === 'dream') {
        const dreamAmount = investmentData.dreamAmount;
        const isGoalReached = finalCapitalAvg >= dreamAmount;
        const statusText = isGoalReached ? `Согласно базовому прогнозу, вы <strong>достигнете своей цели</strong>. Ваш капитал может составить ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>.` : `Согласно базовому прогнозу, для достижения цели вам может не хватить ~<strong>${Math.round(dreamAmount - finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>.`;
        goalSpecificInfoHtml = `<div class="goal-summary-card"><p>Ваша цель — накопить <strong>${dreamAmount.toLocaleString('ru-RU')} ₽</strong> за <strong>${termText}</strong>. ${statusText}</p></div>`;
    } else if (investmentData.goal === 'grow') {
        const profit = finalCapitalAvg - currentPortfolio.initial_amount;
        goalSpecificInfoHtml = `<div class="goal-summary-card"><p>Согласно базовому прогнозу, через <strong>${termText}</strong> ваш капитал может вырасти до ~<strong>${Math.round(finalCapitalAvg).toLocaleString('ru-RU')} ₽</strong>.</p><p>Потенциальный доход может составить <strong>+${Math.round(profit).toLocaleString('ru-RU')} ₽</strong>.</p></div>`;
    }
    container.innerHTML = goalSpecificInfoHtml;
}

function updateChartViewSwitcher() {
    const container = document.getElementById('chart-view-switcher-container');
    if (investmentData.goal === 'passive') {
        container.innerHTML = `
            <div class="view-switcher" id="edit-chart-switcher">
                <button class="switcher-btn ${currentChartView === 'capital' ? 'active' : ''}" data-view="capital">Рост капитала</button>
                <button class="switcher-btn ${currentChartView === 'income' ? 'active' : ''}" data-view="income">Месячный доход</button>
            </div>`;
        
        const chartSwitcher = document.getElementById('edit-chart-switcher');
        chartSwitcher.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                currentChartView = e.target.dataset.view;
                trackEvent('switch_chart_view_edit', { view: currentChartView });
                updateUIFromPortfolio();
            }
        });
    } else {
        container.innerHTML = '';
    }
}

function updateRiskSlider() {
    const slider = document.getElementById('risk-slider');
    slider.value = riskProfileToSliderValue(currentPortfolio.riskProfile);
    document.getElementById('risk-level-label').textContent = sliderValueToRiskProfile(slider.value).label;
}

function updateTermSlider() {
    const slider = document.getElementById('term-slider');
    slider.value = currentPortfolio.term_months; 
    document.getElementById('term-level-label').textContent = formatTerm(currentPortfolio.term_months);
}

function renderAssets() {
    const assetsListContainer = document.getElementById('assets-list');
    assetsListContainer.innerHTML = '';
    currentPortfolio.composition.forEach(asset => {
        const assetDiv = document.createElement('div');
        assetDiv.className = 'asset-item';
        assetDiv.innerHTML = `
            <div class="asset-info">
                <span class="asset-name">${asset.fund_name}</span>
                <span class="asset-percent">${asset.percentage.toFixed(0)}%</span>
            </div>
            <button class="replace-btn">Заменить</button>
        `;
        assetDiv.querySelector('.replace-btn').addEventListener('click', () => openReplacePopup(asset.fund_name));
        assetsListContainer.appendChild(assetDiv);
    });
}

function setupEventListeners() {
    document.getElementById('risk-slider').addEventListener('change', handleRiskSliderChange);
    document.getElementById('risk-slider').addEventListener('input', () => {
         document.getElementById('risk-level-label').textContent = sliderValueToRiskProfile(document.getElementById('risk-slider').value).label;
    });
    
    document.getElementById('reset-btn').addEventListener('click', handleReset);
    document.getElementById('save-btn').addEventListener('click', handleSave);

    const tutorialPopup = document.getElementById('tutorial-popup');
    tutorialPopup.addEventListener('click', e => {
        if (e.target === tutorialPopup || e.target.id === 'popup-close-tutorial' || e.target.id === 'start-tutorial-btn') {
            hideTutorial();
        }
    });

    const replacePopup = document.getElementById('replace-asset-popup');
    replacePopup.addEventListener('click', e => {
        if (e.target === replacePopup || e.target.id === 'close-replace-popup') {
            replacePopup.classList.remove('active');
        }
    });

    const termSlider = document.getElementById('term-slider');
    termSlider.addEventListener('change', handleTermSliderChange);
    termSlider.addEventListener('input', () => {
        document.getElementById('term-level-label').textContent = formatTerm(termSlider.value);
    });
}

async function handleRiskSliderChange() {
    const riskProfile = sliderValueToRiskProfile(document.getElementById('risk-slider').value).riskProfile;
    if (riskProfile !== currentPortfolio.riskProfile) {
        trackEvent('risk_slider_used', { newRisk: riskProfile });
        await recalculatePortfolio();
    }
}

async function handleTermSliderChange() {
    const termInMonths = document.getElementById('term-slider').value;
    if (termInMonths != currentPortfolio.term_months) {
        trackEvent('term_slider_used', { newTermMonths: termInMonths });
        await recalculatePortfolio();
    }
}

async function handleReplaceAsset(newFundName, oldFundName) {
    trackEvent('asset_replaced', { from: oldFundName, to: newFundName });
    const newFundNames = currentPortfolio.composition.map(asset => 
        asset.fund_name === oldFundName ? newFundName : asset.fund_name
    );
    await recalculatePortfolio({ selected_funds: newFundNames });
    document.getElementById('replace-asset-popup').classList.remove('active');
}

function handleReset() {
    trackEvent('click_reset_portfolio_edit');
    const originalPortfolio = JSON.parse(localStorage.getItem('calculatedPortfolio'));
    currentPortfolio = originalPortfolio;
    currentPortfolio.term_months = originalPortfolio.term_months || originalPortfolio.term * 12;
    updateUIFromPortfolio();
    tg.HapticFeedback.impactOccurred('light');
}

function handleSave() {
    trackEvent('click_save_portfolio_edit');
    currentPortfolio.term = Math.ceil(currentPortfolio.term_months / 12);
    investmentData.term = currentPortfolio.term;
    investmentData.term_months = currentPortfolio.term_months;

    localStorage.setItem('investmentData', JSON.stringify(investmentData));
    localStorage.setItem('calculatedPortfolio', JSON.stringify(currentPortfolio));
    tg.HapticFeedback.notificationOccurred('success');
    window.location.href = 'portfolio.html';
}

async function fetchAllFunds() {
    if (!allFundsCache) {
        const response = await fetch(API_URL_FUNDS);
        if (!response.ok) throw new Error("Не удалось загрузить список фондов.");
        allFundsCache = await response.json();
    }
}

async function recalculatePortfolio({ selected_funds = null } = {}) {
    if (isRecalculating) return;
    isRecalculating = true;
    document.querySelector('.container').style.opacity = '0.5';

    try {
        const riskProfile = sliderValueToRiskProfile(document.getElementById('risk-slider').value).riskProfile;
        const termInMonths = parseInt(document.getElementById('term-slider').value, 10);
        
        const response = await fetch(API_URL_CALCULATE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                riskProfile,
                term_months: termInMonths, 
                amount: investmentData.amount,
                dreamAmount: investmentData.dreamAmount,
                passiveIncome: investmentData.passiveIncome,
                selected_funds: selected_funds || currentPortfolio.composition.map(f => f.fund_name)
            })
        });
        if (!response.ok) throw new Error("Ошибка при перерасчете портфеля.");
        
        const newPortfolioData = await response.json();
        
        currentPortfolio = { ...currentPortfolio, ...newPortfolioData };
        currentPortfolio.riskProfile = riskProfile;
        currentPortfolio.term = newPortfolioData.term; 
        currentPortfolio.term_months = newPortfolioData.term_months; 

        updateUIFromPortfolio();

    } catch (error) {
        console.error("❌ Ошибка перерасчета:", error);
        tg.showAlert(error.message || "Не удалось выполнить перерасчет.");
    } finally {
        isRecalculating = false;
        document.querySelector('.container').style.opacity = '1';
    }
}

function openReplacePopup(fundNameToReplace) {
    const popup = document.getElementById('replace-asset-popup');
    const optionsContainer = document.getElementById('replacement-options');
    const currentFund = allFundsCache.find(f => f.name === fundNameToReplace);
    if (!currentFund) return;

    const replacementOptions = allFundsCache.filter(f => f.risk_level === currentFund.risk_level);
    
    document.getElementById('replace-popup-title').textContent = `Заменить "${fundNameToReplace}"`;
    optionsContainer.innerHTML = '';
    replacementOptions.forEach(fund => {
        const button = document.createElement('button');
        button.textContent = fund.name;
        button.className = 'replacement-option-btn';
        if (fund.name === fundNameToReplace) {
            button.classList.add('current');
            button.disabled = true;
        } else {
            button.onclick = () => handleReplaceAsset(fund.name, fundNameToReplace);
        }
        optionsContainer.appendChild(button);
    });
    popup.classList.add('active');
}

function showTutorial() {
    document.getElementById('tutorial-popup').classList.add('active');
}

function hideTutorial() {
    document.getElementById('tutorial-popup').classList.remove('active');
    localStorage.setItem('hasSeenEditTutorial', 'true');
}

function initializeChart() {
    const ctx = document.getElementById('performance-chart')?.getContext('2d');
    if (!ctx) return;
    portfolioChartInstance = new Chart(ctx, {
        type: 'line',
        data: {},
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k ₽' } },
                // --- ИЗМЕНЕНИЕ: Ось X теперь всегда "Месяцы" ---
                x: { title: { display: true, text: 'Месяцы' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function updateChart() {
    if (!portfolioChartInstance) return;
    const chartData = generateChartData(currentPortfolio, investmentData);
    portfolioChartInstance.data = chartData.data;
    portfolioChartInstance.options.scales.y.title.text = chartData.yTitle;
    portfolioChartInstance.update();
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
        } else if (isPassiveGoal && goal_target_capital) {
            targetLineValue = goal_target_capital;
        }
    }

    if (targetLineValue) {
         datasets.push({
            label: 'Цель',
            data: Array(forecast.labels.length).fill(targetLineValue),
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

function riskProfileToSliderValue(profile) {
    switch (profile) {
        case 'conservative': return 10;
        case 'moderate-conservative': return 30;
        case 'moderate': return 50;
        case 'moderate-aggressive': return 70;
        case 'aggressive': return 90;
        default: return 50;
    }
}

function sliderValueToRiskProfile(value) {
    if (value <= 20) return { riskProfile: 'conservative', label: 'Консервативный' };
    if (value <= 40) return { riskProfile: 'moderate-conservative', label: 'Умеренно-консервативный' };
    if (value <= 60) return { riskProfile: 'moderate', label: 'Умеренный' };
    if (value <= 80) return { riskProfile: 'moderate-aggressive', label: 'Умеренно-агрессивный' };
    return { riskProfile: 'aggressive', label: 'Агрессивный' };
}

