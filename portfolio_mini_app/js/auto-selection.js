import { trackEvent } from './script.js';

// --- Вспомогательная функция для "устранения дребезга" (debounce) ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --- Глобальное состояние ---
const state = {
    history: [],
    investmentData: {
        goal: null, 
        amount: 50000, 
        term_months: 12,
        monthlyContribution: 0,
        riskProfile: 'moderate',
        dreamAmount: null, 
        passiveIncome: null,
    },
    chartView: 'capital' 
};
let chartInstance = null;
let backendDataCache = null;
const API_URL = `${window.location.origin}/api/calculate`;
const PASSIVE_INCOME_RATE = 0.18; 
const RECALCULATION_DELAY = 500; // 50ms задержка

const debouncedMakeApiCall = debounce(makeApiCallAndUpdateChart, RECALCULATION_DELAY);

const goalPaths = {
    grow: ['step-grow-amount', 'step-grow-term', 'step-risk', 'step-contribution'],
    dream: ['step-dream-target', 'step-dream-initial', 'step-dream-term', 'step-risk', 'step-contribution'],
    passive: ['step-passive-initial', 'step-passive-term', 'step-passive-income', 'step-risk', 'step-contribution']
};

// --- Инициализация ---
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const goal = urlParams.get('goal');

    if (goal && goalPaths[goal]) {
        state.investmentData.goal = goal;
        state.history.push(goalPaths[goal][0]);
        
        trackEvent('page_view_auto_selection', { goal });
        initializeChart();
        setupEventListeners();
        updateView();
    } else {
        document.body.innerHTML = `<h1>Ошибка: цель не выбрана.</h1><a href="index.html">Вернуться на главную</a>`;
    }
});

function setupEventListeners() {
    document.querySelectorAll('.goal-btn').forEach(button => {
        button.addEventListener('click', () => {
            const goal = button.dataset.goal;
            state.investmentData.goal = goal;
            trackEvent('select_goal', { goal });
            navigateTo(goalPaths[goal][0]);
        });
    });

    document.querySelectorAll('.next-btn').forEach(button => {
        button.addEventListener('click', () => {
            const currentStepId = state.history[state.history.length - 1];
            collectDataFromStep(currentStepId);

            let stepData = { step: currentStepId };
            trackEvent('auto_selection_step_completed', stepData);

            const currentPath = goalPaths[state.investmentData.goal];
            const currentIndex = currentPath.indexOf(currentStepId);
            const nextStepId = currentPath[currentIndex + 1];
            if (nextStepId) navigateTo(nextStepId);
        });
    });

    document.querySelectorAll('.risk-btn').forEach(button => {
        button.addEventListener('click', () => {
            const riskProfile = button.dataset.risk;
            state.investmentData.riskProfile = riskProfile;
            trackEvent('auto_selection_risk_selected', { riskProfile: riskProfile });
            document.querySelectorAll('.risk-btn').forEach(btn => btn.classList.remove('selected'));
            button.classList.add('selected');
            debouncedMakeApiCall();
        });
    });

    document.getElementById('confirm-contribution-btn').addEventListener('click', () => {
        collectDataFromStep('step-contribution');
        trackEvent('confirm_all_and_build', state.investmentData);
        localStorage.setItem('investmentData', JSON.stringify(state.investmentData));
        localStorage.setItem('calculatedPortfolio', JSON.stringify(backendDataCache));
        window.location.href = 'loading.html';
    });

    document.getElementById('back-btn').addEventListener('click', () => {
        if (state.history.length > 1) {
            trackEvent('click_back_button_auto_selection', { fromStep: state.history[state.history.length - 1] });
            state.history.pop();
            updateView();
            updateChart();
        }
    });

    document.querySelectorAll('.toggle-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            state.chartView = button.dataset.view;
            trackEvent('switch_chart_view_auto_selection', { view: state.chartView });
            updateChart();
        });
    });

    document.querySelectorAll('input[type="range"], input[type="number"]').forEach(element => {
        element.addEventListener('input', () => {
             if (element.type === 'range' && element.id.startsWith('term-')) {
                const valueSpanId = element.id.replace('term-', 'term-value-');
                const valueSpan = document.getElementById(valueSpanId);
                if (valueSpan) valueSpan.textContent = formatTermForSlider(element.value);
             }
             if (element.id === 'contribution-slider') {
                 document.getElementById('contribution-value').textContent = `${parseInt(element.value).toLocaleString('ru-RU')} ₽`;
             }
             backendDataCache = null; 
             updateChart();
        });

        element.addEventListener('change', () => {
            const eventName = element.type === 'range' ? 'slider_changed' : 'input_number_changed';
            trackEvent(eventName, {
                elementId: element.id,
                value: element.value
            });
            // On change, trigger the debounced API call
            collectDataFromStep(element.closest('.step').id);
            debouncedMakeApiCall();
        });
    });

    const incomePassiveInput = document.getElementById('income-passive');
    if (incomePassiveInput) {
        incomePassiveInput.addEventListener('input', () => {
            const incomeValue = document.getElementById('income-passive').value;
            const toggle = document.getElementById('chart-view-toggle');
            toggle.classList.toggle('hidden', !(incomeValue && incomeValue > 0));
        });
    }

    const passiveHelpBtn = document.getElementById('passive-income-help-btn');
    if (passiveHelpBtn) {
        passiveHelpBtn.addEventListener('click', () => {
            trackEvent('click_passive_income_help');
            document.getElementById('passive-income-info-popup').classList.add('active');
        });
    }
    
    const chartHelpBtn = document.getElementById('chart-help-btn');
    if (chartHelpBtn) {
        chartHelpBtn.addEventListener('click', () => {
            trackEvent('click_calculation_method_help');
            document.getElementById('calculation-help-popup').classList.add('active');
        });
    }

    setupSlider('term-grow', 'term-value-grow', formatTermForSlider);
    setupSlider('term-dream', 'term-value-dream', formatTermForSlider);
    setupSlider('term-passive', 'term-value-passive', formatTermForSlider);
    setupSlider('contribution-slider', 'contribution-value', (val) => `${parseInt(val).toLocaleString('ru-RU')} ₽`);

    const passivePopup = document.getElementById('passive-income-info-popup');
    passivePopup.addEventListener('click', (e) => {
        if (e.target === passivePopup || e.target.closest('.popup-close, #close-passive-popup-btn')) {
            trackEvent('close_passive_income_popup');
            passivePopup.classList.remove('active');
            localStorage.setItem('hasSeenPassiveIncomeInfo', 'true');
        }
    });

    const calcHelpPopup = document.getElementById('calculation-help-popup');
    calcHelpPopup.addEventListener('click', (e) => {
        if (e.target === calcHelpPopup || e.target.closest('.popup-close, #close-calc-help-btn')) {
            trackEvent('close_calculation_method_popup');
            calcHelpPopup.classList.remove('active');
            localStorage.setItem('hasSeenCalculationHelp', 'true');
        }
    });
}

