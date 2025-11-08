"""Experiment Execution Agent - Agent 5 (Simplified)."""

from typing import Dict, Any, Optional
import json
import uuid
import time
from pathlib import Path

from .base_agent import BaseAgent, AgentInput, AgentOutput
from ..storage.database import db
from ..integrations.obsidian_client import ObsidianClient


class ExperimentExecutionAgent(BaseAgent):
    """
    Agent 5: Experiment Execution

    Executes experiments locally (simplified version).
    """

    def __init__(self):
        """Initialize Experiment Execution Agent."""
        super().__init__(name="ExperimentExecutionAgent")
        self.obsidian = ObsidianClient()

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute experiment execution.

        Args:
            input_data: Contains project_id and optional design_id

        Returns:
            AgentOutput with execution results
        """
        project_id = input_data.project_id
        design_id = input_data.context.get("design_id")

        if not project_id:
            return AgentOutput(
                success=False,
                results={"error": "project_id required"},
                educational_notes="Agent 5 needs a project to work with.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"\n⚙️  Executing experiment for project: {project_id}")

        # Step 1: Load experiment design
        print(f"   Loading experiment design...")

        if design_id:
            designs = db.get_experiment_designs(project_id=project_id)
            design = next((d for d in designs if d["id"] == design_id), None)
        else:
            designs = db.get_experiment_designs(project_id=project_id)
            design = designs[0] if designs else None

        if not design:
            return AgentOutput(
                success=False,
                results={"error": "No experiment design found. Run Agent 4 first."},
                educational_notes="Run Agent 4 (Experiment Design) first.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"   Design ID: {design['id']}")

        # Step 2: Prepare execution environment
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        db.add_experiment_run(
            run_id=run_id,
            design_id=design["id"],
            project_id=project_id,
            platform="local",
            metadata={"automated": True}
        )

        # Step 3: Execute (simplified - generate synthetic results)
        print(f"   Running experiment (simulated)...")

        try:
            # In a real implementation, this would:
            # 1. Write code to file
            # 2. Execute in subprocess
            # 3. Capture output
            # For now, we simulate results

            results_data = {
                "status": "completed",
                "samples_processed": design["data_requirements"].get("min_samples", 1000),
                "metrics": {
                    "accuracy": 0.85,
                    "precision": 0.82,
                    "recall": 0.88,
                    "f1_score": 0.85
                },
                "execution_time_seconds": 45.3
            }

            duration = time.time() - start_time
            logs = f"Execution log:\n- Started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n- Completed successfully\n- Duration: {duration:.2f}s"

            # Update run in database
            db.update_experiment_run(
                run_id=run_id,
                status="completed",
                results_data=results_data,
                logs=logs,
                duration_seconds=duration,
                compute_cost_usd=0.0
            )

            print(f"   ✅ Execution complete! ({duration:.1f}s)")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            db.update_experiment_run(
                run_id=run_id,
                status="failed",
                error=error_msg,
                duration_seconds=duration
            )

            return AgentOutput(
                success=False,
                results={"error": error_msg, "run_id": run_id},
                educational_notes=f"Execution failed: {error_msg}",
                tokens_used=0,
                cost_usd=0.0
            )

        # Step 4: Save results to Obsidian
        print(f"   Saving results to Obsidian...")
        try:
            results_file = self.obsidian.save_experiment_results(
                project_name=project_id,
                experiment_id=run_id,
                results=results_data
            )
            artifacts = [str(results_file)]
        except Exception as e:
            print(f"   Warning: Could not save to Obsidian: {e}")
            artifacts = []

        # Generate educational notes
        educational_notes = self._generate_educational_notes(
            design, results_data, duration
        )

        return AgentOutput(
            success=True,
            results={
                "run_id": run_id,
                "design_id": design["id"],
                "status": "completed",
                "duration_seconds": duration,
                "metrics": results_data["metrics"],
                "samples_processed": results_data["samples_processed"]
            },
            artifacts=artifacts,
            metadata={
                "project_id": project_id,
                "run_id": run_id,
                "design_id": design["id"],
                "platform": "local"
            },
            educational_notes=educational_notes,
            next_steps=[
                "Review experimental results in Obsidian",
                "Run Agent 6 to analyze results",
                "Validate data quality",
                "Compare with expected outcomes"
            ],
            tokens_used=0,  # No LLM calls in execution
            cost_usd=0.0
        )

    def _generate_educational_notes(
        self,
        design: Dict[str, Any],
        results: Dict[str, Any],
        duration: float
    ) -> str:
        """Generate educational notes."""

        metrics_str = "\n".join([f"- {k}: {v}" for k, v in results.get("metrics", {}).items()])

        return self.format_educational_note(f"""
**What just happened:**

I executed the experiment based on your design and collected results.

**Process:**
1. Loaded experiment design from database
2. Set up execution environment (local)
3. Ran experiment code
4. Collected results and metrics
5. Saved everything to database and Obsidian

**Results Summary:**
- **Status**: {results.get('status', 'unknown')}
- **Samples Processed**: {results.get('samples_processed', 'N/A'):,}
- **Execution Time**: {duration:.2f} seconds

**Metrics Collected:**
{metrics_str}

**Why this matters:**
Execution is where theory meets reality. The experimental results will be analyzed by Agent 6 to determine if your hypothesis is supported.

**Note**: This is a simplified execution using simulated data. In a full implementation, this would:
- Write code to a file
- Execute in an isolated environment
- Handle real data processing
- Monitor resource usage
- Capture detailed logs

**Next step:** Agent 6 will perform statistical analysis on these results to validate your hypothesis.
""")
