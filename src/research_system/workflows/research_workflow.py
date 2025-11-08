"""Research workflow orchestration."""

from typing import Dict, Any, Optional
from datetime import datetime
import time

from ..agents.base_agent import AgentInput, AgentOutput
from ..storage.database import db
from ..services.cost_tracker import cost_tracker


class ResearchWorkflow:
    """
    Orchestrates the research workflow across multiple agents.

    For MVP, implements simple sequential execution.
    Will be enhanced with LangGraph for complex workflows.
    """

    def __init__(self, project_id: str, domain: str = "machine_learning"):
        """
        Initialize workflow.

        Args:
            project_id: Research project ID
            domain: Research domain
        """
        self.project_id = project_id
        self.domain = domain
        self.agents = {}
        self.state = {}

    def register_agent(self, name: str, agent: Any) -> None:
        """
        Register an agent with the workflow.

        Args:
            name: Agent identifier
            agent: Agent instance
        """
        self.agents[name] = agent

    async def run_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Run a single agent.

        Args:
            agent_name: Name of registered agent
            task: Task description
            context: Additional context

        Returns:
            Agent output

        Raises:
            ValueError: If agent not registered
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not registered")

        agent = self.agents[agent_name]

        # Prepare input
        agent_input = AgentInput(
            task=task,
            context=context or {},
            project_id=self.project_id,
            domain=self.domain
        )

        # Execute agent
        print(f"\n🤖 Running {agent_name}...")
        print(f"   Task: {task}")

        start_time = time.time()

        try:
            output = await agent.execute(agent_input)
            duration = time.time() - start_time

            # Log to database
            db.log_agent_run(
                project_id=self.project_id,
                agent_name=agent_name,
                tokens_used=output.tokens_used,
                cost_usd=output.cost_usd,
                results=output.results,
                status="completed" if output.success else "failed"
            )

            # Track costs
            cost_tracker.track_api_call(
                agent=agent_name,
                tokens_used=output.tokens_used,
                cost=output.cost_usd,
                metadata={"project_id": self.project_id, "duration": duration}
            )

            # Update workflow state
            self.state[agent_name] = output.results

            print(f"   ✅ Completed in {duration:.2f}s")
            print(f"   💰 Cost: ${output.cost_usd:.4f}")

            if output.educational_notes:
                print(f"\n📚 {output.educational_notes}\n")

            return output

        except Exception as e:
            duration = time.time() - start_time

            # Log failure
            db.log_agent_run(
                project_id=self.project_id,
                agent_name=agent_name,
                tokens_used=0,
                cost_usd=0.0,
                results={},
                status="failed",
                error=str(e)
            )

            print(f"   ❌ Failed after {duration:.2f}s: {e}")

            raise

    async def run_sequential(self, agents_and_tasks: list[tuple[str, str]]) -> Dict[str, Any]:
        """
        Run multiple agents sequentially.

        Args:
            agents_and_tasks: List of (agent_name, task) tuples

        Returns:
            Dictionary with all agent outputs
        """
        results = {}

        for agent_name, task in agents_and_tasks:
            # Pass previous results as context
            output = await self.run_agent(agent_name, task, context=self.state)
            results[agent_name] = output

        return results

    def get_state(self) -> Dict[str, Any]:
        """
        Get current workflow state.

        Returns:
            Current state dictionary
        """
        return self.state

    def print_summary(self) -> None:
        """Print workflow execution summary."""
        total_tokens = sum(
            output.tokens_used
            for output in self.state.values()
            if hasattr(output, 'tokens_used')
        )

        total_cost = sum(
            output.cost_usd
            for output in self.state.values()
            if hasattr(output, 'cost_usd')
        )

        print(f"\n{'='*60}")
        print(f"WORKFLOW SUMMARY - Project: {self.project_id}")
        print(f"{'='*60}")
        print(f"Agents Run: {len(self.state)}")
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"{'='*60}\n")
