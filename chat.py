from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="FastAPI + Ollama demo")

# input schema for /chat
class ChatQuery(BaseModel):
    system: str
    user: str

def call_ollama_chat(system: str, user: str, model: str = "llama3.2:1b") -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "FastAPI is running 🚀"}

@app.post("/chat")
def chat(query: ChatQuery):
    response = call_ollama_chat(query.system, query.user)
    return {"system": query.system, "user": query.user, "response": response}
