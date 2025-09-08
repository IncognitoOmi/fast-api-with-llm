# multi_agent.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from typing import Optional

OLLAMA_BASE = "http://localhost:11434"
MODEL = "llama3.2:1b"

app = FastAPI(title="FastAPI + Ollama Multi-Agent Demo")

# --------- Schemas ----------
class Query(BaseModel):
    question: str


class SummarizeRequest(BaseModel):
    text: str
    max_sentences: Optional[int] = 2


class MultiAgentRequest(BaseModel):
    question: str
    prefer_short_summary: Optional[bool] = True


# --------- Low-level wrappers ----------
def call_ollama_generate(prompt: str, model: str = MODEL, stream: bool = False) -> str:
    url = f"{OLLAMA_BASE}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": stream}
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # non-stream JSON has "response"
        return data.get("response", "")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama generate error: {e}")


def call_ollama_chat(messages: list, model: str = MODEL, stream: bool = False) -> str:
    url = f"{OLLAMA_BASE}/api/chat"
    payload = {"model": model, "messages": messages, "stream": stream}
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # chat returns object with "message": {"content": "..."}
        return data.get("message", {}).get("content", "")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama chat error: {e}")


# --------- Agents ----------
def research_agent(question: str) -> str:
    """
    ResearchAgent: provide a detailed multi-paragraph answer, include sources suggestion and next steps.
    """
    prompt = (
        "You are ResearchAgent, an expert on technical topics. Give a detailed, thorough answer to the question. "
        "If applicable, include short bullet points for 'Key points' and 'Next steps'.\n\n"
        f"QUESTION: {question}\n\nAnswer:"
    )
    return call_ollama_generate(prompt)


def summarizer_agent(text: str, max_sentences: int = 2) -> str:
    """
    SummarizerAgent: take long text and return concise summary in max_sentences.
    """
    prompt = (
        "You are SummarizerAgent. Produce a concise summary of the input text.\n"
        f"Limit the summary to {max_sentences} sentences. Use simple language.\n\n"
        f"TEXT:\n{text}\n\nSUMMARY:"
    )
    return call_ollama_generate(prompt)


# --------- Endpoints ----------
@app.get("/")
def health():
    return {"status": "ok", "note": "Multi-agent demo running"}


@app.post("/research")
def research(query: Query):
    """Single ResearchAgent call"""
    detailed = research_agent(query.question)
    return {"question": query.question, "detailed_answer": detailed}


@app.post("/summarize")
def summarize(req: SummarizeRequest):
    """Single SummarizerAgent call"""
    summary = summarizer_agent(req.text, max_sentences=req.max_sentences)
    return {"summary": summary}


@app.post("/multi-agent")
def multi_agent(req: MultiAgentRequest):
    """
    Orchestrator:
    1) Run ResearchAgent on the question (detailed answer)
    2) Run SummarizerAgent on the detailed answer (short summary)
    3) Return both
    """
    # 1) Research
    detailed = research_agent(req.question)

    # 2) Decide summary length
    max_sentences = 1 if req.prefer_short_summary else 3

    # 3) Summarize the detailed answer
    summary = summarizer_agent(detailed, max_sentences=max_sentences)

    return {
        "question": req.question,
        "detailed_answer": detailed,
        "summary": summary
    }
