"""Hypothesis Formation Agent - Agent 3."""

from typing import List, Dict, Any, Optional
import json
import uuid

from .base_agent import BaseAgent, AgentInput, AgentOutput
from ..storage.database import db
from ..integrations.obsidian_client import ObsidianClient


class HypothesisFormationAgent(BaseAgent):
    """
    Agent 3: Hypothesis Formation

    Converts research ideas into testable, structured hypotheses.
    """

    def __init__(self):
        """Initialize Hypothesis Formation Agent."""
        super().__init__(name="HypothesisFormationAgent")
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
        Execute hypothesis formation.

        Args:
            input_data: Contains project_id and optional idea_title to convert

        Returns:
            AgentOutput with structured hypothesis
        """
        project_id = input_data.project_id
        domain = input_data.domain
        idea_title = input_data.context.get("idea_title")

        if not project_id:
            return AgentOutput(
                success=False,
                results={"error": "project_id required"},
                educational_notes="Agent 3 needs a project to work with.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"\n🔬 Forming testable hypothesis for project: {project_id}")

        # Step 1: Load ideas from Agent 2
        print(f"   Loading research ideas from database...")

        # Get ideas from database (stored in agent_runs metadata)
        agent_runs = db.conn.cursor().execute("""
            SELECT results FROM agent_runs
            WHERE project_id = ? AND agent_name = 'IdeaGenerationAgent'
            AND status = 'completed'
            ORDER BY completed_at DESC LIMIT 1
        """, (project_id,)).fetchone()

        if not agent_runs:
            return AgentOutput(
                success=False,
                results={"error": "No ideas found. Run Agent 2 first."},
                educational_notes="Run Agent 2 (Idea Generation) first to generate ideas.",
                tokens_used=0,
                cost_usd=0.0
            )

        ideas_data = json.loads(agent_runs[0])
        ideas = ideas_data.get("ideas", [])

        if not ideas:
            return AgentOutput(
                success=False,
                results={"error": "No ideas in Agent 2 output"},
                educational_notes="Agent 2 didn't produce any ideas.",
                tokens_used=0,
                cost_usd=0.0
            )

        # Step 2: Select idea
        if idea_title:
            selected_idea = next((i for i in ideas if i["title"] == idea_title), None)
            if not selected_idea:
                return AgentOutput(
                    success=False,
                    results={"error": f"Idea '{idea_title}' not found"},
                    educational_notes="Specify a valid idea title from Agent 2 output.",
                    tokens_used=0,
                    cost_usd=0.0
                )
        else:
            # Use top-ranked idea
            selected_idea = ideas[0]

        print(f"   Selected idea: {selected_idea['title']}")
        print(f"   Novelty: {selected_idea.get('novelty_score', 0):.1f}/10")

        # Step 3: Generate hypothesis
        print(f"   Generating testable hypothesis...")
        hypothesis_data, tokens, cost = self._generate_hypothesis(
            selected_idea, domain
        )

        total_tokens = tokens
        total_cost = cost

        # Step 4: Identify variables
        print(f"   Identifying variables...")
        variables, var_tokens, var_cost = self._identify_variables(
            hypothesis_data, selected_idea, domain
        )

        total_tokens += var_tokens
        total_cost += var_cost

        # Step 5: Define success criteria
        print(f"   Defining success criteria...")
        criteria, crit_tokens, crit_cost = self._define_success_criteria(
            hypothesis_data, variables, domain
        )

        total_tokens += crit_tokens
        total_cost += crit_cost

        # Step 6: Save to database
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:12]}"

        db.add_hypothesis(
            hypothesis_id=hypothesis_id,
            project_id=project_id,
            idea_title=selected_idea["title"],
            hypothesis_text=hypothesis_data["hypothesis"],
            null_hypothesis=hypothesis_data.get("null_hypothesis"),
            independent_variables=variables["independent"],
            dependent_variables=variables["dependent"],
            control_variables=variables["control"],
            success_criteria=criteria,
            metadata={
                "idea_scores": {
                    "novelty": selected_idea.get("novelty_score"),
                    "feasibility": selected_idea.get("feasibility_score"),
                    "impact": selected_idea.get("impact_score")
                }
            }
        )

        # Step 7: Save to Obsidian
        print(f"   Saving to Obsidian vault...")
        try:
            hypothesis_file = self.obsidian.save_hypothesis(
                hypothesis_id=hypothesis_id,
                project_id=project_id,
                idea_title=selected_idea["title"],
                hypothesis_text=hypothesis_data["hypothesis"],
                null_hypothesis=hypothesis_data.get("null_hypothesis"),
                variables=variables,
                success_criteria=criteria
            )
            artifacts = [str(hypothesis_file)]
        except Exception as e:
            print(f"   Warning: Could not save to Obsidian: {e}")
            artifacts = []

        # Generate educational notes
        educational_notes = self._generate_educational_notes(
            hypothesis_data, variables, criteria, selected_idea
        )

        return AgentOutput(
            success=True,
            results={
                "hypothesis_id": hypothesis_id,
                "hypothesis": hypothesis_data["hypothesis"],
                "null_hypothesis": hypothesis_data.get("null_hypothesis"),
                "variables": variables,
                "success_criteria": criteria,
                "idea_source": selected_idea["title"]
            },
            artifacts=artifacts,
            metadata={
                "project_id": project_id,
                "hypothesis_id": hypothesis_id,
                "idea_scores": {
                    "novelty": selected_idea.get("novelty_score"),
                    "feasibility": selected_idea.get("feasibility_score"),
                    "impact": selected_idea.get("impact_score")
                }
            },
            educational_notes=educational_notes,
            next_steps=[
                "Review the hypothesis in your Obsidian vault",
                "Validate that variables are measurable",
                "Run Agent 4 to design experiments",
                "Consider ethical implications"
            ],
            tokens_used=total_tokens,
            cost_usd=total_cost
        )

    def _generate_hypothesis(
        self,
        idea: Dict[str, Any],
        domain: str
    ) -> tuple[Dict[str, str], int, float]:
        """Generate testable hypothesis from idea."""

        # Sanitize inputs
        title = self._sanitize_for_prompt(idea.get("title", ""), 150)
        description = self._sanitize_for_prompt(idea.get("description", ""), 400)
        approach = self._sanitize_for_prompt(idea.get("approach", ""), 300)
        sanitized_domain = self._sanitize_for_prompt(domain, 50)

        prompt = f"""Convert this research idea into a testable hypothesis.

