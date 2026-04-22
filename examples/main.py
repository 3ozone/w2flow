"""main file for the app"""

import asyncio
from timbal import Agent, Workflow


class CreateAgentWorkflow():
    """MyWorkflow class"""

    def __init__(self, name: str, model: str, max_tokens: int):
        """Initialize the agent"""
        self.name = name
        self.model = model
        self.max_tokens = max_tokens

    def create_agent(self) -> Agent:
        """Create the agent"""
        return Agent(
            name=self.name,
            model=self.model,
            max_tokens=self.max_tokens
        )

    def create_workflow(self) -> Workflow:
        """Create the workflow"""
        return Workflow(name=self.name)


class CreateWorkFlow():
    """MyWorkflowAgent class"""

    def __init__(self, name: str, model: str, max_tokens: int):
        """Initialize the agent"""
        self.name = name
        self.model = model
        self.max_tokens = max_tokens

    async def init_workflow(self):
        """Init workflow"""
        workflow_builder = CreateAgentWorkflow(
            name=self.name,
            model=self.model,
            max_tokens=self.max_tokens
        )
        agent = workflow_builder.create_agent()
        workflow = workflow_builder.create_workflow()
        workflow.step(agent, prompt="What time is it in Tokyo right now?")
        result = await workflow().collect()
        print(f"The answer is: {result.output.collect_text()}")


if __name__ == "__main__":
    work = CreateWorkFlow(
        name="google-model",
        model="google/gemini-2.5-flash",
        max_tokens=1024
    )
    asyncio.run(work.init_workflow())
