import requests

# Telegram bot token aur chat_id
BOT_TOKEN = ""
CHAT_ID = ""

# test message
message = "🔥 Test alert from RSI Bot!"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": message}

resp = requests.post(url, data=payload)

print(resp.json())
