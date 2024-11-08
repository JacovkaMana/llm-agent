import os
import json
import requests
import time
import asyncio
from typing import Dict, Any, List, Union, Optional
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(Enum):
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0

    async def wait(self):
        """Wait if necessary to comply with rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.interval:
            wait_time = self.interval - time_since_last_request
            # print(f"\nRate limit: waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=10)  # Adjust the rate as needed


class ChatMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMConfig:
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: Union[str, LLMProvider] = LLMProvider.MISTRAL,
    ):
        self.provider = (
            provider if isinstance(provider, LLMProvider) else LLMProvider(provider)
        )
        self.api_url = api_url or os.getenv("LLM_API_URL")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL")

        if not self.api_key:
            raise ValueError(
                "API key not provided and LLM_API_KEY not found in environment"
            )

    def get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def format_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        return [msg.to_dict() for msg in messages]


async def chat_prompt(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    provider: Union[str, LLMProvider] = LLMProvider.MISTRAL,
) -> str:
    """
    Make a chat completion request to an LLM API endpoint.
    """
    # Wait for rate limiter before making request
    await rate_limiter.wait()

    config = LLMConfig(provider=provider)

    messages = []
    if system_prompt:
        messages.append(ChatMessage("system", system_prompt))
    messages.append(ChatMessage("user", prompt))

    payload = {
        "model": config.model,
        "messages": config.format_messages(messages),
        "temperature": temperature,
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens

    try:
        response = requests.post(
            config.api_url,
            headers=config.get_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()

        if config.provider == LLMProvider.MISTRAL:
            return result["choices"][0]["message"]["content"]
        elif config.provider == LLMProvider.OPENAI:
            return result["choices"][0]["message"]["content"]
        elif config.provider == LLMProvider.ANTHROPIC:
            return result["content"][0]["text"]
        else:  # CUSTOM or unknown provider
            try:
                return result["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                try:
                    return result["response"]
                except KeyError:
                    return str(result)

    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except (KeyError, IndexError) as e:
        raise Exception(f"Unexpected API response format: {str(e)}")


async def structured_output_prompt(
    prompt: str,
    response_format: Dict[str, Any],
    temperature: float = 0.1,
    provider: Union[str, LLMProvider] = LLMProvider.MISTRAL,
) -> Dict[str, Any]:
    """Make a request to LLM API endpoint with structured output format"""

    # Wait for rate limiter before making request
    await rate_limiter.wait()

    system_prompt = """You are a JSON-only response assistant. Never include explanations or notes.
    Only output valid JSON that matches the requested schema exactly. Do not escape underscores or other characters."""

    formatted_prompt = f"""
    Follow this schema exactly:
    {json.dumps(response_format, indent=2)}
    
    For the user input: {prompt}
    
    Rules:
    - Return valid JSON matching the schema
    - Do not escape special characters
    - No markdown formatting
    - No explanations outside JSON
    """

    response = await chat_prompt(
        prompt=formatted_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        provider=provider,
    )

    # Clean the response
    response = response.strip()

    # Remove any markdown formatting
    if response.startswith("```json"):
        response = response.split("```json")[1]
    elif response.startswith("```"):
        response = response.split("```")[1]
    if response.endswith("```"):
        response = response.rsplit("```", 1)[0]

    # Clean up any escaped characters
    response = response.replace("\\_", "_")

    try:
        cleaned_response = response.strip()

        # If response is an array
        if cleaned_response.startswith("["):
            end = cleaned_response.rfind("]") + 1
            if end != 0:
                cleaned_response = cleaned_response[:end]
            result = json.loads(cleaned_response)
            if not isinstance(result, list):
                result = [result]
            return result

        # If response is an object
        elif cleaned_response.startswith("{"):
            end = cleaned_response.rfind("}") + 1
            if end != 0:
                cleaned_response = cleaned_response[:end]
            result = json.loads(cleaned_response)
            return [result]  # Return as single-item list for consistency

        else:
            raise ValueError("Response neither starts with [ nor {")

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON. Response was:\n{response}")
        raise ValueError(
            f"Failed to parse JSON response: {str(e)}\nResponse was: {response}"
        )


def parse_markdown_backticks(str) -> str:
    if "```" not in str:
        return str.strip()

    str = str.split("```", 1)[-1].split("\n", 1)[-1]
    str = str.rsplit("```", 1)[0]
    return str.strip()
