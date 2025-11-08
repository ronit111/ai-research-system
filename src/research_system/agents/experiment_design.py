"""Experiment Design Agent - Agent 4."""

from typing import List, Dict, Any, Optional
import json
import uuid

from .base_agent import BaseAgent, AgentInput, AgentOutput
from ..storage.database import db
from ..integrations.obsidian_client import ObsidianClient


class ExperimentDesignAgent(BaseAgent):
    """
    Agent 4: Experiment Design

    Designs concrete experiments to test hypotheses.
    """

    def __init__(self):
        """Initialize Experiment Design Agent."""
        super().__init__(name="ExperimentDesignAgent")
        self.obsidian = ObsidianClient()

    def _sanitize_for_prompt(self, text: str, max_length: int = 500) -> str:
        """Sanitize text for LLM prompts."""
        if not text:
            return ""
        sanitized = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        return sanitized

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute experiment design.

        Args:
            input_data: Contains project_id and optional hypothesis_id

        Returns:
            AgentOutput with experiment design
        """
        project_id = input_data.project_id
        domain = input_data.domain
        hypothesis_id = input_data.context.get("hypothesis_id")

        if not project_id:
            return AgentOutput(
                success=False,
                results={"error": "project_id required"},
                educational_notes="Agent 4 needs a project to work with.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"\n🧪 Designing experiment for project: {project_id}")

        # Step 1: Load hypothesis
        print(f"   Loading hypothesis from database...")

        if hypothesis_id:
            hypotheses = db.get_hypotheses(project_id)
            hypothesis = next((h for h in hypotheses if h["id"] == hypothesis_id), None)
        else:
            # Use most recent hypothesis
            hypotheses = db.get_hypotheses(project_id)
            hypothesis = hypotheses[0] if hypotheses else None

        if not hypothesis:
            return AgentOutput(
                success=False,
                results={"error": "No hypothesis found. Run Agent 3 first."},
                educational_notes="Run Agent 3 (Hypothesis Formation) first.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"   Hypothesis: {hypothesis['hypothesis_text'][:80]}...")

        # Step 2: Design methodology
        print(f"   Designing experimental methodology...")
        methodology, tokens, cost = self._design_methodology(hypothesis, domain)

        total_tokens = tokens
        total_cost = cost

        # Step 3: Define data requirements
        print(f"   Defining data requirements...")
        data_req, data_tokens, data_cost = self._define_data_requirements(
            hypothesis, methodology
        )

        total_tokens += data_tokens
        total_cost += data_cost

        # Step 4: Estimate resources
        print(f"   Estimating resource requirements...")
        resources = self._estimate_resources(hypothesis, methodology, data_req)

        # Step 5: Generate code template (simplified)
        print(f"   Generating experiment code template...")
        code_template = self._generate_code_template(hypothesis, methodology, data_req)

        # Step 6: Save to database
        design_id = f"exp_{uuid.uuid4().hex[:12]}"

        db.add_experiment_design(
            design_id=design_id,
            hypothesis_id=hypothesis["id"],
            project_id=project_id,
            methodology=methodology,
            data_requirements=data_req,
            code_template=code_template,
            resource_estimates=resources,
            platform="local",
            metadata={"domain": domain}
        )

        # Step 7: Save to Obsidian
        print(f"   Saving to Obsidian vault...")
        try:
            design_file = self.obsidian.save_experiment_design(
                design_id=design_id,
                hypothesis_text=hypothesis["hypothesis_text"],
                methodology=methodology,
                data_requirements=data_req,
                code_template=code_template,
                resources=resources
            )
            artifacts = [str(design_file)]
        except Exception as e:
            print(f"   Warning: Could not save to Obsidian: {e}")
            artifacts = []

        # Generate educational notes
        educational_notes = self._generate_educational_notes(
            hypothesis, methodology, data_req, resources
        )

        return AgentOutput(
            success=True,
            results={
                "design_id": design_id,
                "hypothesis_id": hypothesis["id"],
                "methodology": methodology,
                "data_requirements": data_req,
                "resource_estimates": resources,
                "code_ready": True
            },
            artifacts=artifacts,
            metadata={
                "project_id": project_id,
                "design_id": design_id,
                "hypothesis_id": hypothesis["id"]
            },
            educational_notes=educational_notes,
            next_steps=[
                "Review experiment design in Obsidian",
                "Verify data requirements are feasible",
                "Run Agent 5 to execute experiment",
                "Ensure compute resources are available"
            ],
            tokens_used=total_tokens,
            cost_usd=total_cost
        )

    def _design_methodology(
        self,
        hypothesis: Dict[str, Any],
        domain: str
    ) -> tuple[str, int, float]:
        """Design experimental methodology."""

        hyp_text = self._sanitize_for_prompt(hypothesis.get("hypothesis_text", ""), 300)
        ivs = ", ".join(hypothesis.get("independent_variables", []))
        dvs = ", ".join(hypothesis.get("dependent_variables", []))
        sanitized_domain = self._sanitize_for_prompt(domain, 50)

        prompt = f"""Design an experimental methodology to test this hypothesis.

Domain: {sanitized_domain}
Hypothesis: {hyp_text}
Independent Variables: {ivs}
Dependent Variables: {dvs}

