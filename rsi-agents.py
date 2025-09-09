import requests
import pandas as pd
import numpy as np
import time

# ===== CONFIG =====
BOT_TOKEN = "7699036883:AAEh1PxEVSoqaYyto0E1yByjgxC4q5mLeJw"
CHAT_ID = "1155443179"


# =============== BASE AGENT CLASS ===============
class BaseAgent:
    def run(self, *args, **kwargs):
        raise NotImplementedError


# =============== Data Fetch Agent ===============
class DataAgent(BaseAgent):
    def __init__(self, symbol="BTCUSDT", interval="5m", limit=100):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

    def run(self):
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": self.symbol, "interval": self.interval, "limit": self.limit}
        resp = requests.get(url, params=params)
        data = resp.json()

        df = pd.DataFrame(data, columns=[
            "timestamp","open","high","low","close","volume",
            "close_time","quote_asset_volume","num_trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df[["timestamp", "close"]]


# =============== RSI Calculation Agent ===============
class RSIAgent(BaseAgent):
    def __init__(self, window=14):
        self.window = window

    def run(self, df: pd.DataFrame):
        delta = df['close'].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=self.window, min_periods=self.window).mean()
        avg_loss = pd.Series(loss).rolling(window=self.window, min_periods=self.window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['rsi'] = rsi
        return df


# =============== Alert Agent ===============
class AlertAgent(BaseAgent):
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, message: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}
        requests.post(url, json=payload)

    def run(self, df: pd.DataFrame, symbol="BTCUSDT"):
        latest = df.iloc[-1]
        rsi = latest["rsi"]
        price = latest["close"]

        if pd.notna(rsi):
            if rsi <= 20:
                self.send_message(f"🚨 {symbol} RSI={rsi:.2f} (OVERSOLD)\nPrice={price}")
            elif rsi >= 80:
                self.send_message(f"🚨 {symbol} RSI={rsi:.2f} (OVERBOUGHT)\nPrice={price}")
            else:
                print(f"No alert for {symbol}: RSI={rsi:.2f}, Price={price}")


# =============== Orchestrator Agent ===============
class OrchestratorAgent(BaseAgent):
    def __init__(self, symbols=["BTCUSDT", "ETHUSDT"]):
        self.symbols = symbols
        self.data_agent = DataAgent()
        self.rsi_agent = RSIAgent()
        self.alert_agent = AlertAgent(BOT_TOKEN, CHAT_ID)

    def run(self):
        for symbol in self.symbols:
            self.data_agent.symbol = symbol
            df = self.data_agent.run()
            df = self.rsi_agent.run(df)
            self.alert_agent.run(df, symbol=symbol)


# =============== MAIN LOOP ===============
if __name__ == "__main__":
    orchestrator = OrchestratorAgent(symbols=["BTCUSDT", "ETHUSDT"])
    while True:
        orchestrator.run()
        time.sleep(300)  # every 5 minutes