function navigateTo(stepId) {
    state.history.push(stepId);
    updateView();
    updateChart();

    if (stepId === 'step-passive-income' && !localStorage.getItem('hasSeenPassiveIncomeInfo')) {
        document.getElementById('passive-income-info-popup').classList.add('active');
    }

    if (stepId === 'step-risk' && !localStorage.getItem('hasSeenCalculationHelp')) {
        trackEvent('auto_show_calculation_help');
        document.getElementById('calculation-help-popup').classList.add('active');
    }
}

function updateView() {
    const currentStepId = state.history[state.history.length - 1];
    document.querySelectorAll('.step').forEach(step => {
        step.classList.toggle('active', step.id === currentStepId);
    });
    document.getElementById('back-btn').disabled = state.history.length <= 1;

    const isPassiveGoal = state.investmentData.goal === 'passive';
    const isAfterTermStep = state.history.includes('step-passive-income');
    document.getElementById('chart-view-toggle').classList.toggle('hidden', !(isPassiveGoal && isAfterTermStep));
}

function collectDataFromStep(activeStepId) {
    switch (activeStepId) {
        case 'step-grow-amount':
            state.investmentData.amount = parseInt(document.getElementById('amount-grow').value, 10) || 50000;
            break;
        case 'step-grow-term':
            state.investmentData.term_months = parseInt(document.getElementById('term-grow').value, 10) || 36;
            break;
        case 'step-dream-target':
            state.investmentData.dreamAmount = parseInt(document.getElementById('amount-dream').value, 10) || null;
            break;
        case 'step-dream-initial':
            state.investmentData.amount = parseInt(document.getElementById('initial-amount-dream').value, 10) || 50000;
            break;
        case 'step-dream-term':
            state.investmentData.term_months = parseInt(document.getElementById('term-dream').value, 10) || 36;
            break;
        case 'step-passive-initial':
            state.investmentData.amount = parseInt(document.getElementById('initial-amount-passive').value, 10) || 50000;
            break;
        case 'step-passive-term':
            state.investmentData.term_months = parseInt(document.getElementById('term-passive').value, 10) || 60;
            break;
        case 'step-passive-income':
            state.investmentData.passiveIncome = parseInt(document.getElementById('income-passive').value, 10) || null;
            break;
        case 'step-contribution':
            state.investmentData.monthlyContribution = parseInt(document.getElementById('contribution-slider').value, 10) || 0;
            break;
        case 'step-risk':
            const selectedRiskButton = document.querySelector('.risk-btn.selected');
            if (selectedRiskButton) {
                state.investmentData.riskProfile = selectedRiskButton.dataset.risk;
            }
            break;
    }
}

