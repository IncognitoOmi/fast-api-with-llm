from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from fastapi.responses import StreamingResponse

app = FastAPI(title="FastAPI + Ollama demo")

# input schema for /chat
class ChatQuery(BaseModel):
    system: str
    user: str

def stream_ollama(prompt: str, model: str = "llama3.2:1b"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True 
    }
    resp = requests.post(url, json=payload, stream=True)
    for line in resp.iter_lines():
        if line:
            try:
                data = line.decode("utf-8")
                yield data + "\n"
            except Exception:
                continue

@app.get("/")
def root():
    return {"message": "FastAPI is running 🚀"}

@app.get("/stream")
def stream(prompt: str):
    return StreamingResponse(stream_ollama(prompt), media_type="text/plain")
