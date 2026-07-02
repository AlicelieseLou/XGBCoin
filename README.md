<div align="center">

<img src="frontend/public/logo.png" alt="XGBCoin Logo" width="120">

# XGBCoin

### Real-Time Bitcoin Price Direction Prediction using XGBoost

A web-based machine learning application for predicting the direction of Bitcoin price movement using real-time market data, technical indicators, and the XGBoost classification algorithm.

<!-- Replace with your deployed URL -->
**🌐 Live Demo:** https://xgbcoin-live.web.app

<br>

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Machine%20Learning-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Hosting-FFCA28?logo=firebase&logoColor=black)

</div>

---

# 📖 Overview

**XGBCoin** is a web-based application developed to predict the **direction of Bitcoin price movement** for the next one-hour period using the **XGBoost machine learning algorithm**.

The application automatically retrieves market data from **Coinbase API**, calculates **30 technical indicators**, and generates probabilistic predictions indicating whether Bitcoin is more likely to move upward or downward.

Besides prediction, XGBCoin provides an interactive dashboard and technical indicators in real time.

---

# ✨ Features

- 🧠 **XGBoost Prediction Model**
  - Predicts Bitcoin price direction using a trained XGBoost classifier.

- 📊 **30 Technical Indicators**
  - Automatically calculates technical indicators used as model features.

- ⚡ **Real-Time Market Data**
  - Retrieves live Bitcoin market data from Coinbase API.

- 📈 **Interactive Candlestick Chart**
  - Built with TradingView Lightweight Charts.

- 📉 **Probability-Based Prediction**
  - Displays Bullish and Bearish probabilities instead of deterministic predictions.

- 🔄 **Automatic Prediction Update**
  - Refreshes predictions whenever new market data becomes available.

- 💾 **Persistent User Preferences**
  - Saves chart settings locally using browser storage.

- 📱 **Responsive Interface**
  - Optimized for desktop and mobile devices.

---

# ⚙️ System Architecture

```
Coinbase API
      │
      ▼
 Historical Market Data
      │
      ▼
Technical Indicators (30 Features)
      │
      ▼
Trained XGBoost Model
      │
      ▼
Prediction API (FastAPI)
      │
      ▼
Interactive Web Dashboard
```

---

# 📊 Prediction Workflow

1. Retrieve historical Bitcoin market data from Coinbase API.
2. Calculate 30 technical indicators.
3. Prepare feature vectors.
4. Perform inference using the trained XGBoost model.
5. Generate prediction probabilities.
6. Display results on the web dashboard.

---

# 🛠 Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | Python, FastAPI, Uvicorn |
| Machine Learning | XGBoost, Pandas, NumPy, Joblib |
| Frontend | HTML5, CSS3, JavaScript (ES6), Bootstrap 5 |
| Charts | TradingView Lightweight Charts |
| Data Source | Coinbase API |
| Deployment | Firebase Hosting |

---

# 📂 Project Structure

```text
xgbcoin/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── model/
│   │
│   ├── run.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── public/
│   ├── 404.html
│   └── index.html
│
├── notebook/
│   └── XGBoost_v3_0_Mod.ipynb
│
├── firebase.json
└── README.md
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/AlicelieseLou/XGBCoin.git
cd xgbcoin
```

---

## Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```

---

## Frontend

```bash
cd frontend

python -m http.server 5500
```

Open:

```
http://127.0.0.1:5500
```

---

# 📈 Model Information

| Item | Description |
|------|-------------|
| Algorithm | XGBoost Classifier |
| Target | Bitcoin Price Direction |
| Prediction Horizon | Next 1 Hour |
| Data Source | Coinbase API |
| Features | 30 Technical Indicators |

---

# 🔮 Future Improvements

- Support additional cryptocurrencies
- Model retraining pipeline
- Hyperparameter optimization
- Historical prediction backtesting
- Prediction confidence visualization
- Multi-timeframe forecasting

---

<div align="center">

Made with ❤️ using

**Python • FastAPI • XGBoost • Bootstrap • Firebase**

</div>
