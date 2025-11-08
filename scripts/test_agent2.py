"""Test script for Agent 1 → Agent 2 workflow."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from research_system.agents.literature_review import LiteratureReviewAgent
from research_system.agents.idea_generation import IdeaGenerationAgent
from research_system.agents.base_agent import AgentInput
from research_system.storage.database import db
from research_system.services.cost_tracker import cost_tracker


async def test_workflow():
    """Test Agent 1 → Agent 2 workflow."""

    project_id = "test_project_002"
    query = "attention mechanisms in transformers"

    print("="*60)
    print("AI RESEARCH SYSTEM - Agent 1 → Agent 2 Test")
    print("="*60)
    print(f"\nProject ID: {project_id}")
    print(f"Query: {query}\n")

    # Create project in database
    try:
        db.create_project(
            project_id=project_id,
            name="Test: Attention Mechanisms Research",
            domain="machine_learning",
            metadata={"test": True, "agents": ["literature_review", "idea_generation"]}
        )
    except Exception as e:
        print(f"Project might already exist: {e}\n")

    # ===== AGENT 1: Literature Review =====
    print("\n" + "="*60)
    print("AGENT 1: LITERATURE REVIEW")
    print("="*60)

    agent1 = LiteratureReviewAgent()
    agent1_input = AgentInput(
        task=query,
        context={"max_papers": 5},  # Get 5 papers for more context
        project_id=project_id,
        domain="machine_learning"
    )

    print("\n📚 Running Literature Review Agent...")
    print("-"*60)

    try:
        output1 = await agent1.execute(agent1_input)

        if output1.success:
            print(f"\n✅ Agent 1 Success!")
            print(f"   Papers found: {output1.results['paper_count']}")
            print(f"   Avg relevance: {output1.results['average_relevance']:.1f}/10")
            print(f"   Cost: ${output1.cost_usd:.4f}")
            print(f"   Tokens: {output1.tokens_used:,}")

            print("\n📚 Top 3 Papers:")
            for i, paper in enumerate(output1.results['papers'][:3], 1):
                print(f"   {i}. {paper['title'][:70]}...")
                print(f"      Relevance: {paper['relevance_score']:.1f}/10")
        else:
            print(f"\n❌ Agent 1 failed: {output1.results.get('error')}")
            return

    except Exception as e:
        print(f"\n❌ Agent 1 error: {e}")
        import traceback
        traceback.print_exc()
        return

    # ===== AGENT 2: Idea Generation =====
    print("\n" + "="*60)
    print("AGENT 2: IDEA GENERATION")
    print("="*60)

    agent2 = IdeaGenerationAgent()
    agent2_input = AgentInput(
        task="Generate novel research ideas",
        context={"num_ideas": 5},  # Generate 5 ideas
        project_id=project_id,
        domain="machine_learning"
    )

    print("\n💡 Running Idea Generation Agent...")
    print("-"*60)

    try:
        output2 = await agent2.execute(agent2_input)

        if output2.success:
            print(f"\n✅ Agent 2 Success!")
            print(f"   Ideas generated: {output2.results['idea_count']}")
            print(f"   Avg novelty: {output2.results['average_novelty']:.1f}/10")
            print(f"   Avg feasibility: {output2.results['average_feasibility']:.1f}/10")
            print(f"   Avg impact: {output2.results['average_impact']:.1f}/10")
            print(f"   Cost: ${output2.cost_usd:.4f}")
            print(f"   Tokens: {output2.tokens_used:,}")

            print("\n💡 Top 3 Ideas:")
            for i, idea in enumerate(output2.results['ideas'][:3], 1):
                print(f"\n   {i}. {idea['title']}")
                print(f"      Overall: {idea['overall_score']:.2f}/10 | "
                      f"Novelty: {idea['novelty_score']:.1f} | "
                      f"Feasibility: {idea['feasibility_score']:.1f} | "
                      f"Impact: {idea['impact_score']:.1f}")
                print(f"      Description: {idea['description'][:100]}...")

            print(f"\n{output2.educational_notes}")

            print("\n🎯 Next Steps:")
            for step in output2.next_steps:
                print(f"   • {step}")

            print("\n📝 Files Saved:")
            for file in output2.artifacts:
                print(f"   - {file}")

        else:
            print(f"\n❌ Agent 2 failed: {output2.results.get('error')}")
            return

    except Exception as e:
        print(f"\n❌ Agent 2 error: {e}")
        import traceback
        traceback.print_exc()
        return

    # ===== SUMMARY =====
    print("\n" + "="*60)
    print("WORKFLOW SUMMARY")
    print("="*60)

    total_cost = output1.cost_usd + output2.cost_usd
    total_tokens = output1.tokens_used + output2.tokens_used

    print(f"\n📊 Total Statistics:")
    print(f"   Papers analyzed: {output1.results['paper_count']}")
    print(f"   Ideas generated: {output2.results['idea_count']}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Total cost: ${total_cost:.4f}")

    # Print budget status
    print("\n" + "="*60)
    budget = cost_tracker.get_budget_status()
    print(f"BUDGET STATUS: ${budget['spent']:.2f} / ${budget['budget']:.2f} ({budget['percent_used']:.1f}%)")
    print("="*60)

    print("\n✨ Workflow completed successfully!")
    print("\nCheck your Obsidian vault for:")
    print("   - Papers/ directory for paper summaries")
    print("   - Ideas/ directory for research ideas\n")


if __name__ == "__main__":
    asyncio.run(test_workflow())
