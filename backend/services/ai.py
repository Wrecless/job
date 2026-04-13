import httpx
from typing import Any

from backend.config import get_settings


class AIService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.temperature = settings.ai_temperature
        self.max_tokens = settings.ai_max_tokens
        self.base_url = "https://api.openai.com/v1"
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str | None:
        if not self.is_configured:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"AI generation error: {e}")
                return None


ai_service = AIService()


async def generate_ai_content(
    prompt: str,
    system_prompt: str | None = None,
) -> str | None:
    return await ai_service.generate(prompt, system_prompt)
