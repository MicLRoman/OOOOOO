import { trackEvent } from './script.js';

document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_main');

    // Назначаем обработчики на карточки с целями
    document.querySelectorAll('.goal-card').forEach(card => {
        card.addEventListener('click', () => {
            const goal = card.dataset.goal;
            if (goal) {
                // --- НОВОЕ: Отслеживаем клик по карточке цели ---
                // Это событие фиксирует первоначальный интерес пользователя к цели.
                trackEvent('click_goal_card', { goal });
                
                // Открываем соответствующий pop-up
                showGoalPopup(goal);
            }
        });
    });

    // Назначаем обработчики на кнопки подтверждения внутри pop-up'ов
    document.querySelectorAll('.goal-popup').forEach(popup => {
        const confirmBtn = popup.querySelector('.popup-confirm-btn');
        const goal = popup.id.replace('-popup', '');

        if (confirmBtn) {
            confirmBtn.addEventListener('click', (e) => {
                e.preventDefault();
                // Сохраняем выбранную цель
                localStorage.setItem('selectedGoal', goal);
                // Это событие отслеживает уже подтвержденный выбор цели
                trackEvent('select_goal_on_main', { goal: goal });
                // Переходим на страницу автоподбора
                window.location.href = confirmBtn.href;
            });
        }
        
        // Обработчик для закрытия pop-up'а
        popup.addEventListener('click', (e) => {
            if (e.target === popup || e.target.classList.contains('popup-close')) {
                hideGoalPopup(goal);
            }
        });
    });


    // Назначаем обработчик на кнопку "Демо-портфель"
    const demoPortfolioBtn = document.getElementById('demo-portfolio-btn');
    if (demoPortfolioBtn) {
        demoPortfolioBtn.addEventListener('click', () => {
            trackEvent('click_demo_portfolio');
            Telegram.WebApp.openLink('https://v0-investment-constructor-ui.vercel.app/');
        });
    }
});

// --- ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ POPUP ---
function showGoalPopup(goal) {
    const popup = document.getElementById(`${goal}-popup`);
    if (popup) {
        popup.classList.add('active');
    }
}

function hideGoalPopup(goal) {
    const popup = document.getElementById(`${goal}-popup`);
    if (popup) {
        popup.classList.remove('active');
    }
}
