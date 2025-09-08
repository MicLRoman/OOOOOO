import { trackEvent } from './script.js';

// --- Глобальное состояние ---
let portfolioChartInstance = null;
let popupChartInstance = null;
const API_BASE_URL = "[https://oooooo-q7ete6l6t-mishashegoleh-2041s-projects.vercel.app/](https://oooooo-q7ete6l6t-mishashegoleh-2041s-projects.vercel.app/)";

// --- Инициализация страницы ---
document.addEventListener('DOMContentLoaded', async () => {
    trackEvent('page_view_portfolio');
    try {
        const storedPortfolio = localStorage.getItem('calculatedPortfolio');
        let portfolioData;

        if (storedPortfolio) {
            portfolioData = JSON.parse(storedPortfolio);
        } else {
            const investmentData = JSON.parse(localStorage.getItem('investmentData'));
            if (!investmentData) throw new Error("Данные для расчета не найдены.");
            
            portfolioData = await calculatePortfolio(investmentData);
            localStorage.setItem('calculatedPortfolio', JSON.stringify(portfolioData));
        }

        if (portfolioData) {
            renderPage(portfolioData);
            initializePageLogic(portfolioData);

            if (!localStorage.getItem('hasSeenPortfolioInfo')) {
                showInfoPopup();
            }
        }

    } catch (error) {
        console.error("Критическая ошибка на странице портфеля:", error);
        document.querySelector('.container').innerHTML = `<h1>Ошибка загрузки</h1><p>${error.message}. Пожалуйста, начните заново.</p><a href="index.html" class="btn btn-main">Начать заново</a>`;
    }
});

