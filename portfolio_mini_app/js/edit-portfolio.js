import { trackEvent } from './script.js';

// --- Глобальное состояние и константы ---
let currentPortfolio = null;
let allFundsCache = null; 
let isRecalculating = false;
let portfolioChartInstance = null;
const tg = window.Telegram.WebApp;
const API_URL_CALCULATE = `${window.location.origin}/api/calculate`;
const API_URL_FUNDS = `${window.location.origin}/api/funds`;

// --- Инициализация ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("▶️ DOMContentLoaded: Редактор портфеля начинает инициализацию.");
    trackEvent('page_view_edit_portfolio');
    tg.MainButton.hide();
    document.body.innerHTML = '<div class="loading-indicator">Загружаем редактор...</div>';

    try {
        const storedPortfolio = JSON.parse(localStorage.getItem('calculatedPortfolio'));
        if (!storedPortfolio) throw new Error("Рассчитанный портфель не найден в localStorage.");
        console.log("✅ Портфель загружен из localStorage:", storedPortfolio);
        
        currentPortfolio = storedPortfolio;
        await fetchAllFunds(); // Загружаем и кэшируем все доступные фонды

        renderPage(); // Отрисовываем HTML
        initializePageLogic(); // Настраиваем всю логику

        // Показываем обучалку при первом заходе
        if (!localStorage.getItem('hasSeenEditTutorial')) {
            console.log("ℹ️ Первый визит, показываем обучение.");
            showTutorial();
        }

    } catch (error) {
        console.error("❌ Ошибка инициализации редактора:", error);
        document.body.innerHTML = `<div class="error-message">${error.message}<br><a href="auto-selection.html">Начать заново</a></div>`;
    }
});


// --- Функции отрисовки и UI ---

function renderPage() {
    console.log("🎨 Начинаем отрисовку страницы (renderPage).");
    document.body.innerHTML = `
    <div class="container">
        <div class="edit-header">
            <h1 class="page-title">Настройка портфеля</h1>
            <p class="page-subtitle">Отрегулируйте риск и замените активы, чтобы создать идеальный портфель для себя.</p>
        </div>
        <details class="portfolio-card-toggle" id="portfolio-details" open>
            <summary class="portfolio-card-header">
                <div class="summary-main">
                    <h3 id="portfolio-strategy-title"></h3>
                    <div class="summary-details">
                        <span><span id="portfolio-amount"></span> ₽ • <span id="portfolio-term"></span> лет</span>
                        <div class="guaranteed-return-summary">
                            Гарант. доход: (нижняя планка)<strong id="edit-guaranteed-return"></strong>
                        </div>
                    </div>
                </div>
                <span class="toggle-icon">▼</span>
            </summary>
            <div class="portfolio-card-content">
                <h4>Активы в портфеле</h4>
                <div class="assets-list" id="assets-list"></div>
            </div>
        </details>
        <div class="risk-slider-container" id="risk-slider-section">
            <div class="slider-header">
                <label for="risk-slider">Уровень риска</label>
                <span id="risk-level-label"></span>
            </div>
            <input type="range" id="risk-slider" min="0" max="100" value="50">
            <div class="slider-labels"><span>Мин. риск</span><span>Выс. риск</span></div>
        </div>
        <div class="chart-container">
            <div class="chart-wrapper"><canvas id="performance-chart"></canvas></div>
        </div>
        <div class="action-buttons">
            <button class="btn btn-secondary" id="reset-btn">Сбросить</button>
            <button class="btn btn-main" id="save-btn">Сохранить</button>
        </div>
    </div>
    <!-- Обучающий Pop-up -->
    <div id="tutorial-popup" class="popup-overlay">
        <div class="popup-content">
            <button class="popup-close" id="popup-close-tutorial">&times;</button>
            <h3>Добро пожаловать в редактор!</h3>
            <p>Здесь вы можете тонко настроить ваш портфель.</p>
            <ul class="tutorial-list">
                <li>Используйте <strong>слайдер риска</strong>, чтобы изменить потенциальную доходность и риск портфеля.</li>
                <li>Внутри карточки портфеля вы можете <strong>заменить один актив на другой</strong> из той же категории.</li>
            </ul>
            <button class="btn btn-main" id="start-tutorial-btn">Понятно</button>
        </div>
    </div>
    <!-- Модальное окно для замены активов -->
    <div id="replace-asset-popup" class="popup-overlay">
        <div class="popup-content">
            <button class="popup-close" id="close-replace-popup">&times;</button>
            <h3 id="replace-popup-title">Заменить актив</h3>
            <div id="replacement-options" class="replacement-options-list"></div>
        </div>
    </div>`;
    console.log("✅ Страница отрисована.");
}

