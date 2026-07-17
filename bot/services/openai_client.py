from __future__ import annotations

import asyncio

from openai import OpenAI


class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "Ты полезный ассистент для создания постов в Telegram.",
        model: str = "gpt-4o-mini",
    ) -> str:
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return (response.choices[0].message.content or "").strip()

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        response = await asyncio.to_thread(
            self.client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=1,
        )
        return response.data[0].url
