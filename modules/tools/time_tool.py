from typing import Dict, Any
from datetime import datetime
import pytz
from ..utils.location import location_detector


class TimeTool:
    def __init__(self):
        self.location = location_detector

    async def get_time(self, timezone: str = None) -> Dict[str, Any]:
        """Get current time for a specific timezone"""
        try:
            if not timezone:
                # Get timezone from user's location
                location_info = self.location.get_location()
                timezone = location_info.get("timezone", "UTC")

            # Get current time in specified timezone
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)

            return {
                "timezone": timezone,
                "current_time": current_time.strftime("%I:%M %p"),
                "date": current_time.strftime("%A, %B %d, %Y"),
                "unix_timestamp": int(current_time.timestamp()),
                "is_dst": current_time.dst() != None,
            }

        except pytz.exceptions.UnknownTimeZoneError:
            return {
                "error": f"Unknown timezone: {timezone}",
                "timezone": "UTC",
                "current_time": datetime.now(pytz.UTC).strftime("%I:%M %p"),
            }
        except Exception as e:
            return {
                "error": str(e),
                "timezone": "UTC",
                "current_time": datetime.now(pytz.UTC).strftime("%I:%M %p"),
            }