function initializePageLogic() {
    console.log("⚙️ Инициализация логики страницы (initializePageLogic).");
    displayPortfolioInfo();
    initializeChart();
    setupEventListeners();
}

function displayPortfolioInfo() {
    console.log("ℹ️ Отображаем информацию о портфеле (displayPortfolioInfo).");
    document.getElementById('portfolio-amount').textContent = currentPortfolio.initial_amount.toLocaleString('ru-RU');
    document.getElementById('portfolio-term').textContent = currentPortfolio.term;
    
    // --- НОВЫЙ КОД ---
    const forecast = currentPortfolio.forecast;
    const guaranteedReturn = forecast.min[forecast.min.length - 1] - currentPortfolio.initial_amount;
    document.getElementById('edit-guaranteed-return').textContent = `+${guaranteedReturn.toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ₽`;
    // --- КОНЕЦ НОВОГО КОДА ---

    document.getElementById('risk-slider').value = riskProfileToSliderValue(currentPortfolio.riskProfile);
    updateRiskUI();
    renderAssets();
}

function renderAssets() {
    console.log("📝 Отрисовка списка активов (renderAssets).");
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
    console.log("🔗 Назначаем обработчики событий (setupEventListeners).");
    document.getElementById('risk-slider').addEventListener('input', handleRiskSliderChange);
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
}

// --- Обработчики событий ---

async function handleRiskSliderChange() {
    if (isRecalculating) return;
    updateRiskUI();
    const { riskProfile } = sliderValueToRiskProfile(document.getElementById('risk-slider').value);
    if (riskProfile !== currentPortfolio.riskProfile) {
        console.log(`🎚️ Слайдер риска изменен. Новый профиль: ${riskProfile}`);
        trackEvent('risk_slider_used', { newRisk: riskProfile });
        await recalculatePortfolio({ riskProfile });
    }
}

async function handleReplaceAsset(newFundName, oldFundName) {
    console.log(`🔄 Замена актива: с '${oldFundName}' на '${newFundName}'`);
    trackEvent('asset_replaced', { from: oldFundName, to: newFundName });
    const newFundNames = currentPortfolio.composition.map(asset => 
        asset.fund_name === oldFundName ? newFundName : asset.fund_name
    );
    await recalculatePortfolio({ selected_funds: newFundNames });
    document.getElementById('replace-asset-popup').classList.remove('active');
}

function handleReset() {
    console.log("🔄 Сброс изменений в портфеле.");
    trackEvent('click_reset_portfolio_edit');
    currentPortfolio = JSON.parse(localStorage.getItem('calculatedPortfolio'));
    displayPortfolioInfo();
    updateChart();
    tg.HapticFeedback.impactOccurred('light');
}

function handleSave() {
    console.log("💾 Сохранение портфеля и переход на portfolio.html.");
    trackEvent('click_save_portfolio_edit');
    localStorage.setItem('calculatedPortfolio', JSON.stringify(currentPortfolio));
    tg.HapticFeedback.notificationOccurred('success');
    window.location.href = 'portfolio.html';
}

// --- Логика API и перерасчета ---

async function fetchAllFunds() {
    if (!allFundsCache) {
        console.log("🌐 Запрашиваем список всех фондов с сервера...");
        const response = await fetch(API_URL_FUNDS);
        if (!response.ok) throw new Error("Не удалось загрузить список фондов.");
        allFundsCache = await response.json();
        console.log("✅ Список фондов получен и закэширован:", allFundsCache);
    }
}

