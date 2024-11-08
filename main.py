import asyncio
import os
from typing import Dict, Any, List
from modules.tools_manager import ToolManager
from modules.llm import chat_prompt, structured_output_prompt
from modules.config import Config


class LLMAgent:
    def __init__(self):
        self.tool_manager = ToolManager()

    async def process_request(self, user_input: str) -> str:
        # 1. Plan and get tools
        planning_prompt = f"""
        Based on the user input: '{user_input}'
        Determine which tools are needed to provide a complete answer.
        Available tools: {Config.ALLOWED_COMMANDS}

        Parameter handling rules:
        1. For weather and location-based queries:
           - Extract city or country name if present
           - If no location is specified, use empty params to get default location
        2. For time queries:
           - Extract timezone or city/country if present
           - If no location is specified, use empty params to get local time
        3. For news:
           - Extract specific topic if present
           - If no topic specified, use empty params for default topic
        4. For search:
           - Use the entire query if no other specific parameters are found

        Return a JSON array of commands and their parameters.
        
        Examples:
        "weather in London" -> [{{"command": "weather", "params": {{"location": "London"}}}}]
        "weather" -> [{{"command": "weather", "params": {{}}}}]
        "what time is it in Tokyo" -> [{{"command": "time", "params": {{"timezone": "Asia/Tokyo"}}}}]
        "what's the weather and time in Paris" -> [
            {{"command": "weather", "params": {{"location": "Paris"}}}},
            {{"command": "time", "params": {{"timezone": "Europe/Paris"}}}}
        ]
        "news about AI" -> [{{"command": "news", "params": {{"topic": "AI"}}}}]
        "current time" -> [{{"command": "time", "params": {{}}}}]
        """

        plan = await structured_output_prompt(
            prompt=planning_prompt,
            response_format={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "params": {"type": "object"},
                    },
                },
            },
        )

        print("\nInitial tools:")
        [print(f"Using {cmd['command']} with {cmd['params']}") for cmd in plan]

        # 2. Execute tools and gather data
        tool_responses = await asyncio.gather(
            *[
                self.tool_manager.execute_command(cmd["command"], cmd["params"])
                for cmd in plan
            ]
        )

        # Check for errors
        errors = [resp.error for resp in tool_responses if not resp.success]
        if errors:
            return f"Error(s) occurred: {'; '.join(errors)}"

        # 3. Initial data analysis and draft response
        context = {
            "user_question": user_input,
            "tool_responses": [
                {"command": plan[i]["command"], "data": resp.data}
                for i, resp in enumerate(tool_responses)
            ],
        }

        draft_response_prompt = f"""
        Based on:
        User question: "{user_input}"
        Available data: {context['tool_responses']}
        
        1. Analyze if this data is sufficient to answer the question
        2. Identify any suggestions or recommendations you want to make
        3. Return in JSON format:
        {{
            "draft_answer": string,
            "suggestions": array of strings,
            "needs_search": array of strings with search queries for each suggestion
        }}
        """

        analysis = (
            await structured_output_prompt(
                prompt=draft_response_prompt,
                response_format={
                    "type": "object",
                    "properties": {
                        "draft_answer": {"type": "string"},
                        "suggestions": {"type": "array", "items": {"type": "string"}},
                        "needs_search": {"type": "array", "items": {"type": "string"}},
                    },
                },
            )
        )[0]

        print("\nInitial response done")

        # 4. Perform additional searches for suggestions
        additional_info = []
        if analysis.get("needs_search"):
            print("\nGathering additional information for suggestions...")
            for query in analysis["needs_search"]:
                print(f"Searching: {query}")
                search_result = await self.tool_manager.execute_command(
                    "search", {"query": query}
                )
                if search_result.success:
                    additional_info.append({"query": query, "data": search_result.data})

        print("\nAdditional information analysis done")

        # 5. Generate final enriched response
        final_response_prompt = f"""
        Original answer: {analysis.get('draft_answer')}
        Suggestions to address: {analysis.get('suggestions')}
        Additional information: {additional_info}
        
        Provide a complete response that:
        1. Starts with the main answer to the user's question
        2. Includes relevant suggestions with supporting information
        3. Keeps each part concise but informative
        4. Uses natural, conversational language
        5. Total response should be 6-7 sentences maximum
        """

        return await chat_prompt(
            prompt=final_response_prompt,
            system_prompt="""You are a helpful assistant. Provide clear, concise answers 
            that include both direct responses and relevant suggestions.""",
            temperature=0.7,
        )


async def main():
    agent = LLMAgent()

    print("AI Assistant ready! (Type 'exit' to quit)")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break

        try:
            response = await agent.process_request(user_input)
            print(f"\nAssistant: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
