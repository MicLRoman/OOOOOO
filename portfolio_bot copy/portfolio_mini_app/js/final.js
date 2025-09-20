import { trackEvent } from './script.js';

document.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view_final');

    const portfolioData = JSON.parse(localStorage.getItem('calculatedPortfolio'));
    
    if (!portfolioData || !portfolioData.composition) {
        document.getElementById('assets-purchase-list').innerHTML = '<p class="error-message">Не удалось загрузить данные портфеля. Пожалуйста, вернитесь и соберите его заново.</p>';
        return;
    }

    renderPurchaseList(portfolioData);
});

function renderPurchaseList(portfolioData) {
    const listContainer = document.getElementById('assets-purchase-list');
    listContainer.innerHTML = ''; // Очищаем плейсхолдер

    const { initial_amount, composition } = portfolioData;

    composition.forEach(asset => {
        // Пропускаем активы с долей 0% или без ссылки на покупку
        if (asset.percentage <= 0 || !asset.purchase_url) {
            return;
        }

        const amountToBuy = (initial_amount * (asset.percentage / 100)).toFixed(2);
        
        const assetElement = document.createElement('div');
        assetElement.className = 'asset-item';

        assetElement.innerHTML = `
            <span class="asset-name">${asset.fund_name}</span>
            <div class="asset-amount">
                <span>${parseFloat(amountToBuy).toLocaleString('ru-RU')} ₽</span>
                <button class="copy-btn" data-amount="${amountToBuy}" title="Копировать сумму">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                      <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zM-1 2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5z"/>
                    </svg>
                </button>
            </div>
            <a href="${asset.purchase_url}" target="_blank" class="btn btn-main purchase-link">Купить</a>
        `;

        listContainer.appendChild(assetElement);
    });

    // Добавляем обработчики для кнопок "Копировать"
    listContainer.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', () => {
            const amount = button.dataset.amount;
            navigator.clipboard.writeText(amount).then(() => {
                trackEvent('copy_purchase_amount', { amount });
                button.classList.add('copied');
                setTimeout(() => button.classList.remove('copied'), 1500);
            }).catch(err => {
                console.error('Не удалось скопировать текст: ', err);
            });
        });
    });
}
