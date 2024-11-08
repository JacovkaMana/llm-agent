from typing import Dict, Any
import requests
from ..config import Config


class NewsTool:
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY

    async def get_latest_news(self, topic: str = None) -> Dict[str, Any]:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"apiKey": self.api_key, "language": "en"}
        if topic:
            params["q"] = topic
        response = requests.get(url, params=params)
        return response.json()