Domain: {sanitized_domain}

Research Idea:
**Title**: {title}
**Description**: {description}
**Proposed Approach**: {approach}

Generate:
1. **Hypothesis** (H1): A clear, testable statement predicting a specific relationship
2. **Null Hypothesis** (H0): The statement that there is no effect/relationship

Guidelines:
- Make it specific and measurable
- State the expected direction of effect (if applicable)
- Ensure it can be empirically tested
- Use precise terminology

Respond with JSON:
{{
    "hypothesis": "If X, then Y because Z",
    "null_hypothesis": "X has no effect on Y"
}}

Respond with ONLY valid JSON, no other text."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=500)

        try:
            # Parse JSON
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            if "hypothesis" not in data:
                raise ValueError("Missing 'hypothesis' key")

            return data, tokens, cost

        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Warning: Failed to parse hypothesis JSON: {e}")
            # Fallback
            return {
                "hypothesis": f"Investigating {title} will reveal significant insights about {description[:50]}",
                "null_hypothesis": "No significant effect will be observed"
            }, tokens, cost

    def _identify_variables(
        self,
        hypothesis_data: Dict[str, str],
        idea: Dict[str, Any],
        domain: str
    ) -> tuple[Dict[str, List[str]], int, float]:
        """Identify independent, dependent, and control variables."""

        hypothesis_text = self._sanitize_for_prompt(hypothesis_data.get("hypothesis", ""), 300)
        sanitized_domain = self._sanitize_for_prompt(domain, 50)

        prompt = f"""Identify the variables for this hypothesis.

Domain: {sanitized_domain}
Hypothesis: {hypothesis_text}

Identify:
1. **Independent Variables** (IV): What you manipulate/change
2. **Dependent Variables** (DV): What you measure as outcome
3. **Control Variables**: What you keep constant

Respond with JSON:
{{
    "independent": ["variable 1", "variable 2"],
    "dependent": ["outcome 1", "outcome 2"],
    "control": ["factor 1", "factor 2"]
}}

Respond with ONLY valid JSON, no other text."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=400)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            # Validate structure
            for key in ["independent", "dependent", "control"]:
                if key not in data or not isinstance(data[key], list):
                    data[key] = []

            return data, tokens, cost

        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Warning: Failed to parse variables JSON: {e}")
            # Fallback
            return {
                "independent": ["treatment_condition"],
                "dependent": ["outcome_metric"],
                "control": ["baseline_factors"]
            }, tokens, cost

    def _define_success_criteria(
        self,
        hypothesis_data: Dict[str, str],
        variables: Dict[str, List[str]],
        domain: str
    ) -> tuple[Dict[str, Any], int, float]:
        """Define success criteria for hypothesis testing."""

        hypothesis_text = self._sanitize_for_prompt(hypothesis_data.get("hypothesis", ""), 300)
        dv_list = ", ".join(variables.get("dependent", []))
        sanitized_domain = self._sanitize_for_prompt(domain, 50)

        prompt = f"""Define success criteria for testing this hypothesis.

