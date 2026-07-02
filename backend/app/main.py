from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import pandas as pd
import pandas_ta as ta
import random
import os
import math
import pickle
import time
from datetime import datetime
import numpy as np
import asyncio
import xgboost as xgb
from sklearn.metrics import accuracy_score
from fastapi import BackgroundTasks


app = FastAPI(title="XGBCoin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "app/model/xgboost_crypto_classifier.pkl"
FEATURE_COLS_PATH = "app/model/feature_columns.pkl"

xgb_model = None
xgb_features = []

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURE_COLS_PATH):
        with open(MODEL_PATH, "rb") as f:
            xgb_model = pickle.load(f)
        with open(FEATURE_COLS_PATH, "rb") as f:
            xgb_features = pickle.load(f)
        print("XGBoost model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")



def add_all_features(df):
    import pandas_ta as ta
    import numpy as np
    import pandas as pd
    
    df["sma_10"] = ta.sma(df["close"], length=10)
    df["sma_50"] = ta.sma(df["close"], length=50)
    df["ema_10"] = ta.ema(df["close"], length=10)
    df["ema_50"] = ta.ema(df["close"], length=50)
    
    df["dist_sma_10"] = (df["close"] - df["sma_10"]) / df["sma_10"]
    df["dist_sma_50"] = (df["close"] - df["sma_50"]) / df["sma_50"]
    df["dist_ema_10"] = (df["close"] - df["ema_10"]) / df["ema_10"]
    df["dist_ema_50"] = (df["close"] - df["ema_50"]) / df["ema_50"]
    df["sma_10_50_ratio"] = df["sma_10"] / df["sma_50"]
    
    adx = ta.adx(df["high"], df["low"], df["close"], length=14)
    df["ADX_14"] = adx[adx.columns[0]] if adx is not None else 0
    df["RSI_14"] = ta.rsi(df["close"], length=14)
    
    stoch = ta.stoch(df["high"], df["low"], df["close"])
    if stoch is not None:
        df["Stoch_K"] = stoch[stoch.columns[0]]
        df["Stoch_D"] = stoch[stoch.columns[1]]
    else:
        df["Stoch_K"], df["Stoch_D"] = 50, 50
        
    df["CCI_14"] = ta.cci(df["high"], df["low"], df["close"], length=14)
    df["ROC_10"] = ta.roc(df["close"], length=10)
    df["WILLR_14"] = ta.willr(df["high"], df["low"], df["close"], length=14)
    
    macd = ta.macd(df["close"])
    df["MACD_HIST"] = macd[macd.columns[1]] if macd is not None else 0
    
    bb = ta.bbands(df["close"])
    if bb is not None:
        df["BB_PCT_B"] = bb[bb.columns[4]]
        df["BB_WIDTH"] = bb[bb.columns[3]]
    else:
        df["BB_PCT_B"], df["BB_WIDTH"] = 0.5, 0
        
    df["atr_ratio"] = ta.atr(df["high"], df["low"], df["close"]) / df["close"]
    
    df["return_1h"] = df["close"].pct_change(1)
    df["return_3h"] = df["close"].pct_change(3)
    df["return_6h"] = df["close"].pct_change(6)
    df["return_24h"] = df["close"].pct_change(24)
    
    df["volatility_6h"] = df["return_1h"].rolling(6).std()
    df["volatility_24h"] = df["return_1h"].rolling(24).std()
    
    df["volume_ratio_24h"] = df["volume"] / df["volume"].rolling(24).mean()
    df["CMF_20"] = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=20)

    hl_range = df["high"] - df["low"]
    hl_range = hl_range.replace(0, 1e-8)
    
    df["body_ratio"] = abs(df["close"] - df["open"]) / hl_range
    df["upper_shadow_ratio"] = (df["high"] - df[["close", "open"]].max(axis=1)) / hl_range
    df["lower_shadow_ratio"] = (df[["close", "open"]].min(axis=1) - df["low"]) / hl_range
    
    df["day_of_week"] = df["time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["time"].dt.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["time"].dt.hour / 24)
    
    df["volatility_ratio"] = df["volatility_6h"] / df["volatility_24h"]
    df["return_1h_lag1"] = df["return_1h"].shift(1)
    df["return_1h_lag2"] = df["return_1h"].shift(2)
    df["return_1h_lag3"] = df["return_1h"].shift(3)
    df["return_3h_lag1"] = df["return_3h"].shift(1)
    df["return_3h_lag2"] = df["return_3h"].shift(2)
    
    # --- 4H FEATURES ---
    df_4h = df.set_index("time").resample("4h").agg({
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }).dropna().reset_index()
    
    sma_20_4h = ta.sma(df_4h["close"], length=20)
    ema_20_4h = ta.ema(df_4h["close"], length=20)
    
    df_4h["dist_sma20_4H"] = (df_4h["close"] - sma_20_4h) / sma_20_4h
    df_4h["dist_ema20_4H"] = (df_4h["close"] - ema_20_4h) / ema_20_4h
    df_4h["RSI_14_4H"] = ta.rsi(df_4h["close"], length=14)
    
    atr_4h = ta.atr(df_4h["high"], df_4h["low"], df_4h["close"], length=14)
    df_4h["ATR_RATIO_4H"] = atr_4h / df_4h["close"]
    
    df_4h["return_4H"] = df_4h["close"].pct_change(1)
    df_4h["return_12H"] = df_4h["close"].pct_change(3)
    df_4h["return_24H_4H"] = df_4h["close"].pct_change(6)
    
    df_4h["volume_ratio_4H"] = df_4h["volume"] / df_4h["volume"].rolling(20).mean()
    
    features_4h = df_4h[["time", "dist_sma20_4H", "dist_ema20_4H", "RSI_14_4H", "ATR_RATIO_4H", "return_4H", "return_12H", "return_24H_4H", "volume_ratio_4H"]].sort_values("time")
    
    df = df.sort_values("time")
    df = pd.merge_asof(df, features_4h, on="time", direction="backward")
    
    return df

async def retrain_model_task():
    while True:
        now = datetime.now(timezone.utc)
        target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if target_time <= now:
            target_time += pd.Timedelta(days=1)
        sleep_seconds = (target_time - now).total_seconds()
        
        await asyncio.sleep(sleep_seconds)
        
        try:
            print("Starting automated retraining...")
            url = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1000"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                res = await client.get(url)
                data = res.json()
                
            df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base", "taker_quote", "ignore"])
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
                
            # Features
            df = add_all_features(df)
            
            df["next_close"] = df["close"].shift(-1)
            df["future_return"] = ((df["next_close"] - df["close"]) / df["close"]) * 100
            df["target"] = (df["future_return"] > 0.10).astype(int)
            
            df = df.dropna().reset_index(drop=True)
            
            X = df[xgb_features].copy()
            y = df["target"].copy()
            
            model = xgb.XGBClassifier(
                objective='binary:logistic',
                eval_metric='logloss',
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05
            )
            model.fit(X, y)
            
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(model, f)
                
            global xgb_model
            xgb_model = model
            print("Retraining completed and model updated in memory.")
        except Exception as e:
            print(f"Retraining failed: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(retrain_model_task())

pred_cache = {
    "hour": None,
    "naik": 50.0,
    "turun": 50.0
}

@app.get("/")
async def read_root():
    return {"message": "XGBCoin API is running"}

@app.get("/api/history")
async def get_history(interval: str = "1m"):
    valid_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    if interval not in valid_intervals:
        interval = "1m"
        
    url = f"https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval={interval}&limit=1000"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            res1 = await client.get(url)
            if res1.status_code != 200:
                return []
            data1 = res1.json()

            data2, data3 = [], []
            if len(data1) == 1000:
                first_time = data1[0][0]
                res2 = await client.get(f"{url}&endTime={first_time - 1}")
                if res2.status_code == 200:
                    data2 = res2.json()
                    
                    if len(data2) == 1000:
                        first_time2 = data2[0][0]
                        res3 = await client.get(f"{url}&endTime={first_time2 - 1}")
                        if res3.status_code == 200:
                            data3 = res3.json()
                            
            data = data3 + data2 + data1
        except Exception:
            return []
            
    if not data or not isinstance(data, list):
        return []
        
    formatted = []
    for row in data:
        formatted.append({
            "time": int(row[0] / 1000),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5])
        })
        
    df = pd.DataFrame(formatted)
    df = df.drop_duplicates(subset=["time"]).sort_values(by="time")
    
    df["sma"] = ta.sma(df["close"], length=20)
    df["ema"] = ta.ema(df["close"], length=20)
    df["rsi"] = ta.rsi(df["close"], length=14)
    
    macd = ta.macd(df["close"])
    if macd is not None and not macd.empty:
        df["macd"] = macd[macd.columns[0]]
        df["macd_histogram"] = macd[macd.columns[1]]
        df["macd_signal"] = macd[macd.columns[2]]
    else:
        df["macd"], df["macd_histogram"], df["macd_signal"] = None, None, None
        
    bbands = ta.bbands(df["close"], length=20)
    if bbands is not None and not bbands.empty:
        df["bb_lower"] = bbands[bbands.columns[0]]
        df["bb_middle"] = bbands[bbands.columns[1]]
        df["bb_upper"] = bbands[bbands.columns[2]]
    else:
        df["bb_lower"], df["bb_middle"], df["bb_upper"] = None, None, None

    df = df.where(pd.notnull(df), None)
    
    df = df.replace({np.nan: None})
    df = df.rename(columns={"volume": "value"})
    cols = ["time", "open", "high", "low", "close", "value", "sma", "ema", "rsi", "macd", "macd_histogram", "macd_signal", "bb_lower", "bb_middle", "bb_upper"]
    cols = [c for c in cols if c in df.columns]
    
    records = df[cols].to_dict('records')
    formatted_data = [{k: v for k, v in row.items() if v is not None} for row in records]
        
    return formatted_data

