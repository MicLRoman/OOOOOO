import numpy as np
import math

PASSIVE_INCOME_RATE_PERCENT = 18.0
NUM_SIMULATIONS = 10000
DEPOSIT_ANNUAL_RATE_PERCENT = 15.3

class PortfolioCalculator:
    def __init__(self, repository):
        self.repository = repository

    def calculate(self, risk_profile: str, amount: int, term: int = None,
                  selected_funds: list = None, dreamAmount: int = None, passiveIncome: int = None, term_months: int = None,
                  monthly_contribution: int = 0) -> dict: 

        if term_months:
            num_months = int(term_months)
            term = round(num_months / 12, 1)
        else:
            num_months = (term or 1) * 12

        print(f"\n--- 🚀 [КАЛЬКУЛЯТОР] Начат новый расчет... ---")
        print(f"Входные данные: Риск='{risk_profile}', Сумма={amount}, Срок={num_months} мес., Пополнение={monthly_contribution}, Цель(сумма)={dreamAmount}, Цель(доход)={passiveIncome}")

        if risk_profile == 'conservative' and num_months <= 12:
            print("\n--- 🛡️ [КАЛЬКУЛЯТОР] Активирован режим защиты капитала для краткосрочного консервативного портфеля... ---")
            strategy_template = self.repository.get_strategy_template('no-loss')
            all_funds = self.repository.get_all_funds()
            if not strategy_template:
                strategy_template = self.repository.get_strategy_template('conservative')
            
            strategy_template['composition'] = self._find_no_loss_composition(
                initial_composition=strategy_template['composition'].copy(),
                all_funds=all_funds,
                amount=amount,
                num_months=num_months,
                monthly_contribution=monthly_contribution
            )
            strategy_template['name'] = "Консервативная (с защитой капитала)"
            print(f"--- Итоговая безопасная композиция: {strategy_template['composition']} ---\n")
        
        else:
            strategy_template = self.repository.get_strategy_template(risk_profile)
            all_funds = self.repository.get_all_funds()

        if not strategy_template:
            return {"error": f"Стратегия '{risk_profile}' не найдена."}

        portfolio_composition = self._assemble_portfolio(strategy_template, all_funds, selected_funds)
        total_return, total_volatility = self._calculate_portfolio_metrics(portfolio_composition, strategy_template)
        
        forecast = self._generate_forecast_monte_carlo(amount, num_months, total_return, total_volatility, monthly_contribution, risk_profile)
        
        forecast_without_contribution = None
        if monthly_contribution > 0:
            print("--- 📊 [КАЛЬКУЛЯТОР] Расчет дополнительного прогноза без пополнений... ---")
            forecast_without_contribution = self._generate_forecast_monte_carlo(amount, num_months, total_return, total_volatility, 0, risk_profile)

        deposit_forecast = self._generate_deposit_forecast(amount, num_months, monthly_contribution)

        target_capital = None
        if passiveIncome:
            annual_income = passiveIncome * 12
            target_capital = annual_income / (PASSIVE_INCOME_RATE_PERCENT / 100.0) if PASSIVE_INCOME_RATE_PERCENT > 0 else 0

        monthly_income_forecast = self._generate_monthly_income_forecast(forecast['avg'])
        final_composition_details = self._get_final_composition_details(portfolio_composition, strategy_template)

        result = {
            "initial_amount": amount,
            "monthly_contribution": monthly_contribution,
            "term": term,
            "term_months": num_months,
            "strategy_name": strategy_template['name'],
            "riskProfile": risk_profile,
            "expected_annual_return": f"{total_return:.1f}",
            "composition": final_composition_details,
            "forecast": forecast,
            "forecast_without_contribution": forecast_without_contribution,
            "deposit_forecast": deposit_forecast,
            "goal_dream_amount": dreamAmount,
            "goal_target_capital": target_capital,
            "monthly_income_forecast": monthly_income_forecast,
            "passiveIncome": passiveIncome
        }
        print("--- ✅ [КАЛЬКУЛЯТОР] Расчет завершен. ---\n")
        return result

    def _find_no_loss_composition(self, initial_composition: dict, all_funds: list, amount: int, num_months: int, monthly_contribution: int = 0) -> dict:
        current_composition = initial_composition
        
        for i in range(10): 
            temp_strategy = {"composition": current_composition}
            portfolio_funds = self._assemble_portfolio(temp_strategy, all_funds)
            total_return, total_volatility = self._calculate_portfolio_metrics(portfolio_funds, temp_strategy)
            
            # --- ИЗМЕНЕНИЕ: Указываем риск-профиль "no-loss" для расчета перцентилей ---
            forecast = self._generate_forecast_monte_carlo(amount, num_months, total_return, total_volatility, monthly_contribution, 'no-loss')
            min_final_amount = forecast['min'][-1]
            total_invested = amount + (monthly_contribution * num_months)

            print(f"Итерация {i+1}: Доля облигаций {current_composition.get('bonds', 0):.1f}%. Мин. прогноз: {min_final_amount:,.0f} ₽ (Цель: >= {total_invested:,.0f} ₽)")

            if min_final_amount >= total_invested:
                print("--- ✅ Условие безубыточности достигнуто. ---")
                return current_composition
            
            bonds_share = current_composition.get('bonds', 0)
            if bonds_share >= 95:
                print("--- ⚠️ Достигнут лимит облигаций (95%). Возвращаем самую безопасную из возможных композиций. ---")
                return current_composition

            increase_by = 5.0
            risky_assets = {k: v for k, v in current_composition.items() if k != 'bonds'}
            total_risky_share = sum(risky_assets.values())

            if total_risky_share <= increase_by:
                 final_composition = {'bonds': 100}
                 for key in risky_assets: final_composition[key] = 0
                 return final_composition

            for key, value in risky_assets.items():
                reduction = (value / total_risky_share) * increase_by
                current_composition[key] -= reduction
            
            current_composition['bonds'] = bonds_share + increase_by
            
            total_sum = sum(current_composition.values())
            for key in current_composition:
                current_composition[key] = (current_composition[key] / total_sum) * 100

        print("--- ⚠️ Не удалось достичь безубыточности за 10 итераций. Возвращается последняя рассчитанная композиция. ---")
        return current_composition

    def _assemble_portfolio(self, strategy_template, all_funds, selected_funds=None):
        portfolio = []
        if selected_funds:
            for fund_name in selected_funds:
                found = next((f for f in all_funds if f['name'] == fund_name), None)
                if found: portfolio.append(found)
            return portfolio
        else:
            used_funds = set()
            for risk_level, _ in strategy_template['composition'].items():
                candidates = [f for f in all_funds if f.get('risk_level') == risk_level and f['name'] not in used_funds]
                if candidates:
                    candidates.sort(key=lambda x: x['annual_return_percent'], reverse=True)
                    best_fund = candidates[0]
                    portfolio.append(best_fund)
                    used_funds.add(best_fund['name'])
            return portfolio

    def _calculate_portfolio_metrics(self, portfolio_composition, strategy_template):
        total_return = 0
        total_volatility = 0
        risk_to_fund_map = {fund.get('risk_level'): fund for fund in portfolio_composition}

        for risk_level, percentage in strategy_template['composition'].items():
            fund_for_level = risk_to_fund_map.get(risk_level)
            if fund_for_level:
                share_fraction = percentage / 100.0
                total_return += fund_for_level['annual_return_percent'] * share_fraction
                total_volatility += fund_for_level['volatility_percent'] * share_fraction
        
        return total_return, total_volatility

    def _get_final_composition_details(self, portfolio_composition, strategy_template):
        final_composition = []
        risk_to_fund_map = {fund.get('risk_level'): fund for fund in portfolio_composition}

        for risk_level, percentage in strategy_template['composition'].items():
            fund = risk_to_fund_map.get(risk_level)
            if fund:
                final_composition.append({
                    "fund_name": fund['name'],
                    "percentage": percentage,
                    "risk_level": risk_level,
                    "purchase_url": fund.get('purchase_url')
                })
        return final_composition
    
    def _generate_deposit_forecast(self, amount, num_months, monthly_contribution=0):
        """Calculates the growth of a deposit with monthly capitalization."""
        monthly_rate = (DEPOSIT_ANNUAL_RATE_PERCENT / 100) / 12
        capital_over_time = [float(amount)]

        current_capital = float(amount)
        for _ in range(num_months):
            # Add contribution at the beginning of the month
            current_capital += monthly_contribution
            # Calculate interest on the new capital
            interest = current_capital * monthly_rate
            current_capital += interest
            capital_over_time.append(current_capital)
        
        # The first value is at month 0, so we need num_months + 1 total values.
        # The loop runs num_months times, adding one value each time.
        # Initial amount is already there. So the length is correct.
        # Let's adjust to match the length of forecast labels.
        if len(capital_over_time) == num_months + 1:
             return capital_over_time
        # In case of any mismatch, let's build it safely.
        final_capital = [float(amount)]
        c = float(amount)
        for i in range(1, num_months + 1):
            c += monthly_contribution
            c *= (1 + monthly_rate)
            final_capital.append(c)
        return final_capital

    def _generate_forecast_monte_carlo(self, amount, num_months, annual_return, annual_volatility, monthly_contribution=0, risk_profile='moderate'):
        monthly_return = (1 + annual_return / 100)**(1/12) - 1
        monthly_volatility = annual_volatility / math.sqrt(12) / 100

        simulations_matrix = np.zeros((num_months + 1, NUM_SIMULATIONS))
        simulations_matrix[0] = amount
        
        # Исправленный цикл симуляции
        for t in range(1, num_months + 1):
            # Пополнение происходит в начале каждого месяца
            current_capital = simulations_matrix[t-1] + monthly_contribution
            
            # Затем начисляются проценты за месяц
            random_shocks = np.random.normal(0, 1, NUM_SIMULATIONS)
            monthly_returns = monthly_return + random_shocks * monthly_volatility
            simulations_matrix[t] = current_capital * (1 + monthly_returns)

        # Отдельно обрабатываем случай без пополнений, чтобы избежать двойного сложения
        if monthly_contribution == 0:
            simulations_matrix = np.zeros((num_months + 1, NUM_SIMULATIONS))
            simulations_matrix[0] = amount
            for t in range(1, num_months + 1):
                random_shocks = np.random.normal(0, 1, NUM_SIMULATIONS)
                monthly_returns = monthly_return + random_shocks * monthly_volatility
                simulations_matrix[t] = simulations_matrix[t-1] * (1 + monthly_returns)


        labels = list(range(num_months + 1))
        
        if risk_profile in ['moderate', 'moderate-conservative', 'moderate-aggressive']:
            min_percentile = 15
            max_percentile = 85
        else:
            min_percentile = 5
            max_percentile = 95
            
        min_data = np.percentile(simulations_matrix, min_percentile, axis=1).tolist()
        # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Используем среднее арифметическое вместо медианы ---
        avg_data = np.mean(simulations_matrix, axis=1).tolist()
        # avg_data = np.percentile(simulations_matrix, 50, axis=1).tolist()
        max_data = np.percentile(simulations_matrix, max_percentile, axis=1).tolist()

        return {"labels": labels, "avg": avg_data, "min": min_data, "max": max_data}


    def _generate_monthly_income_forecast(self, capital_forecast: list):
        rate = PASSIVE_INCOME_RATE_PERCENT / 100.0
        return [ (capital * rate) / 12 for capital in capital_forecast ]

