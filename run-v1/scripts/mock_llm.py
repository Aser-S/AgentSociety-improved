"""Tiny OpenAI-compatible stand-in LLM for smoke-testing AgentSociety v1 without an API key.
Replies are canned; it only proves the pipeline runs end to end. Logs prompts to mock_llm.log."""
import json, random, time
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

def answer(prompt: str) -> str:
    p = prompt.lower()
    if "json" in p:
        return json.dumps({"plan": "go to work, then go home", "intention": "work", "response": "ok",
                           "satisfaction": 0.7, "energy": 0.6, "hunger": 0.3, "safety": 0.8, "social": 0.5,
                           "need_type": "whatever", "steps": [{"intention": "go to work", "type": "mobility"}],
                           "target": 1, "selected_option": 1, "thought": "Today is a normal day."})
    if "yes or no" in p or "true or false" in p:
        return random.choice(["yes", "no"])
    for k in ("number", "integer", "score", "1-10", "0-1"):
        if k in p:
            return str(random.randint(1, 5))
    return "I feel fine today and will follow my usual routine."

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    prompt = "\n".join(str(m.get("content", "")) for m in body.get("messages", []))
    content = answer(prompt)
    with open("mock_llm.log", "a") as f:
        f.write(json.dumps({"prompt": prompt[-400:], "reply": content}) + "\n")
    return {"id": "mock", "object": "chat.completion", "created": int(time.time()),
            "model": body.get("model", "mock"),
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(content) // 4,
                      "total_tokens": (len(prompt) + len(content)) // 4}}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
