import asyncio
from typing import Dict, Any
from pydantic import BaseModel
from typing import Optional
from modules.config import Config, AllowedCommands
from modules.tools.search_tool import SearchTool
from modules.tools.news_tool import NewsTool
from modules.tools.weather_tool import WeatherTool
from modules.tools.time_tool import TimeTool
from modules.utils.location import location_detector


class ToolResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class ToolManager:
    def __init__(self):
        self.search_tool = SearchTool()
        self.news_tool = NewsTool()
        self.weather_tool = WeatherTool()
        self.time_tool = TimeTool()

        # Get user's location
        self.location = location_detector.get_location()

        # Default parameters using user's location
        self.defaults = {
            "search": {"query": "latest news"},
            "weather": {
                "location": f"{self.location['city']}, {self.location['country']}"
            },
            "news": {"topic": "technology"},
            "time": {"timezone": self.location["timezone"]},
        }

    async def execute_command(
        self, command: str, params: Dict[str, Any]
    ) -> ToolResponse:
        if command not in Config.ALLOWED_COMMANDS:
            return ToolResponse(
                success=False,
                data={},
                error=f"Command {command} not allowed. Allowed commands: {Config.ALLOWED_COMMANDS}",
            )

        try:
            # Merge provided parameters with defaults
            tool_params = self.defaults.get(command, {}).copy()
            if params:
                tool_params.update(params)

            if command == AllowedCommands.SEARCH.value:
                result = await self.search_tool.search(tool_params.get("query"))

            elif command == AllowedCommands.NEWS.value:
                result = await self.news_tool.get_latest_news(tool_params.get("topic"))

            elif command == AllowedCommands.WEATHER.value:
                result = await self.weather_tool.get_weather(
                    tool_params.get("location")
                )

            elif command == AllowedCommands.TIME.value:
                result = await self.time_tool.get_time(tool_params.get("timezone"))

            elif command == AllowedCommands.HELP.value:
                result = {
                    "available_commands": {
                        "search": f"Search for information (default: {self.defaults['search']['query']})",
                        "news": f"Get latest news (default: {self.defaults['news']['topic']})",
                        "weather": f"Get weather information (default: {self.defaults['weather']['location']})",
                        "time": f"Get current time (default: {self.defaults['time']['timezone']})",
                        "help": "Show available commands",
                    }
                }

            return ToolResponse(success=True, data=result)

        except Exception as e:
            return ToolResponse(success=False, data={}, error=str(e))


async def ingest_memory() -> dict:
    # Implementation for memory ingestion
    pass