Domain: {sanitized_domain}
Hypothesis: {hypothesis_text}
Dependent Variables: {dv_list}

Define:
1. **Statistical Significance**: p-value threshold (typically 0.05)
2. **Effect Size**: Minimum meaningful difference (Cohen's d, etc.)
3. **Sample Size**: Minimum required samples
4. **Metrics**: How to measure each DV quantitatively

Respond with JSON:
{{
    "significance_level": 0.05,
    "minimum_effect_size": 0.3,
    "minimum_sample_size": 100,
    "metrics": {{
        "metric_name": "measurement_method"
    }}
}}

Respond with ONLY valid JSON, no other text."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=400)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            # Set defaults if missing
            if "significance_level" not in data:
                data["significance_level"] = 0.05
            if "minimum_effect_size" not in data:
                data["minimum_effect_size"] = 0.3
            if "minimum_sample_size" not in data:
                data["minimum_sample_size"] = 100
            if "metrics" not in data:
                data["metrics"] = {}

            return data, tokens, cost

        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Warning: Failed to parse criteria JSON: {e}")
            # Fallback
            return {
                "significance_level": 0.05,
                "minimum_effect_size": 0.3,
                "minimum_sample_size": 100,
                "metrics": {"primary_outcome": "measure_change"}
            }, tokens, cost

    def _generate_educational_notes(
        self,
        hypothesis_data: Dict[str, str],
        variables: Dict[str, List[str]],
        criteria: Dict[str, Any],
        idea: Dict[str, Any]
    ) -> str:
        """Generate educational notes for the user."""

        return self.format_educational_note(f"""
**What just happened:**

I converted your research idea "{idea['title']}" into a testable, structured hypothesis.

**Process:**
1. Analyzed your research idea for core claims
2. Formulated a specific, testable hypothesis (H1)
3. Generated a null hypothesis (H0) for statistical testing
4. Identified independent, dependent, and control variables
5. Defined success criteria (significance level, effect size, sample size)

**The Hypothesis:**
{hypothesis_data.get('hypothesis', 'N/A')}

**Variables Identified:**
- **Independent** (what we manipulate): {len(variables.get('independent', []))} variable(s)
- **Dependent** (what we measure): {len(variables.get('dependent', []))} variable(s)
- **Control** (what we keep constant): {len(variables.get('control', []))} variable(s)

**Success Criteria:**
- Statistical significance: p < {criteria.get('significance_level', 0.05)}
- Minimum effect size: {criteria.get('minimum_effect_size', 0.3)}
- Minimum sample size: {criteria.get('minimum_sample_size', 100)}

**Why this matters:**
A well-formed hypothesis is:
- **Testable**: Can be empirically validated or rejected
- **Specific**: Clear predictions, not vague claims
- **Falsifiable**: Could be proven wrong
- **Measurable**: Variables can be quantified

**Scientific Method:**
We're following the scientific method:
1. ✅ Question (from literature review)
2. ✅ Hypothesis (just completed!)
3. ⏭️  Experiment Design (Agent 4)
4. ⏭️  Data Collection (Agent 5)
5. ⏭️  Analysis (Agent 6)
6. ⏭️  Conclusion

**Next step:** Agent 4 will design concrete experiments to test this hypothesis. Review the hypothesis in your Obsidian vault and ensure the variables are truly measurable with available resources.
""")
