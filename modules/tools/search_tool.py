from typing import Dict, Any
import requests
from urllib.parse import quote
from ..config import Config


class SearchTool:
    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        self.cse_id = Config.GOOGLE_CSE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str) -> Dict[str, Any]:
        """
        Search using Google Custom Search API
        """
        try:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": 5,  # Number of results
                "fields": "items(title,snippet,link,pagemap/metatags/og:description)",  # Only get what we need
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            if "items" in data:
                for item in data["items"]:
                    # Try to get a better description from OpenGraph if available
                    description = item.get("snippet", "")
                    if "pagemap" in item and "metatags" in item["pagemap"]:
                        for metatag in item["pagemap"]["metatags"]:
                            if "og:description" in metatag:
                                description = metatag["og:description"]
                                break

                    results.append(
                        {
                            "title": item.get("title", ""),
                            "description": description,
                            "url": item.get("link", ""),
                        }
                    )

            # Create a comprehensive abstract from the first result
            abstract = ""
            if results:
                abstract = f"{results[0]['title']}: {results[0]['description']}"

            return {
                "abstract": abstract,
                "results": results,
                "query": query,
            }

        except requests.exceptions.Timeout:
            return {
                "error": "Search request timed out",
                "results": [],
                "abstract": "Search timed out, please try again",
                "query": query,
            }
        except Exception as e:
            return {
                "error": str(e),
                "results": [],
                "abstract": f"Search error occurred while searching for: {query}",
                "query": query,
            }
