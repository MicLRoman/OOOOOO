import { trackEvent } from './script.js';

// Ждем, пока вся страница загрузится
document.addEventListener('DOMContentLoaded', () => {
    // --- НОВЫЙ КОД ДЛЯ POPUP ---
    const introPopup = document.getElementById('intro-popup');

    // Показываем попап, если его еще не видели
    if (!localStorage.getItem('hasSeenIntroPopup')) {
        showIntroPopup();
    }
    
    // Назначаем обработчики для закрытия попапа
    if (introPopup) {
        introPopup.addEventListener('click', (e) => {
            if (e.target === introPopup || e.target.closest('#intro-popup-close, #intro-popup-confirm')) {
                hideIntroPopup();
            }
        });
    }
    // --- КОНЕЦ НОВОГО КОДА ---


    const autoSelectionBtn = document.getElementById('auto-selection-btn');
    const demoPortfolioBtn = document.getElementById('demo-portfolio-btn');

    if (autoSelectionBtn) {
        autoSelectionBtn.addEventListener('click', () => {
            trackEvent('click_auto_selection');
            window.location.href = 'auto-selection.html';
        });
    }

    if (demoPortfolioBtn) {
        demoPortfolioBtn.addEventListener('click', () => {
            trackEvent('click_demo_portfolio');
            Telegram.WebApp.openLink('https://v0-investment-constructor-ui.vercel.app/');
        });
    }
});

// --- НОВЫЕ ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ POPUP ---
function showIntroPopup() {
    const popup = document.getElementById('intro-popup');
    if (popup) popup.classList.add('active');
}

function hideIntroPopup() {
    const popup = document.getElementById('intro-popup');
    if (popup) popup.classList.remove('active');
    // Устанавливаем флаг, чтобы больше не показывать
    localStorage.setItem('hasSeenIntroPopup', 'true');
}

