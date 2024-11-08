from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
from ..config import Config


class WeatherTool:
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        # Configure retry strategy
        self.session = requests.Session()
        retries = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # status codes to retry on
            allowed_methods=["GET"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    async def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather data with retries and proper error handling
        """
        try:
            params = {"q": location, "appid": self.api_key, "units": "metric"}

            # Make request with retry mechanism
            response = self.session.get(
                self.base_url, params=params, timeout=15  # Increased timeout
            )
            response.raise_for_status()
            data = response.json()

            # Check for API error responses
            if data.get("cod") and str(data["cod"]) != "200":
                return {
                    "error": data.get("message", "Unknown error from weather API"),
                    "location": location,
                    "temperature": None,
                    "conditions": None,
                }

            # Format the response
            return {
                "location": location,
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "conditions": data.get("weather", [{}])[0].get("description"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "country": data.get("sys", {}).get("country"),
                "city": data.get("name"),
                "timestamp": data.get("dt"),
            }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timed out after multiple retries",
                "location": location,
                "temperature": None,
                "conditions": None,
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to get weather data: {str(e)}",
                "location": location,
                "temperature": None,
                "conditions": None,
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "location": location,
                "temperature": None,
                "conditions": None,
            }
        finally:
            # Always add a small delay after the request
            time.sleep(0.5)