async function recalculatePortfolio({ riskProfile = currentPortfolio.riskProfile, selected_funds = null }) {
    console.log("⏳ Начинаем перерасчет портфеля...", { riskProfile, selected_funds });
    isRecalculating = true;
    document.querySelector('.container').style.opacity = '0.5';
    try {
        const response = await fetch(API_URL_CALCULATE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                riskProfile,
                amount: currentPortfolio.initial_amount,
                term: currentPortfolio.term,
                selected_funds
            })
        });
        if (!response.ok) throw new Error("Ошибка при перерасчете портфеля.");
        currentPortfolio = await response.json();
        console.log("✅ Портфель успешно пересчитан:", currentPortfolio);
        displayPortfolioInfo();
        updateChart();
    } catch (error) {
        console.error("❌ Ошибка перерасчета:", error);
        tg.showAlert(error.message);
    } finally {
        isRecalculating = false;
        document.querySelector('.container').style.opacity = '1';
    }
}

// --- Логика попапов ---

function openReplacePopup(fundNameToReplace) {
    console.log(`↕️ Открываем попап для замены актива '${fundNameToReplace}'`);
    const popup = document.getElementById('replace-asset-popup');
    const optionsContainer = document.getElementById('replacement-options');
    const currentFund = allFundsCache.find(f => f.name === fundNameToReplace);
    if (!currentFund) {
        console.error(`Не удалось найти фонд '${fundNameToReplace}' в кэше.`);
        return;
    }

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
    console.log(" TUTORIAL: Показываем.");
    document.getElementById('tutorial-popup').classList.add('active');
    document.getElementById('risk-slider-section').style.zIndex = '1001';
    document.getElementById('portfolio-details').style.zIndex = '1001';
}

function hideTutorial() {
    console.log(" TUTORIAL: Скрываем.");
    document.getElementById('tutorial-popup').classList.remove('active');
    document.getElementById('risk-slider-section').style.zIndex = '';
    document.getElementById('portfolio-details').style.zIndex = '';
    localStorage.setItem('hasSeenEditTutorial', 'true');
}

// --- Логика графика и хелперы ---

function initializeChart() {
    console.log("📈 Инициализация графика (initializeChart).");
    const ctx = document.getElementById('performance-chart')?.getContext('2d');
    if (!ctx) {
        console.error("❌ Canvas для графика не найден!");
        return;
    }
    portfolioChartInstance = new Chart(ctx, {
        type: 'line', // <-- ИСПРАВЛЕНИЕ: Добавлен тип графика
        data: {},
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k ₽' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                x: { title: { display: true, text: 'Годы' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            },
            plugins: { legend: { display: false } }
        }
    });
    console.log("✅ Экземпляр графика создан.");
    updateChart();
}

function updateChart() {
    if (!portfolioChartInstance) {
        console.warn("⚠️ Попытка обновить график до его инициализации.");
        return;
    }
    console.log("📊 Обновляем данные графика...", currentPortfolio.forecast);
    portfolioChartInstance.data = {
        labels: currentPortfolio.forecast.labels,
        datasets: [
            { label: 'Макс.', data: currentPortfolio.forecast.max, borderColor: '#28a745', tension: 0.2 },
            { label: 'Сред.', data: currentPortfolio.forecast.avg, borderColor: '#f8f9fa', tension: 0.2 },
            { label: 'Мин.', data: currentPortfolio.forecast.min, borderColor: '#dc3545', tension: 0.2 }
        ]
    };
    portfolioChartInstance.update();
    console.log("✅ График обновлен.");
}

function updateRiskUI() {
    const sliderValue = document.getElementById('risk-slider').value;
    const { label } = sliderValueToRiskProfile(sliderValue);
    document.getElementById('risk-level-label').textContent = label;
    document.getElementById('portfolio-strategy-title').textContent = `${label} портфель`;
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