function initializeChart() {
    const ctx = document.getElementById('investment-chart').getContext('2d');
    const chartContainer = document.querySelector('.panel-right .chart-container');
    if (chartContainer && !document.getElementById('chart-legend')) {
        const legendDiv = document.createElement('div');
        legendDiv.id = 'chart-legend';
        legendDiv.className = 'chart-legend';
        chartContainer.appendChild(legendDiv);
    }

    Chart.defaults.color = '#aaaaaa';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    chartInstance = new Chart(ctx, { 
        type: 'line', 
        data: {}, 
        options: getChartOptions(),
    });
}

function getChartOptions(yAxisLabel = 'Сумма капитала, ₽') {
    return {
        responsive: true, 
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: false, ticks: { callback: value => (value / 1000) + 'k' }, title: { display: true, text: yAxisLabel } },
            x: { title: { display: true, text: 'Месяцы' } }
        },
        plugins: { 
            legend: { display: false }, 
            tooltip: { 
                 callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) label += ': ';
                        if (context.parsed.y !== null) {
                            label += new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(context.parsed.y);
                        }
                        return label;
                    }
                }
            } 
        }
    };
}

function updateChart() {
    if (!chartInstance) return;
    const currentStepId = state.history[state.history.length - 1];
    collectDataFromStep(currentStepId);

    const termSteps = ['step-grow-term', 'step-dream-term', 'step-passive-term'];

    if (termSteps.includes(currentStepId)) {
        debouncedMakeApiCall(); // Use debounced call for term steps as well
    } else if (backendDataCache) {
        drawForecast(backendDataCache);
    } else if (currentStepId === 'step-risk' || currentStepId === 'step-contribution') {
        debouncedMakeApiCall();
    }
    else {
        const { goal, dreamAmount, passiveIncome, amount, term_months } = state.investmentData;
        if (goal === 'passive' && passiveIncome) {
            const targetCapital = (passiveIncome * 12) / PASSIVE_INCOME_RATE;
            if (state.chartView === 'income') {
                drawPreviewWithTargetLine(passiveIncome, 0, term_months, 'Месячный доход, ₽');
            } else {
                drawPreviewWithTargetLine(targetCapital, amount, term_months);
            }
        } else if (goal === 'dream' && dreamAmount) {
            drawPreviewWithTargetLine(dreamAmount, amount, term_months);
        } else {
            drawInitialPreview(amount, term_months);
        }
    }
}


function drawInitialPreview(amount, termInMonths) {
    if (!chartInstance) return;
    chartInstance.options = getChartOptions('Сумма капитала, ₽');
    chartInstance.data = {
        labels: Array.from({ length: termInMonths + 1 }, (_, i) => i),
        datasets: [{
            label: 'Начальная сумма', data: Array(termInMonths + 1).fill(amount),
            borderColor: '#aaaaaa', borderWidth: 2, pointRadius: 0
        }]
    };
    chartInstance.update();
    updateChartLegend(chartInstance, state.investmentData, 'capital');
}

function drawPreviewWithTargetLine(targetAmount, startAmount, termInMonths, yAxisLabel = 'Сумма капитала, ₽') {
     if (!chartInstance) return;
    chartInstance.options = getChartOptions(yAxisLabel);
    chartInstance.data = {
        labels: Array.from({ length: termInMonths + 1 }, (_, i) => i),
        datasets: [
            { label: 'Начальное значение', data: Array(termInMonths + 1).fill(startAmount), borderColor: '#aaaaaa', borderWidth: 2, pointRadius: 0 },
            { label: 'Цель', data: Array(termInMonths + 1).fill(targetAmount), borderColor: '#dc2626', borderDash: [5, 5], borderWidth: 2, pointRadius: 0 }
        ]
    };
    chartInstance.update();
    updateChartLegend(chartInstance, state.investmentData, 'capital');
}