Describe:
1. **Experimental Design Type**: (e.g., A/B test, controlled experiment, observational study)
2. **Procedure**: Step-by-step process
3. **Controls**: How to isolate effects
4. **Measurements**: When and how to measure DVs

Write a clear, detailed methodology description (2-3 paragraphs)."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=800)

        return response.strip(), tokens, cost

    def _define_data_requirements(
        self,
        hypothesis: Dict[str, Any],
        methodology: str
    ) -> tuple[Dict[str, Any], int, float]:
        """Define data requirements for the experiment."""

        hyp_text = self._sanitize_for_prompt(hypothesis.get("hypothesis_text", ""), 200)
        method_text = self._sanitize_for_prompt(methodology, 300)

        prompt = f"""Define data requirements for this experiment.

Hypothesis: {hyp_text}
Methodology: {method_text}

Specify:
1. **Dataset Name/Source**: Where to get data
2. **Sample Size**: Minimum required samples
3. **Features**: Required data columns/fields
4. **Format**: Data format (CSV, JSON, etc.)

Respond with JSON:
{{
    "dataset_source": "name or URL",
    "min_samples": 1000,
    "required_features": ["feature1", "feature2"],
    "data_format": "CSV"
}}

Respond with ONLY valid JSON."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=400)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)
            return data, tokens, cost

        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Warning: Failed to parse data requirements: {e}")
            return {
                "dataset_source": "synthetic_data",
                "min_samples": 1000,
                "required_features": ["input", "output"],
                "data_format": "CSV"
            }, tokens, cost

    def _estimate_resources(
        self,
        hypothesis: Dict[str, Any],
        methodology: str,
        data_req: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate resource requirements (simplified)."""

        sample_size = data_req.get("min_samples", 1000)

        # Simple heuristic-based estimation
        if sample_size < 1000:
            compute_time = "< 5 minutes"
            cost = 0.0
        elif sample_size < 10000:
            compute_time = "5-30 minutes"
            cost = 0.0
        else:
            compute_time = "30-120 minutes"
            cost = 0.1

        return {
            "estimated_compute_time": compute_time,
            "estimated_cost_usd": cost,
            "platform": "local",
            "memory_gb": 4,
            "storage_gb": 1
        }

    def _generate_code_template(
        self,
        hypothesis: Dict[str, Any],
        methodology: str,
        data_req: Dict[str, Any]
    ) -> str:
        """Generate Python code template for experiment."""

        ivs = hypothesis.get("independent_variables", [])
        dvs = hypothesis.get("dependent_variables", [])

        template = f'''"""
Experiment: {hypothesis.get("hypothesis_text", "")[:60]}...
Generated by AI Research System
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
DATA_SOURCE = "{data_req.get("dataset_source", "data.csv")}"
SAMPLE_SIZE = {data_req.get("min_samples", 1000)}

# Independent Variables: {", ".join(ivs)}
# Dependent Variables: {", ".join(dvs)}

def load_data():
    """Load and prepare data."""
    # TODO: Implement data loading
    data = pd.DataFrame()  # Load your data here
    return data

def run_experiment():
    """Execute the experiment."""
    print("Loading data...")
    data = load_data()

    print(f"Data shape: {{data.shape}}")

    # TODO: Implement experimental procedure
    # 1. Manipulate independent variables
    # 2. Measure dependent variables
    # 3. Record results

    results = {{
        "sample_size": len(data),
        "metrics": {{}}
    }}

    return results

def save_results(results):
    """Save experimental results."""
    output_path = Path("results") / "experiment_results.json"
    output_path.parent.mkdir(exist_ok=True)

    import json
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {{output_path}}")

if __name__ == "__main__":
    results = run_experiment()
    save_results(results)
    print("Experiment complete!")
'''

        return template

    def _generate_educational_notes(
        self,
        hypothesis: Dict[str, Any],
        methodology: str,
        data_req: Dict[str, Any],
        resources: Dict[str, Any]
    ) -> str:
        """Generate educational notes."""

        return self.format_educational_note(f"""
**What just happened:**

I designed a concrete experiment to test your hypothesis: "{hypothesis.get('hypothesis_text', '')[:80]}..."

**Process:**
1. Analyzed the hypothesis and variables
2. Designed experimental methodology
3. Defined data requirements
4. Estimated resource needs
5. Generated executable Python code template

**Experiment Type:**
The methodology describes how to systematically test your hypothesis by manipulating the independent variables and measuring the dependent variables.

**Data Requirements:**
- **Source**: {data_req.get('dataset_source', 'N/A')}
- **Samples**: {data_req.get('min_samples', 'N/A')} minimum
- **Features**: {len(data_req.get('required_features', []))} required

**Resources Needed:**
- **Compute Time**: {resources.get('estimated_compute_time', 'N/A')}
- **Cost**: ${resources.get('estimated_cost_usd', 0):.2f}
- **Platform**: {resources.get('platform', 'local')}

**Why this matters:**
A good experimental design ensures:
- **Validity**: Results actually test your hypothesis
- **Reproducibility**: Others can replicate your work
- **Efficiency**: Minimizes resource waste
- **Statistical Power**: Enough samples to detect effects

**Next step:** Agent 5 will execute this experiment design. Review the code template in your Obsidian vault and customize it for your specific data source if needed.
""")
