import os
import requests
import json
from dotenv import load_dotenv
from langchain_core.language_models.llms import LLM

load_dotenv()  # .env dosyasından API key'i çek

class OpenRouterLLM(LLM):
    model: str = "deepseek/deepseek-r1-0528:free"
    api_key: str = os.getenv("OPENROUTER_API_KEY")

    def _call(self, prompt: str, stop=None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "LangchainPizzaBot",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))

        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.status_code} - {response.text}")
        
        return response.json()["choices"][0]["message"]["content"]
    
    @property
    def _llm_type(self) -> str:
        return "openrouter" 