// --- Функции для работы с API ---
async function calculatePortfolio(data) {
    const response = await fetch(`${API_BASE_URL}/api/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Не удалось рассчитать портфель. Попробуйте позже.');
    return await response.json();
}

// --- Основная функция рендеринга ---
function renderPage(portfolioData) {
    const { initial_amount, term, strategy_name, composition, forecast } = portfolioData;
    const minForecastValue = forecast.min[forecast.min.length - 1];
    const guaranteedIncome = minForecastValue > initial_amount ? minForecastValue - initial_amount : 0;
    const container = document.querySelector('.container');
    if (!container) return;

    const mainHTML = `
        <div class="portfolio-header">
            <h1 class="page-title">Ваш портфель</h1>
            <div class="header-buttons">
                <button class="btn btn-main" id="edit-portfolio-btn">Редактировать</button>
                <button class="btn btn-secondary" id="restart-btn">Начать сначала</button>
            </div>
        </div>
        <div class="portfolio-card">
            <div class="info-item"><span class="label">Сумма:</span><span class="value">${initial_amount.toLocaleString('ru-RU')} ₽</span></div>
            <div class="info-item"><span class="label">Срок:</span><span class="value">${term} лет</span></div>
            <div class="info-item"><span class="label">Стратегия:</span><span class="value">${strategy_name}</span></div>
            <div class="info-item guaranteed-income"><span class="label">Гарантированный доход:</span><span class="value">+${guaranteedIncome.toLocaleString('ru-RU')} ₽</span></div>
            <div class="assets-section-toggle" id="assets-toggle">
                <div class="assets-toggle-header"><h4>Активы в портфеле</h4><span class="toggle-icon">▼</span></div>
                <div class="assets-list-container"><div class="assets-list" id="assets-list">
                    ${composition.map(asset => `<div class="asset-item"><span class="asset-name">${asset.fund_name}</span><span class="asset-percent">${asset.percentage.toFixed(0)}%</span></div>`).join('')}
                </div></div>
            </div>
        </div>
        <div class="view-switcher">
            <button class="switcher-btn active" data-view="chart">График успеха</button>
            <button class="switcher-btn" data-view="similar">Похожие портфели</button>
        </div>
        <div class="content-views">
            <div id="chart-view" class="view active">
                <div class="chart-container">
                    <div class="chart-header">
                        <div><h3 class="chart-title">Прогноз роста</h3><p class="chart-subtitle">Динамика вашего портфеля</p></div>
                        <div class="chart-controls">
                            <button class="chart-mode-btn" data-mode="5y">5 лет</button>
                            <button class="chart-mode-btn" data-mode="1y">1 год</button>
                            <button class="chart-mode-btn active" data-mode="future">Прогноз</button>
                        </div>
                    </div>
                    <div class="chart-wrapper"><canvas id="performance-chart"></canvas></div>
                </div>
            </div>
            <div id="similar-view" class="view">
                <div class="similar-container">
                    <h3 class="similar-title">Успешные практики других людей</h3>
                     <div class="slider-container">
                        <button class="slider-arrow prev" id="slider-prev">‹</button>
                        <div class="slider-wrapper" id="slider-wrapper"></div>
                        <button class="slider-arrow next" id="slider-next">›</button>
                    </div>
                </div>
            </div>
        </div>
        <div class="confirm-section"><button class="btn btn-main btn-large" id="confirm-portfolio-btn">Подтвердить портфель</button></div>
    `;
    
    const infoPopupHTML = `
        <div id="info-popup" class="popup-overlay">
            <div class="popup-content info-popup-content">
                <button class="popup-close" id="info-popup-close">&times;</button>
                <h3>Ваш стартовый портфель</h3>
                <p><strong>Это шаблонный портфель, который вы можете изменить как угодно в редакторе.</strong></p>
                <p>Он уже сбалансирован и диверсифицирован по разным активам (акции, облигации, золото) для снижения рисков.</p>
                <button class="btn btn-main" id="info-popup-confirm">Понятно</button>
            </div>
        </div>
    `;
    
    container.innerHTML = mainHTML + infoPopupHTML;
}

function initializePageLogic(portfolioData) {
    initializeAssetsToggle();
    initializeTabs();
    initializeSlider();
    initializeChart(portfolioData); 
    initializePopup();

    document.getElementById('edit-portfolio-btn')?.addEventListener('click', () => {
        trackEvent('click_edit_portfolio');
        window.location.href = 'edit-portfolio.html';
    });
    
    document.getElementById('restart-btn')?.addEventListener('click', () => {
        trackEvent('click_restart_portfolio');
        localStorage.clear();
        window.location.href = 'index.html';
    });

    document.getElementById('confirm-portfolio-btn')?.addEventListener('click', () => {
        trackEvent('click_confirm_portfolio');
        window.location.href = 'confirm-portfolio.html';
    });
}

function initializeAssetsToggle() {
    const toggle = document.getElementById('assets-toggle');
    toggle?.addEventListener('click', () => toggle.classList.toggle('expanded'));
}

function initializeTabs() {
    const switcherBtns = document.querySelectorAll('.switcher-btn');
    switcherBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const viewToShow = btn.dataset.view;
            switcherBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.view').forEach(view => view.classList.toggle('active', view.id === `${viewToShow}-view`));
            trackEvent('switch_portfolio_view', { view: viewToShow });
        });
    });
}

function initializeSlider() {
    const sliderWrapper = document.getElementById('slider-wrapper');
    if (!sliderWrapper) return;
    const similarPortfolios = [
        { title: 'Петр, 22 года', desc: 'Начинающий инвестор, умеренная стратегия.', returns: '+15%', riskProfile: 'moderate' },
        { title: 'Анна, 35 лет', desc: 'Опытный инвестор, агрессивный рост.', returns: '+25%', riskProfile: 'aggressive' },
        { title: 'Иван, 50 лет', desc: 'Консервативный подход, стабильный доход.', returns: '+8%', riskProfile: 'conservative' },
    ];
    sliderWrapper.innerHTML = `<div class="slider-track">${similarPortfolios.map((p, index) => `
        <div class="slide">
            <h4 class="slide-title">${p.title}</h4>
            <p class="slide-desc">${p.desc}</p>
            <p class="slide-return">${p.returns} годовых</p>
            <button class="btn btn-secondary btn-expand-portfolio" data-index="${index}">Развернуть портфель</button>
        </div>`).join('')}</div>`;
    document.querySelectorAll('.btn-expand-portfolio').forEach(btn => {
        btn.addEventListener('click', () => {
            const portfolioData = similarPortfolios[btn.dataset.index];
            showPortfolioPopup(portfolioData);
        });
    });
    const track = document.querySelector('.slider-track');
    let currentIndex = 0;
    const updateSlider = () => track && (track.style.transform = `translateX(-${currentIndex * 100}%)`);
    document.getElementById('slider-prev')?.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + similarPortfolios.length) % similarPortfolios.length;
        updateSlider();
    });
    document.getElementById('slider-next')?.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % similarPortfolios.length;
        updateSlider();
    });
}

function initializePopup() {
    const popup = document.getElementById('info-popup');
    if (popup) {
        popup.addEventListener('click', (e) => {
            if (e.target === popup || e.target.closest('#info-popup-close, #info-popup-confirm')) {
                hideInfoPopup();
            }
        });
    }
}

function showPortfolioPopup(data) { /* TODO */ }

function showInfoPopup() {
    document.getElementById('info-popup')?.classList.add('active');
}

function hideInfoPopup() {
    document.getElementById('info-popup')?.classList.remove('active');
    localStorage.setItem('hasSeenPortfolioInfo', 'true');
}

function initializeChart(portfolioData) {
    const ctx = document.getElementById('performance-chart')?.getContext('2d');
    if (!ctx) return;
    if (portfolioChartInstance) portfolioChartInstance.destroy();
    portfolioChartInstance = new Chart(ctx, {
        type: 'line', data: {},
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                 y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k ₽' } },
                 x: { title: { display: true, text: 'Годы' } }
            },
            plugins: { legend: { display: false } }
        }
    });
    document.querySelectorAll('.chart-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chart-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const mode = btn.dataset.mode;
            updateChart(mode, portfolioData);
            trackEvent('switch_chart_mode', { mode });
        });
    });
    updateChart('future', portfolioData);
}

function updateChart(mode, portfolioData) {
    if (!portfolioChartInstance) return;
    const chartData = generateChartData(mode, portfolioData);
    portfolioChartInstance.data = chartData.data;
    portfolioChartInstance.options.scales.x.title.text = chartData.xTitle;
    portfolioChartInstance.update();
}

// --- ИСПРАВЛЕННАЯ ЛОГИКА ГРАФИКА ---
function generateChartData(mode, portfolioData) {
    const { initial_amount, term, forecast } = portfolioData;

    if (mode === 'future') {
        return {
            data: {
                labels: forecast.labels,
                datasets: [
                    { label: 'Макс. доход', data: forecast.max, borderColor: '#28a745', tension: 0.1, fill: false },
                    { label: 'Сред. доход', data: forecast.avg, borderColor: '#f8f9fa', tension: 0.1, fill: false },
                    { label: 'Мин. доход', data: forecast.min, borderColor: '#dc3545', tension: 0.1, fill: false }
                ]
            },
            xTitle: 'Годы (прогноз)'
        };
    } else {
        const historyYears = mode === '1y' ? 1 : 5;
        
        // 1. Генерируем исторические данные
        const historyLabels = Array.from({ length: historyYears + 1 }, (_, i) => `-${historyYears - i}г`);
        let historicalData = [initial_amount];
        let lastVal = initial_amount;
        for (let i = 0; i < historyYears; i++) {
            lastVal /= (1 + (Math.random() * 0.1 + 0.05));
            historicalData.unshift(lastVal);
        }

        // 2. Берем будущие данные из прогноза
        const futureLabels = forecast.labels.slice(1).map(y => `+${y}г`); // "+1г", "+2г" ...

        // 3. Создаем "пустышки", чтобы сдвинуть прогноз вправо
        const emptyHistory = Array(historyYears).fill(null);

        return {
            data: {
                labels: historyLabels.concat(futureLabels),
                datasets: [
                    // Историческая линия
                    { data: historicalData.concat(Array(term).fill(null)), borderColor: '#f8f9fa', tension: 0.1, label: 'История' },
                    // Прогнозные линии, сдвинутые вправо
                    { data: emptyHistory.concat(forecast.max), borderColor: '#28a745', tension: 0.1, borderDash: [5, 5], label: 'Макс. прогноз' },
                    { data: emptyHistory.concat(forecast.avg), borderColor: '#f8f9fa', tension: 0.1, borderDash: [5, 5], label: 'Сред. прогноз' },
                    { data: emptyHistory.concat(forecast.min), borderColor: '#dc3545', tension: 0.1, borderDash: [5, 5], label: 'Мин. прогноз' },
                ]
            },
            xTitle: `История за ${historyYears} лет и прогноз на ${term} лет`
        };
    }
}