@app.get("/api/predict")
async def get_prediction():
    global pred_cache
    
    from datetime import timezone, timedelta
    current_time = datetime.now(timezone.utc)
    
    target_time = current_time.replace(minute=0, second=0, microsecond=0)
    target_timestamp = int(target_time.timestamp() * 1000)
    
    months = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    target_str = f"Waktu Prediksi Untuk {target_time.day} {months[target_time.month]} {target_time.year} Pukul {target_time.strftime('%H:00')} UTC"
    
    import time
    if pred_cache.get("cache_time", 0) > time.time() - 15:
        return pred_cache["response"]
        
    if xgb_model is None or not xgb_features:
        naik_prob = round(random.uniform(45.0, 55.0), 1)
        turun_prob = round(100.0 - naik_prob, 1)
        
        pred_cache = {"hour": current_hour, "naik": naik_prob, "turun": turun_prob, "history": []}
        return {
            "current": {
                "naik": naik_prob, 
                "turun": turun_prob, 
                "target_time": target_str, 
                "target_timestamp": target_timestamp
            },
            "history": []
        }

    url = "https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=500"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            res = await client.get(url)
            if res.status_code != 200:
                raise Exception("Failed to fetch klines")
            data = res.json()
        except Exception:
            return {
                "current": {
                    "naik": pred_cache.get("naik", 50.0), 
                    "turun": pred_cache.get("turun", 50.0), 
                    "target_time": target_str, 
                    "target_timestamp": target_timestamp
                },
                "history": pred_cache.get("history", [])
            }
            
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base", "taker_quote", "ignore"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
        
    df = add_all_features(df)
    
    df.fillna(0, inplace=True)

    df_closed = df.iloc[:-1]
    latest_incomplete_row = df.iloc[-1:]
    latest_closed_row = df_closed.iloc[-1:]

    history_data = []
    
    # Calculate history for the last 15 hours
    for i in range(15, 0, -1):
        if len(df_closed) < i + 1: continue
        row = df_closed.iloc[-(i+1):-i]
        
        X_hist = row[xgb_features]
        probs_hist = xgb_model.predict_proba(X_hist)[0]
        
        hist_turun_prob = round(float(probs_hist[0]) * 100, 1)
        hist_naik_prob = round(float(probs_hist[1]) * 100, 1)
        
        hist_target_timestamp = int((row["time"].iloc[0] + pd.Timedelta(hours=1)).timestamp() * 1000)
        
        next_row = df_closed.iloc[-i:] if i == 1 else df_closed.iloc[-i: -i+1]
        
        actual_close = float(next_row["close"].iloc[0])
        prev_close = float(row["close"].iloc[0])
        
        price_change_pct = (actual_close - prev_close) / prev_close * 100
        
        if price_change_pct > 0.1:
            actual_dir = "UPTREND"
        elif price_change_pct >= 0:
            actual_dir = "SIDEWAYS"
        else:
            actual_dir = "DOWNTREND"
            
        pred_dir = "UPTREND" if hist_naik_prob > 50 else "NOT_UPTREND"
        
        if pred_dir == "UPTREND" and actual_dir == "UPTREND":
            status = "VALID"
        elif pred_dir == "NOT_UPTREND" and actual_dir in ["DOWNTREND", "SIDEWAYS"]:
            status = "VALID"
        else:
            status = "INVALID"
                
        history_data.append({
            "naik": hist_naik_prob,
            "turun": hist_turun_prob,
            "target_timestamp": hist_target_timestamp,
            "status": status,
            "actual_dir": actual_dir,
            "start_price": prev_close,
            "end_price": actual_close,
            "volume": float(row["volume"].sum() if "volume" in row else 0),
            "volatility": float(row["volatility_24h"].iloc[-1] if "volatility_24h" in row else 0),
            "rsi": float(row["RSI_14"].iloc[-1] if "RSI_14" in row else 0),
            "adx": float(row["ADX_14"].iloc[-1] if "ADX_14" in row else 0),
            "macd": float(row["MACD_HIST"].iloc[-1] if "MACD_HIST" in row else 0),
            "trend": "BULLISH" if float(row["close"].iloc[-1]) > float(row["sma_50"].iloc[-1] if "sma_50" in row else 0) else "BEARISH"
        })
        
    history_data.reverse()

    X = latest_closed_row[xgb_features]
    probs = xgb_model.predict_proba(X)[0]

    turun_prob = round(float(probs[0]) * 100, 1)
    naik_prob = round(float(probs[1]) * 100, 1)

    response_data = {
        "current": {
            "naik": naik_prob, 
            "turun": turun_prob, 
            "target_time": target_str, 
            "target_timestamp": target_timestamp,
            "status": "PENDING",
            "start_price": float(latest_closed_row["close"].iloc[0]),
            "end_price": None,
            "volume": float(latest_incomplete_row["volume"].sum() if "volume" in latest_incomplete_row else 0),
            "volatility": float(latest_incomplete_row["volatility_24h"].iloc[-1] if "volatility_24h" in latest_incomplete_row else 0),
            "rsi": float(latest_incomplete_row["RSI_14"].iloc[-1] if "RSI_14" in latest_incomplete_row else 0),
            "adx": float(latest_incomplete_row["ADX_14"].iloc[-1] if "ADX_14" in latest_incomplete_row else 0),
            "macd": float(latest_incomplete_row["MACD_HIST"].iloc[-1] if "MACD_HIST" in latest_incomplete_row else 0),
            "trend": "BULLISH" if float(latest_incomplete_row["close"].iloc[-1]) > float(latest_incomplete_row["sma_50"].iloc[-1] if "sma_50" in latest_incomplete_row else 0) else "BEARISH"
        },
        "history": history_data
    }
    
    pred_cache = {
        "cache_time": time.time(),
        "response": response_data
    }
    
    return response_data
