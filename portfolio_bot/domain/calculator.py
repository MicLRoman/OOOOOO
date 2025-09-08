import random

class PortfolioCalculator:
    def __init__(self, repository):
        self.repository = repository

    # --- ИЗМЕНЕНИЕ: Метод теперь принимает опциональный список фондов ---
    def calculate(self, risk_profile: str, amount: int, term: int, selected_funds: list[str] = None) -> dict:
        """
        Главный метод. Если передан `selected_funds`, использует их. Иначе - подбирает лучшие.
        """
        print(f"\n--- 🚀 [КАЛЬКУЛЯТОР] Расчет: Риск='{risk_profile}', Сумма={amount}, Срок={term} ---")

        strategy_template = self.repository.get_strategy_template(risk_profile)
        all_funds = self.repository.get_all_funds()

        if not strategy_template:
            return {"error": f"Стратегия '{risk_profile}' не найдена."}

        # --- НОВАЯ ЛОГИКА: Выбираем, как формировать портфель ---
        portfolio_composition_funds = []
        if selected_funds:
            print("[ШАГ 1] Используются переданные фонды для перерасчета.")
            fund_map = {f['name']: f for f in all_funds}
            for fund_name in selected_funds:
                if fund_name in fund_map:
                    portfolio_composition_funds.append(fund_map[fund_name])
        else:
            print("[ШАГ 1] Подбираются оптимальные фонды по стратегии.")
            portfolio_composition_funds = self._assemble_portfolio(strategy_template, all_funds)

        if not portfolio_composition_funds:
             return {"error": "Не удалось собрать портфель из указанных фондов."}

        total_return, total_volatility = self._calculate_portfolio_metrics(portfolio_composition_funds, strategy_template)
        print(f"[ШАГ 2] Ожидаемая доходность: {total_return:.2f}%, Волатильность: {total_volatility:.2f}%")

        forecast = self._generate_forecast(amount, term, total_return, total_volatility)
        print("[ШАГ 3] Сгенерирован прогноз для графика.")

        # Собираем итоговый состав портфеля с долями из шаблона
        composition_details = []
        shares = list(strategy_template['composition'].values())
        for i, fund in enumerate(portfolio_composition_funds):
            composition_details.append({"fund_name": fund['name'], "percentage": shares[i]})

        print("--- ✅ [КАЛЬКУЛЯТОР] Расчет завершен. ---\n")
        
        return {
            "initial_amount": amount,
            "term": term,
            "riskProfile": risk_profile, # Добавляем риск-профиль для фронтенда
            "strategy_name": strategy_template['name'],
            "expected_annual_return": round(total_return, 2),
            "composition": composition_details,
            "forecast": forecast
        }

    def _assemble_portfolio(self, strategy_template, all_funds):
        portfolio = []
        for risk_level, _ in strategy_template['composition'].items():
            candidates = [f for f in all_funds if f['risk_level'] == risk_level]
            if candidates:
                candidates.sort(key=lambda x: x['annual_return_percent'], reverse=True)
                portfolio.append(candidates[0])
        return portfolio

    def _calculate_portfolio_metrics(self, portfolio_composition, strategy_template):
        total_return = 0
        total_volatility = 0
        shares = list(strategy_template['composition'].values())
        
        # Убедимся, что количество фондов и долей совпадает
        num_items = min(len(portfolio_composition), len(shares))

        for i in range(num_items):
            fund = portfolio_composition[i]
            share_fraction = shares[i] / 100.0
            total_return += fund['annual_return_percent'] * share_fraction
            total_volatility += fund['volatility_percent'] * share_fraction
            
        return total_return, total_volatility

    def _generate_forecast(self, amount, term, total_return, total_volatility):
        labels = list(range(term + 1))
        avg_data, min_data, max_data = [], [], []
        avg_rate = 1 + (total_return / 100.0)
        min_rate = 1 + ((total_return - total_volatility * 0.5) / 100.0)
        max_rate = 1 + ((total_return + total_volatility * 0.5) / 100.0)

        for year in labels:
            # Округляем значения для чистоты данных
            avg_data.append(round(amount * (avg_rate ** year), 2))
            min_data.append(round(amount * (min_rate ** year), 2))
            max_data.append(round(amount * (max_rate ** year), 2))

        return {"labels": labels, "avg": avg_data, "min": min_data, "max": max_data}

