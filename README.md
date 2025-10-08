# 🤖 PortfolioBot: An Investment Sandbox for Beginners

**PortfolioBot** is a Telegram-based Mini App designed to be a "safe sandbox" for beginner investors. It helps users take their first step into the world of finance by removing key barriers—fear, complexity, and information overload. The project combines a user-friendly Telegram bot with an interactive web-based portfolio constructor.

---

### 🎯 The Problem

We are focused on the **"Beginning Enthusiast"** target audience (18-24 years old): students and recent graduates who have their first disposable income but find the world of investing intimidating.

Their key pain points include:
-   **Fear & Complexity:** Financial markets seem unpredictable and risky. The abundance of information (charts, hundreds of funds, complex terminology) is overwhelming rather than helpful.
-   **Distrust of "Black Boxes":** Users are wary of automated solutions where they don't understand the logic behind the recommendations. They want transparency.
-   **FOMO (Fear Of Missing Out):** There is a strong desire to be "in the know" and make their money work for them, but they are paralyzed by uncertainty about where to start.

---

### ✨ Our Solution & Unique Value Proposition (UVP)

Our product shifts the user's focus from analyzing the past to **modeling and preparing for the future**.

Instead of just another "auto-selection" tool, we provide a **portfolio constructor and simulator**. Our UVP is to empower users to:
1.  **Receive a clear, diversified portfolio template** based on their personal goals and risk profile.
2.  **Make an informed decision** by understanding the "why" behind each component of their portfolio.
3.  **Stress-test their strategy** by modeling its potential performance in thousands of future economic scenarios.

> We don't just tell users *what* to do; we give them the tools to understand *how* to act for themselves.

---

### 🚀 Key Features

-   **Goal-Oriented Onboarding:** The user journey starts by choosing a relatable goal, such as "Save for a Dream," "Grow Capital," or "Generate Passive Income."
-   **Automated Portfolio Templating:** Based on the user's goal and a simple risk assessment, the bot suggests a balanced, starter portfolio composed of real-world bonds and funds.
-   **Visual Risk Management:** An intuitive slider allows the user to instantly adjust their risk level, with the portfolio composition and forecast adapting in real-time.
-   **Probabilistic Future Modeling:** Our core feature, powered by a Monte Carlo simulation on the backend, shows users a probable range of outcomes (optimistic, pessimistic, and average) for their chosen strategy.
-   **Interactive Portfolio Editor:** Users are not locked into the initial suggestion. They can modify the portfolio's risk, term, and even replace specific assets with alternatives from the same risk category.
-   **Social Proof & Comparison:** The ability to view anonymized, similar portfolios from other users helps socially validate a user's strategy and builds confidence.
-   **Full Transparency:** We provide clear descriptions for each financial instrument and explain the logic behind the portfolio's construction.

---

### 🛠️ Tech Stack & Architecture

The project is a hybrid system consisting of a Telegram bot, a web application (Mini App), and an analytics dashboard.

-   **Backend:**
    -   **Telegram Bot:** `Python` with the `pyTelegramBotAPI` library (`main.py`) to handle user commands and send portfolio summaries.
    -   **API & Web Server:** `Python` with `Flask` (`api_server.py`) to serve the frontend Mini App and provide API endpoints (`/api/calculate`, `/api/funds`).
    -   **Calculation Engine:** `NumPy` for performing Monte Carlo simulations to generate portfolio forecasts (`calculator.py`).

-   **Frontend (Telegram Mini App):**
    -   `HTML`, `CSS`, and modern `JavaScript (ESM)`.
    -   `Chart.js` for interactive data visualization.
    -   Communicates with the backend via REST API calls.

-   **Database:**
    -   `SQLite` for storing user registration data (`portfolio_bot.db`).
    -   `Firebase Firestore` for event-based product analytics.

-   **Analytics:**
    -   `Python` with `Streamlit`, `Pandas`, and `Plotly` for a standalone analytics dashboard (`analyzer.py`) that visualizes user behavior and funnel metrics.

---

### 🌊 How It Works: User Flow

1. A user starts the bot in Telegram and receives a welcome message with a button to open the Mini App.
2. Inside the Mini App, the user chooses a financial goal (e.g., "Save for a Dream").
3. They answer a few simple questions: investment amount, term, and risk tolerance.
4. The backend calculates and returns a recommended starter portfolio with a visual forecast.
5. The user can then enter the **editor** to adjust the risk level, term, monthly contributions, or even swap out individual funds. The forecast chart updates with every change.
6. Once satisfied, the user confirms the portfolio. The bot sends a summary message directly to their chat.
7. A final screen provides direct links and instructions on how to purchase the selected assets.

---

> ### Disclaimer
>
> All information provided by the bot, including scenario modeling and portfolio compositions, is for informational and educational purposes only. It does **not** constitute an individual investment recommendation (IIR). Users should conduct their own research or consult with a qualified financial advisor before making any investment decisions.
