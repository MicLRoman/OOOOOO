# -*- coding: utf-8 -*-

# Данные по облигациям, скопированные из вашего файла
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

# Данные по фондам акций, скопированные из вашего файла
EQUITY_FUNDS = [
    # --- Низкий риск ---
    {
        "name": "Альфа-Капитал Облигации Плюс", "risk_level": "low",
        "annual_return_percent": 28.79, "volatility_percent": 12,
        "purchase_url": "https://finuslugi.ru/invest/funds/5f6d1ba3-2049-49be-b755-000c901d1f28"
    },
    {
        "name": "ТРИНФИКО – Российские доходные облигации", "risk_level": "low",
        "annual_return_percent": 23.45, "volatility_percent": 14,
        "purchase_url": "https://finuslugi.ru/invest/funds/1b535701-8dc2-439a-afd5-4c82eb141ec1"
    },
    {
        "name": "Солид - Российские облигации", "risk_level": "low",
        "annual_return_percent": 20.20, "volatility_percent": 12,
        "purchase_url": "https://finuslugi.ru/invest/funds/020db42a-9c02-43ed-bc45-36c8995652f4"
    },
    {
        "name": "Альфа-Капитал – Валютные облигации", "risk_level": "low",
        "annual_return_percent": 15.60, "volatility_percent": 10,
        "purchase_url": "https://finuslugi.ru/invest/funds/c899d604-9123-4375-a304-ebc76eb87147"
    },

    # --- Средний риск ---
    {
        "name": "ДОХОДЪ – Перспективные облигации", "risk_level": "medium",
        "annual_return_percent": 26.08, "volatility_percent": 28,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c27fa7a-7b39-421e-af16-6c61c557bfe2"
    },
    {
        "name": "ГЕРОИ – Валютные возможности", "risk_level": "medium",
        "annual_return_percent": 19.89, "volatility_percent": 22,
        "purchase_url": "https://finuslugi.ru/invest/funds/d3e7b311-c1d7-456c-bb44-e2da0e3d92ca"
    },
    {
        "name": "Альфа-Капитал Баланс", "risk_level": "medium",
        "annual_return_percent": 19.70, "volatility_percent": 20,
        "purchase_url": "https://finuslugi.ru/invest/funds/9cd098a8-65e5-4f5e-b953-20def00ff9c9"
    },
    {
        "name": "Солид – Пенсионный капитал", "risk_level": "medium",
        "annual_return_percent": 15.69, "volatility_percent": 18,
        "purchase_url": "https://finuslugi.ru/invest/funds/0c568f93-5f58-4418-b3ef-4bf45d658539"
    },
    {
        "name": "Солид - Индекс МосБиржи", "risk_level": "medium",
        "annual_return_percent": 13.04, "volatility_percent": 15,
        "purchase_url": "https://finuslugi.ru/invest/funds/d459be9f-4c7c-436c-a510-06a4bfb3fbe9"
    },

    # --- Высокий риск ---
    {
        "name": "Альфа-Капитал – Высокодоходные облигации", "risk_level": "high",
        "annual_return_percent": 32.39, "volatility_percent": 40,
        "purchase_url": "https://finuslugi.ru/invest/funds/502dda6c-7d7b-45ca-9936-05fbe50ff54a"
    },
    {
        "name": "Альфа-Капитал – Ликвидные акции", "risk_level": "high",
        "annual_return_percent": 17.71, "volatility_percent": 28,
        "purchase_url": "https://finuslugi.ru/invest/funds/4e0e6b16-15b2-4188-9438-844c62be048c"
    },
    {
        "name": "ДОХОДЪ – Дивидендные акции", "risk_level": "high",
        "annual_return_percent": 14.18, "volatility_percent": 25,
        "purchase_url": "https://finuslugi.ru/invest/funds/03417e3a-8f2d-482a-9984-d52fd3d6cef4"
    },
    {
        "name": "Альфа-Капитал Акции компаний роста", "risk_level": "high",
        "annual_return_percent": 11.13, "volatility_percent": 22,
        "purchase_url": "https://finuslugi.ru/invest/funds/78f3621f-08bd-4e55-9463-445f17bdd5dd"
    },
]

def format_and_print_assets():
    """
    Функция для форматирования и вывода информации об активах.
    """
    print("--- Облигации ---")
    for bond in BONDS:
        # Форматируем строку в виде: тип - название - ссылка
        print(f"облигация - {bond['name']} - {bond['purchase_url']}")

    print("\n--- Фонды акций ---")
    for fund in EQUITY_FUNDS:
        # Форматируем строку в виде: тип - название - ссылка
        print(f"фонд - {fund['name']} - {fund['purchase_url']}")

# Запускаем функцию при выполнении скрипта
if __name__ == "__main__":
    format_and_print_assets()
