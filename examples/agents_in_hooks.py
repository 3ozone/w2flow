"""hooks in agents example"""
from timbal import Agent
from timbal.state import get_run_context

# Agent that will be used in a hook
agent_is_company = Agent(
    name="agent_is_company",
    system_prompt="""Determine if the input is a company name.
    Return only 'true' or 'false'.""",
    model="google/gemini-2.5-flash"
)

# Nest the agent under the parent agent's path
agent_is_company.nest("agent")


async def pre_hook():
    """Pre-hook to determine if the input is a company name."""
    span = get_run_context().current_span()

    result = await agent_is_company(
        prompt=f"Is '{span.input.get('prompt')}' a company?"
    ).collect()

    span.is_company = result.output.collect_text().strip().lower() == "true"

agent = Agent(
    name="agent",
    model="google/gemini-2.5-flash",
    pre_hook=pre_hook
)


async def main():
    """Main function to run the tool."""
    result = await agent(prompt="Apple").collect()
    return result.output

if __name__ == "__main__":
    import asyncio
    output = asyncio.run(main())
    print(output)
