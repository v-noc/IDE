# agent/runner/executor.py

from agent.runner.task_manager import TaskManager
from agent.graph.builder import build_agent_graph
from agent.workflows.base import BaseWorkflow


class AgentExecutor:
    """High-level entry point for running agents and workflows as tasks."""

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager

    def run_workflow(self, workflow: BaseWorkflow, **kwargs) -> str:
        """Submit a workflow for background execution."""
        return self.task_manager.submit(
            name=f"workflow:{workflow.name}",
            coro_factory=workflow.run,
            **kwargs,
        )

    def run_agent_chat(self, conversation_id: str, message: str) -> str:
        """Submit an agent chat turn for background execution."""
        async def _run_agent(**kw):
            graph = build_agent_graph()
            result = await graph.ainvoke(kw)
            return result

        return self.task_manager.submit(
            name=f"agent:chat:{conversation_id}",
            coro_factory=_run_agent,
            conversation_id=conversation_id,
            message=message,
        )
