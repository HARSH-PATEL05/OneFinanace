import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"

BASE_SYSTEM_PROMPT = """You are Sahayak, a smart and friendly personal finance assistant built into OneFinance — a personal finance platform for Indian users.

Your job:
- Answer questions about personal finance, budgeting, saving, investing, and stocks
- Give advice relevant to Indian markets (NSE, BSE, Nifty, Sensex)
- When the user asks about their finances, use the snapshot provided below
- Be concise — this is a chat UI, not an essay
- If you don't know something, say so honestly
- Never make up stock prices or financial figures
- Use ₹ for currency, not $
- If no financial snapshot is provided, answer generally

You are not a generic chatbot. You are a finance specialist. Stay on topic."""


def build_system_prompt(context_block: str = "") -> str:
    if context_block:
        return f"{BASE_SYSTEM_PROMPT}\n\n{context_block}"
    return BASE_SYSTEM_PROMPT


async def stream_chat(user_message: str, history: list, context_block: str = ""):
    """
    Sends message + history to Ollama and streams the response back.
    context_block is the user's financial snapshot as a formatted string.
    """

    system_prompt = build_system_prompt(context_block)

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
