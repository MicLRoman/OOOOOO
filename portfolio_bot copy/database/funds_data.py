# portfolio_bot/database/funds_data.py
# ФИНАЛЬНАЯ ВЕРСИЯ.
# Этот файл содержит отобранный и очищенный список фондов для использования в боте.
# Данные о доходности и волатильности рассчитаны на основе реальной истории цен.

PASSIVE_INCOME_RATE_PERCENT = 18.0

# ==============================================================================
# БАЗА ДАННЫХ АКТИВОВ (ОЧИЩЕННАЯ)
# ==============================================================================

# --- Облигации (остаются без изменений) ---
BONDS = [
     {
        "name": "МТС (облигация)", "risk_level": "bonds",
        "annual_return_percent": 18.0, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A109A00"
     },
     {
        "name": "ЕвроТранс (облигация)", "risk_level": "bonds",
        "annual_return_percent": 21.0, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A109LH7"
     },
     {
        "name": "СОВКОМБАНК (облигация)", "risk_level": "bonds",
        "annual_return_percent": 18.3, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A10CMG6"
     }
]

# --- Фонды акций (финальный отобранный список) ---
EQUITY_FUNDS = [
    # --- НИЗКИЙ РИСК ---
    # {
    #     "name": "Альфа-Капитал Облигации Плюс", "risk_level": "low",
    #     "annual_return_percent": 24.06, "volatility_percent": 9.78,
    #     "purchase_url": "https://finuslugi.ru/invest/funds/5f6d1ba3-2049-49be-b755-000c901d1f28"
    # },
    {
        "name": "Альфа-Капитал - Накопительный", "risk_level": "low",
        "annual_return_percent": 22.67, "volatility_percent": 2.21,
        "purchase_url": "https://finuslugi.ru/invest/funds/e17245ef-514d-4a2a-be32-b2a8c5e29a39"
    },
    {
        "name": "ТРИНФИКО – Российские доходные облигации", "risk_level": "low",
        "annual_return_percent": 21.33, "volatility_percent": 10.45,
        "purchase_url": "https://finuslugi.ru/invest/funds/1b535701-8dc2-439a-afd5-4c82eb141ec1"
    },
    {
        "name": "Солид - Российские облигации", "risk_level": "low",
        "annual_return_percent": 20.47, "volatility_percent": 11.02,
        "purchase_url": "https://finuslugi.ru/invest/funds/020db42a-9c02-43ed-bc45-36c8995652f4"
    },
    {
        "name": "ДОХОДЪ – Денежный рынок", "risk_level": "low",
        "annual_return_percent": 16.64, "volatility_percent": 1.11,
        "purchase_url": "https://finuslugi.ru/invest/funds/84b3eacc-b641-4b34-bf47-74caf12ef231"
    },
    {
        "name": "Альфа-Капитал – Валютные облигации", "risk_level": "low",
        "annual_return_percent": 13.49, "volatility_percent": 10.68,
        "purchase_url": "https://finuslugi.ru/invest/funds/c899d604-9123-4375-a304-ebc76eb87147"
    },

    # --- СРЕДНИЙ РИСК ---
    {
        "name": "ДОХОДЪ – Перспективные облигации", "risk_level": "medium",
        "annual_return_percent": 27.19, "volatility_percent": 20.31,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c27fa7a-7b39-421e-af16-6c61c557bfe2"
    },
    {
        "name": "Солид – Пенсионный капитал", "risk_level": "medium",
        "annual_return_percent": 9.27, "volatility_percent": 16.79,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c568f93-5f58-4418-b3ef-4bf45d658539"
    },

    # --- ВЫСОКИЙ РИСК ---
    {
        "name": "ДОХОДЪ – Золото", "risk_level": "high",
        "annual_return_percent": 39.86, "volatility_percent": 24.59,
        "purchase_url": "https://finuslugi.ru/invest/funds/e18b6907-a8d7-4d1e-9fa2-472dc6b9897d"
    },
    {
        "name": "Альфа-Капитал - Великолепная семерка", "risk_level": "high",
        "annual_return_percent": 6.79, "volatility_percent": 25.43,
        "purchase_url": "https://finuslugi.ru/invest/funds/75d35014-d64a-419d-bfa7-e29d40b7907e"
    }
]


# Объединяем все фонды в один список для удобства
ALL_FUNDS = BONDS + EQUITY_FUNDS


# ==============================================================================
# ШАБЛОНЫ СТРАТЕГИЙ (остаются без изменений)
# ==============================================================================
STRATEGY_TEMPLATES = {
    "no-loss": {
        "name": "Гарантированный",
        "composition": { "bonds": 85, "low": 15, "medium": 0, "high": 0 }
    },
    "conservative": {
        "name": "Консервативная",
        "composition": { "bonds": 40, "low": 40, "medium": 15, "high": 5 }
    },
    "moderate-conservative": {
        "name": "Умеренно-консервативная",
        "composition": { "bonds": 30, "low": 35, "medium": 25, "high": 10 }
    },
    "moderate": {
        "name": "Умеренная",
        "composition": { "bonds": 20, "low": 30, "medium": 30, "high": 20 }
    },
    "moderate-aggressive": {
        "name": "Умеренно-агрессивная",
        "composition": { "bonds": 10, "low": 25, "medium": 35, "high": 30 }
    },
    "aggressive": {
        "name": "Агрессивная",
        "composition": { "bonds": 5, "low": 15, "medium": 30, "high": 50 }
    }
}


# ==============================================================================
# НАРОДНЫЕ ОБЛИГАЦИИ (остаются без изменений)
# ==============================================================================
PEOPLES_BONDS = [
     { "name": "МТС (облигация)", "annual_return_percent": 11.0 },
     { "name": "ЕвроТранс (облигация)", "annual_return_percent": 21.0 },
     { "name": "СОВКОМБАНК (облигация)", "annual_return_percent": 18.3 },
]

