from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="FastAPI + Ollama demo")

# FastAPI app → /ask endpoint → call Ollama → return answer.
class Query(BaseModel):
    question: str

def call_ollama(prompt: str, model: str = "llama3.2:1b") -> str:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "FastAPI is running 🚀"}

@app.post("/ask")
def ask(query: Query):
    answer = call_ollama(query.question)
    return {"question": query.question, "answer": answer}


