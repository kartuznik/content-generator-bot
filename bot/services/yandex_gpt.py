import httpx


class YandexGPTClient:
    def __init__(self, iam_token: str, folder_id: str):
        self.iam_token = iam_token
        self.folder_id = folder_id
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "Ты полезный ассистент для создания постов в Telegram.",
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json",
        }
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {"stream": False, "temperature": 0.7, "maxTokens": 1000},
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["result"]["alternatives"][0]["message"]["text"].strip()