function drawForecast(data) {
    if (!chartInstance) return;
    const { forecast, goal_target_capital, monthly_income_forecast } = data;
    const isPassiveGoal = state.investmentData.goal === 'passive';
    const isIncomeView = isPassiveGoal && state.chartView === 'income';

    const yAxisLabel = isIncomeView ? 'Месячный доход, ₽' : 'Сумма капитала, ₽';
    chartInstance.options = getChartOptions(yAxisLabel);

    let datasets = [];
    let targetLineValue = null;

    if (isIncomeView) {
        datasets.push({ label: 'Прогноз дохода', data: monthly_income_forecast, borderColor: '#f8f9fa', tension: 0.1 });
        targetLineValue = state.investmentData.passiveIncome;
    } else {
        const currentStepId = state.history[state.history.length - 1];
        if (currentStepId === 'step-contribution' && state.investmentData.monthlyContribution > 0 && data.forecast_without_contribution) {
            datasets.push({ label: 'Макс. (без пополнений)', data: data.forecast_without_contribution.max, borderColor: 'rgba(40, 167, 69, 0.5)', borderDash: [5, 5], tension: 0.1 });
            datasets.push({ label: 'Сред. (без пополнений)', data: data.forecast_without_contribution.avg, borderColor: 'rgba(248, 249, 250, 0.5)', borderDash: [5, 5], tension: 0.1 });
            datasets.push({ label: 'Мин. (без пополнений)', data: data.forecast_without_contribution.min, borderColor: 'rgba(220, 53, 69, 0.5)', borderDash: [5, 5], tension: 0.1 });
        }
        
        datasets.push({ label: 'Макс. доход', data: forecast.max, borderColor: '#28a745', tension: 0.1 });
        datasets.push({ label: 'Сред. доход', data: forecast.avg, borderColor: '#f8f9fa', tension: 0.1 });
        datasets.push({ label: 'Мин. доход', data: forecast.min, borderColor: '#dc3545', tension: 0.1 });

        if (currentStepId === 'step-risk' && data.deposit_forecast) {
            datasets.push({
                label: 'Накопления на вкладе',
                data: data.deposit_forecast,
                borderColor: 'rgba(255, 255, 255, 0.5)',
                borderDash: [5, 5],
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1
            });
        }
        
        if (state.investmentData.goal === 'dream') {
            targetLineValue = state.investmentData.dreamAmount;
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

    chartInstance.data = { labels: forecast.labels, datasets };
    chartInstance.update();
    updateChartLegend(chartInstance, state.investmentData, state.chartView);
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

        const firstValue = dataset.data[0];
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
            case 'Накопления на вкладе': labelText = 'Доход на вкладе'; break;
            case 'Прогноз дохода': labelText = 'Прогноз дохода'; break;
            case 'Базовый сценарий': labelText = 'Базовый сценарий'; break;
            case 'Цель':
                isGoalLine = true;
                if (investmentData.goal === 'dream') {
                    labelText = 'Целевая сумма';
                } else if (investmentData.goal === 'passive') {
                    labelText = (currentChartView === 'income') ? 'Целевой доход' : 'Необходимая сумма';
                }
                break;
            default:
                if (dataset.label.includes('(без пополнений)')) return;
                break;
        }
        
        if (!isGoalLine && dataset.label !== 'Прогноз дохода' && typeof firstValue !== 'undefined') {
            const profit = lastValue - firstValue;
            const sign = profit >= 0 ? '+' : '';
            const profitClass = profit < 0 ? 'loss' : 'gain';
            profitText = `<span class="${profitClass}">${sign}${Math.round(profit).toLocaleString('ru-RU')} ₽</span>`;
        }

        const lineStyle = dataset.borderDash ? `border-bottom: 2px dashed ${color};` : `background-color: ${color};`;

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

async function makeApiCallAndUpdateChart() {
    const currentStepId = state.history[state.history.length - 1];
    const isApiStep = ['step-grow-term', 'step-dream-term', 'step-passive-term', 'step-risk', 'step-contribution'].includes(currentStepId);
    
    if (!isApiStep) {
        backendDataCache = null;
        updateChart();
        return;
    }

    try {
        chartInstance.canvas.style.opacity = '0.5';
        
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.investmentData)
        });
        if (!response.ok) throw new Error('Ошибка сети при основном запросе');
        
        backendDataCache = await response.json();

        if (currentStepId === 'step-contribution' && state.investmentData.monthlyContribution > 0) {
            const payloadWithoutContributions = {
                ...state.investmentData,
                monthlyContribution: 0
            };
            const responseWithout = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payloadWithoutContributions)
            });

            if (responseWithout.ok) {
                const dataWithout = await responseWithout.json();
                backendDataCache.forecast_without_contribution = dataWithout.forecast;
            } else {
                 console.warn("Не удалось загрузить прогноз без пополнений для сравнения.");
            }
        }
        
        drawForecast(backendDataCache);

    } catch (error) {
        console.error("Ошибка при получении прогноза:", error);
    } finally {
        chartInstance.canvas.style.opacity = '1';
    }
}

function setupSlider(sliderId, valueSpanId, formatter) {
    const slider = document.getElementById(sliderId);
    const valueSpan = document.getElementById(valueSpanId);
    if (slider && valueSpan) {
        valueSpan.textContent = formatter(slider.value);
    }
}

function formatTermForSlider(months) {
    months = parseInt(months, 10);
    let monthText;
    if (months % 10 === 1 && months % 100 !== 11) {
        monthText = 'месяц';
    } else if ([2, 3, 4].includes(months % 10) && ![12, 13, 14].includes(months % 100)) {
        monthText = 'месяца';
    } else {
        monthText = 'месяцев';
    }
    return `${months} ${monthText}`;
}

