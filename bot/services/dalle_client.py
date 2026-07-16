import asyncio

from openai import OpenAI


class DALLEClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> str:
        response = await asyncio.to_thread(
            self.client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=1,
        )
        return response.data[0].url
