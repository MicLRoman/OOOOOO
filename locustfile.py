from locustfile import HttpUser, task, between

class PortfolioUser(HttpUser):
    wait_time = between(1, 5) # Пауза между запросами от 1 до 5 сек

    # Это самый тяжелый запрос, его и будем тестировать
    @task
    def calculate_portfolio(self):
        self.client.post("/api/calculate", json={
            "riskProfile": "aggressive",
            "amount": 100000,
            "term_months": 36,
            "monthlyContribution": 10000,
            "goal": "grow"
        })