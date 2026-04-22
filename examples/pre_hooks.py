"""Exemple using pre-hooks"""
from datetime import datetime

from timbal import Tool
from timbal.state import get_run_context


def pre_hook():
    """Pre-hook to modify input parameters and store custom data."""
    span = get_run_context().current_span()
    # Modify input parameters that will be passed to the handler
    span.input["name"] = span.input["name"].capitalize()
    # Add a new parameter
    span.input["location"] = "Barcelona"
    # Store custom data for later use
    span.greet_time = datetime.now()


def greet(name: str, location: str) -> str:
    """Handler function that uses the modified input parameters."""
    return f"Hello {name} from {location}!"


greet_tool = Tool(
    name="greet",
    pre_hook=pre_hook,
    handler=greet,
)


async def main():
    """Main function to run the tool."""
    result = await greet_tool(name="alice").collect()
    return result.output

if __name__ == "__main__":
    import asyncio
    output = asyncio.run(main())
    print(output)
