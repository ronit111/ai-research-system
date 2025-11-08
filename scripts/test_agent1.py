"""Simple test script for Literature Review Agent."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from research_system.agents.literature_review import LiteratureReviewAgent
from research_system.agents.base_agent import AgentInput
from research_system.storage.database import db
from research_system.services.cost_tracker import cost_tracker


async def test_literature_review():
    """Test Agent 1 with a sample query."""

    # Create a test project
    project_id = "test_project_001"
    query = "attention mechanisms in transformers"

    print("="*60)
    print("AI RESEARCH SYSTEM - Agent 1 Test")
    print("="*60)
    print(f"\nProject ID: {project_id}")
    print(f"Query: {query}\n")

    # Create project in database
    try:
        db.create_project(
            project_id=project_id,
            name="Test: Attention Mechanisms",
            domain="machine_learning",
            metadata={"test": True}
        )
    except Exception as e:
        print(f"Project might already exist: {e}")

    # Initialize agent
    agent = LiteratureReviewAgent()

    # Prepare input
    agent_input = AgentInput(
        task=query,
        context={"max_papers": 3},  # Small number for testing
        project_id=project_id,
        domain="machine_learning"
    )

    # Run agent
    print("\nRunning Literature Review Agent...")
    print("-"*60)

    try:
        output = await agent.execute(agent_input)

        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)

        if output.success:
            print(f"\n✅ Successfully reviewed {output.results['paper_count']} papers")
            print(f"📊 Average Relevance: {output.results['average_relevance']:.1f}/10")
            print(f"💰 Cost: ${output.cost_usd:.4f}")
            print(f"🔢 Tokens: {output.tokens_used:,}")

            print("\n📚 Top Papers:")
            for i, paper in enumerate(output.results['papers'], 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   Authors: {', '.join(paper['authors'][:3])}")
                print(f"   Relevance: {paper['relevance_score']:.1f}/10")
                print(f"   Year: {paper.get('year', 'N/A')}")

            print("\n💡 Key Concepts:")
            print(output.results['key_concepts'])

            print("\n📝 Files Saved:")
            for file in output.artifacts:
                print(f"   - {file}")

            print(f"\n{output.educational_notes}")

            print("\n🎯 Next Steps:")
            for step in output.next_steps:
                print(f"   • {step}")

        else:
            print(f"\n❌ Agent failed: {output.results.get('error', 'Unknown error')}")

        # Print budget status
        print("\n" + "="*60)
        budget = cost_tracker.get_budget_status()
        print(f"BUDGET STATUS: ${budget['spent']:.2f} / ${budget['budget']:.2f} ({budget['percent_used']:.1f}%)")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_literature_review())
