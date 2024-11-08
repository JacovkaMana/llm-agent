from enum import Enum
from typing import List
import os

from dotenv import load_dotenv

load_dotenv()


class AllowedCommands(Enum):
    SEARCH = "search"
    NEWS = "news"
    WEATHER = "weather"
    TIME = "time"
    HELP = "help"


class Config:
    ALLOWED_COMMANDS: List[str] = [cmd.value for cmd in AllowedCommands]
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")
