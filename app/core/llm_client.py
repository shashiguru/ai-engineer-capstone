import time
from openai import OpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL

class LLMClient:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        if not OPENAI_MODEL:
            raise ValueError("OPENAI_MODEL is not set")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def chat(self, messages: str | list[dict]) -> tuple[str, dict]:
        start = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": messages}
            ]
        )

        latency_ms = (time.perf_counter() - start) * 1000
        reply = response.choices[0].message.content or ""

        usage = {}
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            meta = {
                "model": self.model,
                "latency": round(latency_ms, 2),
                "usage": usage
            }
        return reply, meta