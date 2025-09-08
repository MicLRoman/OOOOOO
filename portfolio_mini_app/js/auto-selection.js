import { trackEvent } from './script.js';

// --- Глобальные переменные и состояние ---
let currentStep = 1;
const investmentData = {
    amount: 50000,
    term: 5,
    riskProfile: 'moderate',
};
let chartInstance = null;
// --- ИЗМЕНЕНИЕ: Используем относительный URL ---
const API_URL = `${window.WEB_APP_BASE_URL}/api/calculate`;

// --- DOM-элементы ---
const backBtn = document.getElementById('back-btn');
const confirmAmountBtn = document.getElementById('confirm-amount-btn');
const confirmTermBtn = document.getElementById('confirm-term-btn');
const unknownTermBtn = document.getElementById('unknown-term-btn');
const confirmRiskBtn = document.getElementById('confirm-risk-btn');
const amountInput = document.getElementById('amount');
const termSlider = document.getElementById('term');
const termValueSpan = document.getElementById('term-value');
const riskButtons = document.querySelectorAll('.risk-btn');
const steps = [
    document.getElementById('step-1'),
    document.getElementById('step-2'),
    document.getElementById('step-3'),
];
const chartCanvas = document.getElementById('investment-chart');
const chartLegend = document.getElementById('chart-legend');

// --- Инициализация ---
document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_auto_selection');

    confirmAmountBtn.addEventListener('click', handleConfirmAmount);
    confirmTermBtn.addEventListener('click', handleConfirmTerm);
    unknownTermBtn.addEventListener('click', handleUnknownTerm);
    confirmRiskBtn.addEventListener('click', handleConfirmRisk);
    backBtn.addEventListener('click', handleGoBack);
    termSlider.addEventListener('input', handleTermChange);

    riskButtons.forEach(button => {
        button.addEventListener('click', () => handleRiskSelect(button.dataset.risk));
    });

    initializeChart();
});

// --- Обработчики событий ---

function handleConfirmAmount() {
    const amountValue = parseInt(amountInput.value, 10);
    if (isNaN(amountValue) || amountValue < 1000) {
        Telegram.WebApp.showAlert('Пожалуйста, введите сумму не менее 1000 ₽.');
        return;
    }
    investmentData.amount = amountValue;
    trackEvent('confirm_amount', { amount: investmentData.amount });
    currentStep = 2;
    updateStepVisibility();
    updateChart();
}

function handleTermChange() {
    const term = termSlider.value;
    investmentData.term = parseInt(term, 10);
    termValueSpan.textContent = term;
    updateChart();
}

function handleConfirmTerm() {
    trackEvent('confirm_term', { term: investmentData.term });
    currentStep = 3;
    updateStepVisibility();
    // ИЗМЕНЕНИЕ: Сразу показываем график для среднего риска
    handleRiskSelect('moderate');
}

function handleUnknownTerm() {
    investmentData.term = 5;
    termSlider.value = 5;
    termValueSpan.textContent = '5';
    trackEvent('confirm_term_unknown');
    currentStep = 3;
    updateStepVisibility();
    // ИЗМЕНЕНИЕ: Сразу показываем график для среднего риска
    handleRiskSelect('moderate');
}

// --- ИЗМЕНЕНИЕ: Функция стала асинхронной и обращается к API ---
async function handleRiskSelect(risk) {
    investmentData.riskProfile = risk;
    riskButtons.forEach(button => {
        button.classList.toggle('selected', button.dataset.risk === risk);
    });
    trackEvent('select_risk', { risk: investmentData.riskProfile });

    try {
        // Показываем спиннер или состояние загрузки
        chartCanvas.style.opacity = '0.5';

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(investmentData)
        });

        if (!response.ok) throw new Error('Ошибка сети при расчете графика');

        const backendData = await response.json();
        // Передаем данные с бэкенда в функцию обновления графика
        updateChart(backendData);

    } catch (error) {
        console.error("Ошибка при получении прогноза:", error);
        Telegram.WebApp.showAlert("Не удалось загрузить прогноз. Попробуйте еще раз.");
    } finally {
        // Убираем состояние загрузки
        chartCanvas.style.opacity = '1';
    }
}

function handleConfirmRisk() {
    trackEvent('confirm_risk_and_build');
    localStorage.setItem('investmentData', JSON.stringify(investmentData));
    window.location.href = 'loading.html';
}

function handleGoBack() {
    if (currentStep > 1) {
        currentStep--;
        updateStepVisibility();
        updateChart();
    }
}

function updateStepVisibility() {
    steps.forEach((step, index) => {
        step.classList.toggle('active', index + 1 === currentStep);
    });
    backBtn.disabled = currentStep === 1;
}

// --- Логика графика ---

function initializeChart() {
    if (!chartCanvas) return;
    const ctx = chartCanvas.getContext('2d');
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = () => {
        Chart.defaults.color = '#aaaaaa';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        chartInstance = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 400, easing: 'easeInOutQuad' },
                scales: {
                    y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k ₽' } },
                    x: { title: { display: true, text: 'Годы' } }
                },
                plugins: { legend: { display: false } }
            }
        });
        updateChart();
    };
    document.head.appendChild(script);
}

// --- ИЗМЕНЕНИЕ: Функция теперь может принимать данные с бэкенда ---
function updateChart(backendData = null) {
    if (!chartInstance) return;

    let datasets = [];
    let labels = [];

    // Если пришли данные с бэкенда (Шаг 3)
    if (backendData && backendData.forecast) {
        chartLegend.classList.add('visible');
        const forecast = backendData.forecast;
        labels = forecast.labels;
        datasets = [
            { label: 'Макс. доход', data: forecast.max, borderColor: '#28a745', tension: 0.1, fill: false },
            { label: 'Сред. доход', data: forecast.avg, borderColor: '#f8f9fa', tension: 0.1, fill: false },
            { label: 'Мин. доход', data: forecast.min, borderColor: '#dc3545', tension: 0.1, fill: false }
        ];
        chartInstance.options.scales.x.max = investmentData.term;
        delete chartInstance.options.scales.y.max; // Убираем фиксацию оси Y
    } 
    // Если данных нет (Шаги 1 и 2)
    else {
        chartLegend.classList.remove('visible');
        labels = Array.from({ length: 11 }, (_, i) => i);
        datasets.push({
            label: 'Сумма',
            data: Array(11).fill(investmentData.amount),
            borderColor: 'rgba(255, 255, 255, 0.5)',
            borderWidth: 2,
            pointRadius: 0
        });
        chartInstance.options.scales.x.max = (currentStep === 1) ? 10 : investmentData.term;
    }

    chartInstance.data.labels = labels;
    chartInstance.data.datasets = datasets;
    chartInstance.update();
}
