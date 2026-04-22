"""Tooling functions for the agent."""

from timbal import Tool


def summ(a: int, b: int) -> int:
    """Return the sum of two numbers."""
    return a + b


tool = Tool(name="sumar", handler=summ, default_params={"b": 3})


async def trace_tool():
    """Trace the tool execution."""
    async for event in tool(a=1, b=2):
        print(f"Tool event: {event}")  # noqa: T201


async def main():
    """Main function to run the tool."""
    await trace_tool()
    result = await tool(a=3, b=5).collect()
    return result.output

if __name__ == "__main__":
    import asyncio
    output = asyncio.run(main())
    print(f"Tool output: {output}")  # noqa: T201
