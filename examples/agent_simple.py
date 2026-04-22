"""Agent simple example using tools."""

from timbal import Agent
from timbal.types.message import Message


agent = Agent(
    name="testing",
    model="google/gemini-2.5-flash",
    max_tokens=1024,
)


async def main():
    """Main function to run the agent."""

    response = await agent(prompt="What is the capital of Germany?").collect()
    print(f"Agent response: {response.output}")

    response = await agent(prompt=Message.validate("What is the capital of Germany?")).collect()
    print(
        f"Agent response with Message input: {response.output.collect_text()}")

    # async for event in agent(prompt="Hello"):
    #     print(event)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
