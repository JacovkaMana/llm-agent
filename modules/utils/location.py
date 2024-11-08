import requests
from typing import Dict, Any
from functools import lru_cache


class LocationDetector:
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json"  # Free, no API key needed

    @lru_cache(maxsize=1)  # Cache the result to avoid multiple API calls
    def get_location(self) -> Dict[str, Any]:
        """Get location information based on IP address"""
        try:
            response = requests.get(self.ip_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return {
                    "city": data.get("city", ""),
                    "country": data.get("country", ""),
                    "timezone": data.get("timezone", ""),
                    "lat": data.get("lat", 0),
                    "lon": data.get("lon", 0),
                }
            else:
                return {
                    "city": "London",
                    "country": "UK",
                    "timezone": "Europe/London",
                }  # Default fallback

        except Exception:
            return {
                "city": "London",
                "country": "UK",
                "timezone": "Europe/London",
            }  # Default fallback


# Global instance
location_detector = LocationDetector()
