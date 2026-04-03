import os
import json
from openai import OpenAI
from typing import Optional

# ---- Configuration ----
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = os.getenv("MODEL", "openai/gpt-4o")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))

# ---- Tool Definitions ----
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on a given topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_result",
            "description": "Save the final result or report to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the output file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to save"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    }
]

# ---- Tool Execution ----
def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool and return the result."""
    if tool_name == "web_search":
        # In production, integrate with Tavily, SerpAPI, or similar
        query = tool_args.get("query", "")
        print(f"[TOOL] web_search: {query}")
        return f"Search results for '{query}': [Integrate with Tavily API for real results]"

    elif tool_name == "save_result":
        filename = tool_args.get("filename", "output.txt")
        content = tool_args.get("content", "")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[TOOL] save_result: Saved to {filename}")
        return f"Successfully saved result to {filename}"

    return f"Unknown tool: {tool_name}"

# ---- Agent Loop ----
def run_agent(task: str, system_prompt: Optional[str] = None) -> str:
    """
    Run the AI agent on a given task.
    The agent will autonomously plan and execute steps until completion.
    """
    if system_prompt is None:
        system_prompt = (
            "You are an autonomous AI agent. You have access to tools to complete tasks. "
            "Think step by step, use tools when needed, and always provide a final answer."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]

    print(f"\n{'='*50}")
    print(f"TASK: {task}")
    print(f"{'='*50}")

    for iteration in range(MAX_ITERATIONS):
        print(f"\n[Iteration {iteration + 1}/{MAX_ITERATIONS}]")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        # If no tool calls, agent is done
        if not message.tool_calls:
            print(f"\n[AGENT DONE]")
            print(f"Final answer: {message.content}")
            return message.content

        # Process tool calls
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"[CALLING TOOL] {tool_name} with args: {tool_args}")
            tool_result = execute_tool(tool_name, tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    return "Max iterations reached."

# ---- Entry Point ----
if __name__ == "__main__":
    task = input("Enter your task for the AI agent: ")
    result = run_agent(task)
    print(f"\nResult:\n{result}")
