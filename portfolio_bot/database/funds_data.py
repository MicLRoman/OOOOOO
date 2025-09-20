# portfolio_bot/database/funds_data.py
# ВЕРСИЯ С ДЕТАЛЬНЫМИ ДАННЫМИ ИЗ JSON
# Этот файл содержит актуализированный список фондов с подробной информацией.

PASSIVE_INCOME_RATE_PERCENT = 18.0

# ==============================================================================
# БАЗА ДАННЫХ АКТИВОВ (ОБНОВЛЕННАЯ)
# ==============================================================================

# --- Облигации (добавлены поля для консистентности) ---
BONDS = [
     {
        "name": "МТС (облигация)", "risk_level": "bonds",
        "annual_return_percent": 18.0, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A109A00",
        "one_year_return_str": "+18.0%", "min_purchase_str": "От 1 000 ₽",
        "description": "Корпоративная облигация компании МТС. Стабильный инструмент с фиксированной доходностью."
     },
     {
        "name": "ЕвроТранс (облигация)", "risk_level": "bonds",
        "annual_return_percent": 21.0, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A109LH7",
        "one_year_return_str": "+21.0%", "min_purchase_str": "От 1 000 ₽",
        "description": "Высокодоходная корпоративная облигация компании ЕвроТранс."
     },
     {
        "name": "СОВКОМБАНК (облигация)", "risk_level": "bonds",
        "annual_return_percent": 18.3, "volatility_percent": 0,
        "purchase_url": "https://finuslugi.ru/invest/bonds/RU000A10CMG6",
        "one_year_return_str": "+18.3%", "min_purchase_str": "От 1 000 ₽",
        "description": "Корпоративная облигация Совкомбанка. Надежный эмитент."
     }
]

# --- Фонды акций (данные из JSON) ---
EQUITY_FUNDS = [
    # --- НИЗКИЙ РИСК ---
    {
        "name": "Альфа-Капитал Облигации Плюс", "risk_level": "low",
        "annual_return_percent": 27.72, "volatility_percent": 9.78,
        "purchase_url": "https://finuslugi.ru/invest/funds/5f6d1ba3-2049-49be-b755-000c901d1f28",
        "one_year_return_str": "+27,72%", "min_purchase_str": "От 100 ₽",
        "description": "В составе фонда — ОФЗ и облигации крупных российских компаний, что позволяет занять стратегическую позицию на рынке рублевого долга."
    },
    {
        "name": "Альфа-Капитал - Накопительный", "risk_level": "low",
        "annual_return_percent": 22.18, "volatility_percent": 2.21,
        "purchase_url": "https://finuslugi.ru/invest/funds/e17245ef-514d-4a2a-be32-b2a8c5e29a39",
        "one_year_return_str": "+22,18%", "min_purchase_str": "От 100 ₽",
        "description": "Фонд инвестирует в инструменты с фиксированной доходностью, преимущественно в корпоративные и государственные облигации."
    },
    {
        "name": "ТРИНФИКО – Российские доходные облигации", "risk_level": "low",
        "annual_return_percent": 21.33, "volatility_percent": 10.45,
        "purchase_url": "https://finuslugi.ru/invest/funds/1b535701-8dc2-439a-afd5-4c82eb141ec1",
        "one_year_return_str": "+21,33%", "min_purchase_str": "От 1 000 ₽",
        "description": "Фонд инвестирует в государственные, муниципальные и корпоративные облигации. Цель — обеспечить доходность выше инфляции и ставок по депозитам."
    },
    {
        "name": "Солид - Российские облигации", "risk_level": "low",
        "annual_return_percent": 20.47, "volatility_percent": 11.02,
        "purchase_url": "https://finuslugi.ru/invest/funds/020db42a-9c02-43ed-bc45-36c8995652f4",
        "one_year_return_str": "+20,47%", "min_purchase_str": "От 1 ₽",
        "description": "Стратегия фонда заключается в активном управлении портфелем облигаций в зависимости от рыночной ситуации."
    },
    {
        "name": "ДОХОДЪ – Денежный рынок", "risk_level": "low",
        "annual_return_percent": 16.64, "volatility_percent": 1.11,
        "purchase_url": "https://finuslugi.ru/invest/funds/84b3eacc-b641-4b34-bf47-74caf12ef231",
        "one_year_return_str": "+16,64%", "min_purchase_str": "От 1 000 ₽",
        "description": "Фонд размещает активы в инструменты денежного рынка, обеспечивая минимальный риск и ликвидность."
    },
    {
        "name": "Альфа-Капитал – Валютные облигации", "risk_level": "low",
        "annual_return_percent": 13.49, "volatility_percent": 10.68,
        "purchase_url": "https://finuslugi.ru/invest/funds/c899d604-9123-4375-a304-ebc76eb87147",
        "one_year_return_str": "+13,49%", "min_purchase_str": "От 100 ₽",
        "description": "Фонд инвестирует в еврооблигации российских компаний, номинированные в долларах США. Подходит для защиты сбережений от валютных рисков."
    },
    # --- СРЕДНИЙ РИСК ---
    {
        "name": "ДОХОДЪ – Перспективные облигации", "risk_level": "medium",
        "annual_return_percent": 24.56, "volatility_percent": 20.31,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c27fa7a-7b39-421e-af16-6c61c557bfe2",
        "one_year_return_str": "+24,56%", "min_purchase_str": "От 1 000 ₽",
        "description": "Фонд инвестирует в облигации второго и третьего эшелонов с целью получения повышенной доходности."
    },
    {
        "name": "Солид – Пенсионный капитал", "risk_level": "medium",
        "annual_return_percent": 9.27, "volatility_percent": 16.79,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c568f93-5f58-4418-b3ef-4bf45d658539",
        "one_year_return_str": "+9,27%", "min_purchase_str": "От 1 ₽",
        "description": "Сбалансированная стратегия, сочетающая вложения в акции и облигации. Цель — обеспечить долгосрочный рост капитала."
    },
    # --- ВЫСОКИЙ РИСК ---
    {
        "name": "ДОХОДЪ – Золото", "risk_level": "high",
        "annual_return_percent": 26.16, "volatility_percent": 24.59,
        "purchase_url": "https://finuslugi.ru/invest/funds/e18b6907-a8d7-4d1e-9fa2-472dc6b9897d",
        "one_year_return_str": "+26,16%", "min_purchase_str": "От 1 000 ₽",
        "description": "Фонд инвестирует в золото через биржевые инструменты. Является защитным активом в периоды нестабильности."
    },
    {
        "name": "Альфа-Капитал - Великолепная семерка", "risk_level": "high",
        "annual_return_percent": 6.79, "volatility_percent": 25.43,
        "purchase_url": "https://finuslugi.ru/invest/funds/75d35014-d64a-419d-bfa7-e29d40b7907e",
        "one_year_return_str": "+6,79%", "min_purchase_str": "От 100 ₽",
        "description": "Фонд следует за динамикой акций 7 крупнейших американских технологических компаний."
    }
]

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
