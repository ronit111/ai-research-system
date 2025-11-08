#!/usr/bin/env python3
"""
End-to-end test for the complete 6-agent research workflow.

Tests the entire pipeline:
1. Agent 1: Literature Review
2. Agent 2: Idea Generation
3. Agent 3: Hypothesis Formation
4. Agent 4: Experiment Design
5. Agent 5: Experiment Execution
6. Agent 6: Results Analysis
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from research_system.agents.literature_review import LiteratureReviewAgent
from research_system.agents.idea_generation import IdeaGenerationAgent
from research_system.agents.hypothesis_formation import HypothesisFormationAgent
from research_system.agents.experiment_design import ExperimentDesignAgent
from research_system.agents.experiment_execution import ExperimentExecutionAgent
from research_system.agents.results_analysis import ResultsAnalysisAgent
from research_system.agents.base_agent import AgentInput
from research_system.storage.database import db
from research_system.config.settings import settings


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num: int, text: str):
    """Print a formatted step."""
    print(f"\n{'─' * 80}")
    print(f"STEP {step_num}: {text}")
    print('─' * 80)


def print_result(success: bool, message: str):
    """Print a formatted result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


async def main():
    """Run end-to-end test."""

    print_header("AI Research System - End-to-End Test")
    print(f"Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {settings.database_path}")
    print(f"Obsidian Vault: {settings.obsidian_vault_path}")

    # Test configuration
    project_id = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    domain = "natural language processing"
    query = "transformer models attention mechanisms"

    print(f"\nTest Configuration:")
    print(f"  Project ID: {project_id}")
    print(f"  Domain: {domain}")
    print(f"  Query: {query}")

    total_cost = 0.0
    total_tokens = 0
    results = {}

    try:
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: Literature Review
        # ═══════════════════════════════════════════════════════════════════
        print_step(1, "Agent 1: Literature Review")

        agent1 = LiteratureReviewAgent()
        input1 = AgentInput(
            project_id=project_id,
            domain=domain,
            query=query,
            context={"max_papers": 5}
        )

        output1 = await agent1.execute(input1)

        if output1.success:
            papers = output1.results.get("papers", [])
            print_result(True, f"Literature review complete: {len(papers)} papers found")
            print(f"   Top paper: {papers[0].get('title', 'N/A')[:60]}...")
            total_cost += output1.cost_usd
            total_tokens += output1.tokens_used
            results["agent1"] = output1
        else:
            print_result(False, f"Literature review failed: {output1.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: Idea Generation
        # ═══════════════════════════════════════════════════════════════════
        print_step(2, "Agent 2: Idea Generation")

        agent2 = IdeaGenerationAgent()
        input2 = AgentInput(
            project_id=project_id,
            domain=domain,
            context={"num_ideas": 5}
        )

        output2 = await agent2.execute(input2)

        if output2.success:
            ideas = output2.results.get("ideas", [])
            print_result(True, f"Idea generation complete: {len(ideas)} ideas generated")
            if ideas:
                top_idea = ideas[0]
                print(f"   Top idea: {top_idea.get('title', 'N/A')}")
                print(f"   Overall score: {top_idea.get('overall_score', 0):.2f}/10")
            total_cost += output2.cost_usd
            total_tokens += output2.tokens_used
            results["agent2"] = output2
        else:
            print_result(False, f"Idea generation failed: {output2.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: Hypothesis Formation
        # ═══════════════════════════════════════════════════════════════════
        print_step(3, "Agent 3: Hypothesis Formation")

        agent3 = HypothesisFormationAgent()
        input3 = AgentInput(
            project_id=project_id,
            domain=domain,
            context={}  # Will use top-ranked idea
        )

        output3 = await agent3.execute(input3)

        if output3.success:
            hypothesis = output3.results.get("hypothesis", "")
            hypothesis_id = output3.results.get("hypothesis_id", "")
            variables = output3.results.get("variables", {})
            print_result(True, f"Hypothesis formation complete")
            print(f"   Hypothesis ID: {hypothesis_id}")
            print(f"   Hypothesis: {hypothesis[:80]}...")
            print(f"   Independent variables: {len(variables.get('independent', []))}")
            print(f"   Dependent variables: {len(variables.get('dependent', []))}")
            total_cost += output3.cost_usd
            total_tokens += output3.tokens_used
            results["agent3"] = output3
        else:
            print_result(False, f"Hypothesis formation failed: {output3.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # STEP 4: Experiment Design
        # ═══════════════════════════════════════════════════════════════════
        print_step(4, "Agent 4: Experiment Design")

        agent4 = ExperimentDesignAgent()
        input4 = AgentInput(
            project_id=project_id,
            domain=domain,
            context={}  # Will use most recent hypothesis
        )

        output4 = await agent4.execute(input4)

        if output4.success:
            design_id = output4.results.get("design_id", "")
            data_req = output4.results.get("data_requirements", {})
            resources = output4.results.get("resource_estimates", {})
            print_result(True, f"Experiment design complete")
            print(f"   Design ID: {design_id}")
            print(f"   Data source: {data_req.get('dataset_source', 'N/A')}")
            print(f"   Sample size: {data_req.get('min_samples', 'N/A')}")
            print(f"   Compute time: {resources.get('estimated_compute_time', 'N/A')}")
            print(f"   Cost: ${resources.get('estimated_cost_usd', 0):.2f}")
            total_cost += output4.cost_usd
            total_tokens += output4.tokens_used
            results["agent4"] = output4
        else:
            print_result(False, f"Experiment design failed: {output4.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # STEP 5: Experiment Execution
        # ═══════════════════════════════════════════════════════════════════
        print_step(5, "Agent 5: Experiment Execution")

        agent5 = ExperimentExecutionAgent()
        input5 = AgentInput(
            project_id=project_id,
            domain=domain,
            context={}  # Will use most recent design
        )

        output5 = await agent5.execute(input5)

        if output5.success:
            run_id = output5.results.get("run_id", "")
            status = output5.results.get("status", "")
            metrics = output5.results.get("metrics", {})
            duration = output5.results.get("duration_seconds", 0)
            print_result(True, f"Experiment execution complete")
            print(f"   Run ID: {run_id}")
            print(f"   Status: {status}")
            print(f"   Duration: {duration:.2f}s")
            if metrics:
                print(f"   Metrics:")
                for key, value in metrics.items():
                    print(f"     - {key}: {value}")
            total_cost += output5.cost_usd
            total_tokens += output5.tokens_used
            results["agent5"] = output5
        else:
            print_result(False, f"Experiment execution failed: {output5.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # STEP 6: Results Analysis
        # ═══════════════════════════════════════════════════════════════════
        print_step(6, "Agent 6: Results Analysis")

        agent6 = ResultsAnalysisAgent()
        input6 = AgentInput(
            project_id=project_id,
            domain=domain,
            context={}  # Will use most recent run
        )

        output6 = await agent6.execute(input6)

        if output6.success:
            analysis_id = output6.results.get("analysis_id", "")
            decision = output6.results.get("decision", "")
            p_value = output6.results.get("p_value", "N/A")
            effect_size = output6.results.get("effect_size", "N/A")
            print_result(True, f"Results analysis complete")
            print(f"   Analysis ID: {analysis_id}")
            print(f"   Decision: {decision}")
            print(f"   P-value: {p_value if isinstance(p_value, str) else f'{p_value:.4f}'}")
            print(f"   Effect size: {effect_size if isinstance(effect_size, str) else f'{effect_size:.3f}'}")
            total_cost += output6.cost_usd
            total_tokens += output6.tokens_used
            results["agent6"] = output6
        else:
            print_result(False, f"Results analysis failed: {output6.results.get('error')}")
            return

        # ═══════════════════════════════════════════════════════════════════
        # VERIFICATION
        # ═══════════════════════════════════════════════════════════════════
        print_header("Verification")

        # Check database records
        print("Database Records:")
        papers_count = len(db.get_papers(project_id))
        print_result(papers_count > 0, f"Papers: {papers_count} records")

        hypotheses = db.get_hypotheses(project_id)
        print_result(len(hypotheses) > 0, f"Hypotheses: {len(hypotheses)} records")

        designs = db.get_experiment_designs(project_id)
        print_result(len(designs) > 0, f"Experiment Designs: {len(designs)} records")

        runs = db.get_experiment_runs(project_id)
        print_result(len(runs) > 0, f"Experiment Runs: {len(runs)} records")

        analyses = db.get_analyses(project_id)
        print_result(len(analyses) > 0, f"Analyses: {len(analyses)} records")

        # Check Obsidian files
        print("\nObsidian Files:")
        vault_path = settings.obsidian_vault_path

        papers_dir = vault_path / "Papers"
        if papers_dir.exists():
            papers_files = list(papers_dir.glob("*.md"))
            print_result(len(papers_files) > 0, f"Papers: {len(papers_files)} files")
        else:
            print_result(False, "Papers directory not found")

        ideas_dir = vault_path / "Ideas"
        if ideas_dir.exists():
            ideas_files = list(ideas_dir.glob("*.md"))
            print_result(len(ideas_files) > 0, f"Ideas: {len(ideas_files)} files")
        else:
            print_result(False, "Ideas directory not found")

        hypotheses_dir = vault_path / "Hypotheses"
        if hypotheses_dir.exists():
            hypotheses_files = list(hypotheses_dir.glob("*.md"))
            print_result(len(hypotheses_files) > 0, f"Hypotheses: {len(hypotheses_files)} files")
        else:
            print_result(False, "Hypotheses directory not found")

        designs_dir = vault_path / "Experiment_Designs"
        if designs_dir.exists():
            designs_files = list(designs_dir.glob("*.md"))
            print_result(len(designs_files) > 0, f"Experiment Designs: {len(designs_files)} files")
        else:
            print_result(False, "Experiment_Designs directory not found")

        experiments_dir = vault_path / "Experiments"
        if experiments_dir.exists():
            experiments_files = list(experiments_dir.glob("*.md"))
            print_result(len(experiments_files) > 0, f"Experiments: {len(experiments_files)} files")
        else:
            print_result(False, "Experiments directory not found")

        analyses_dir = vault_path / "Analyses"
        if analyses_dir.exists():
            analyses_files = list(analyses_dir.glob("*.md"))
            print_result(len(analyses_files) > 0, f"Analyses: {len(analyses_files)} files")
        else:
            print_result(False, "Analyses directory not found")

        # ═══════════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        print_header("Test Summary")

        print("✅ All 6 agents executed successfully!")
        print(f"\nProject ID: {project_id}")
        print(f"Total tokens used: {total_tokens:,}")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n📁 Outputs saved to:")
        print(f"  Database: {settings.database_path}")
        print(f"  Obsidian Vault: {settings.obsidian_vault_path}")

        print("\n🔬 Scientific Process Complete:")
        print("  1. ✅ Literature Review")
        print("  2. ✅ Idea Generation")
        print("  3. ✅ Hypothesis Formation")
        print("  4. ✅ Experiment Design")
        print("  5. ✅ Experiment Execution")
        print("  6. ✅ Results Analysis")

        print("\n" + "=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
