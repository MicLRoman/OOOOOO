# portfolio_bot/database/funds_data.py

# ==============================================================================
# БАЗА ДАННЫХ ПИФов
# ==============================================================================
# ... (здесь без изменений)

ALL_FUNDS = [
    # --- Низкий риск ---
    {
        "name": "ГЕРОИ – Рублевые перспективы", "risk_level": "low",
        "total_return_percent": 37.13, "annual_return_percent": 12.38, "volatility_percent": 5,
        "min_investment": 30000, "management_company": "ООО УК 'ГЕРОИ'"
    },
    {
        "name": "ТРИНФИКО – Российские доходные облигации", "risk_level": "low",
        "total_return_percent": 18.98, "annual_return_percent": 9.49, "volatility_percent": 5,
        "min_investment": 1000, "management_company": "АО 'Управляющая Компания ТРИНФИКО'"
    },
    {
        "name": "Солид - Российские облигации", "risk_level": "low",
        "total_return_percent": 18.41, "annual_return_percent": 9.21, "volatility_percent": 5,
        "min_investment": 1000, "management_company": "АО 'СОЛИД МЕНЕДЖМЕНТ'"
    },
    {
        "name": "ДОХОДЪ – Денежный рынок", "risk_level": "low",
        "total_return_percent": 15.33, "annual_return_percent": 15.33, "volatility_percent": 3,
        "min_investment": 1000, "management_company": "ООО 'УК 'ДОХОДЪ'"
    },

    # --- Средний риск ---
    {
        "name": "Альфа-Капитал Облигации Плюс", "risk_level": "medium",
        "total_return_percent": 24.27, "annual_return_percent": 11.8, "volatility_percent": 10,
        "min_investment": 100, "management_company": "ООО УК 'Альфа-Капитал'"
    },
    {
        "name": "ДОХОДЪ – Перспективные облигации", "risk_level": "medium",
        "total_return_percent": 21.99, "annual_return_percent": 10.99, "volatility_percent": 12,
        "min_investment": 1000, "management_company": "ООО 'УК 'ДОХОДЪ'"
    },
    {
        "name": "Альфа-Капитал Баланс", "risk_level": "medium",
        "total_return_percent": 12.38, "annual_return_percent": 8.1, "volatility_percent": 15,
        "min_investment": 100, "management_company": "ООО УК 'Альфа-Капитал'"
    },
    {
        "name": "Солид - Индекс МосБиржи", "risk_level": "medium",
        "total_return_percent": 5.87, "annual_return_percent": 5.87, "volatility_percent": 18,
        "min_investment": 1000, "management_company": "АО 'СОЛИД МЕНЕДЖМЕНТ'"
    },

    # --- Высокий риск ---
    {
        "name": "Альфа-Капитал – Высокодоходные облигации", "risk_level": "high",
        "total_return_percent": 27.48, "annual_return_percent": 13.5, "volatility_percent": 20,
        "min_investment": 50000, "management_company": "ООО УК 'Альфа-Капитал'"
    },
    {
        "name": "Альфа-Капитал Акции компаний роста", "risk_level": "high",
        "total_return_percent": 13.29, "annual_return_percent": 9.8, "volatility_percent": 25,
        "min_investment": 100, "management_company": "ООО УК 'Альфа-Капитал'"
    },
    {
        "name": "Альфа-Капитал – Ликвидные акции", "risk_level": "high",
        "total_return_percent": 11.03, "annual_return_percent": 7.5, "volatility_percent": 22,
        "min_investment": 100, "management_company": "ООО УК 'Альфа-Капитал'"
    },
    {
        "name": "ДОХОДЪ – Акции первого эшелона", "risk_level": "high",
        "total_return_percent": 5.08, "annual_return_percent": 5.08, "volatility_percent": 28,
        "min_investment": 1000, "management_company": "ООО 'УК 'ДОХОДЪ'"
    },
]


# ==============================================================================
# ШАБЛОНЫ СТРАТЕГИЙ
# ==============================================================================
# "Рецепты" для нашего калькулятора.
# Ключи - это 'risk_level' из ALL_FUNDS, значения - доля в % в портфеле.

STRATEGY_TEMPLATES = {
    "conservative": {
        "name": "Консервативная",
        "composition": { "low": 60, "medium": 25, "high": 15 }
    },
    # --- НОВЫЙ ПРОФИЛЬ ---
    "moderate-conservative": {
        "name": "Умеренно-консервативная",
        "composition": { "low": 45, "medium": 35, "high": 20 }
    },
    "moderate": {
        "name": "Умеренная",
        "composition": { "low": 30, "medium": 40, "high": 30 }
    },
    # --- НОВЫЙ ПРОФИЛЬ ---
    "moderate-aggressive": {
        "name": "Умеренно-агрессивная",
        "composition": { "low": 20, "medium": 35, "high": 45 }
    },
    "aggressive": {
        "name": "Агрессивная",
        "composition": { "low": 10, "medium": 30, "high": 60 }
    }
}
