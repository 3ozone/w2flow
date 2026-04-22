"""Testing the WebSearch tool with an agent."""
from datetime import datetime

from timbal import Agent
from timbal.tools import WebSearch


def get_datetime() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sum(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b


agent = Agent(
    name="my_agent",
    model="google/gemini-2.5-flash",
    max_tokens=1024,
    tools=[get_datetime, sum]
)


async def main():
    """Main function to run the agent."""
    while True:
        prompt = input("prompt: ")

        if prompt == "q":
            break

        summary_a = input("summary a: ")
        summary_b = input("summary b: ")

        agent_output_event = await agent(prompt=prompt).collect()

        print(f"Agent: {agent_output_event.output}")  # noqa: T201

    for tool in agent.tools:
        if tool.name == "sum":
            result = await tool(a=summary_a, b=summary_b).collect()
            print(f"Sum result: {result.output}")  # noqa: T201

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
