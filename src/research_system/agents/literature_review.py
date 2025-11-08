"""Literature Review Agent - Agent 1."""

from typing import List, Dict, Any
import json

from .base_agent import BaseAgent, AgentInput, AgentOutput
from ..integrations.semantic_scholar import SemanticScholarClient
from ..integrations.mcp_knowledge_graph import KnowledgeGraphClient
from ..integrations.obsidian_client import ObsidianClient
from ..storage.database import db


class LiteratureReviewAgent(BaseAgent):
    """
    Agent 1: Literature Review

    Searches academic literature, scores relevance, and builds knowledge graph.
    """

    def __init__(self):
        """Initialize Literature Review Agent."""
        super().__init__(name="LiteratureReviewAgent")
        self.scholar = SemanticScholarClient()
        self.knowledge_graph = KnowledgeGraphClient()
        self.obsidian = ObsidianClient()

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute literature review.

        Args:
            input_data: Contains research query and parameters

        Returns:
            AgentOutput with papers, summaries, and metadata
        """
        query = input_data.task
        max_papers = input_data.context.get("max_papers", 5)
        project_id = input_data.project_id

        print(f"\n📚 Searching academic literature for: '{query}'")

        # Step 1: Search Semantic Scholar
        print(f"   Searching Semantic Scholar API...")
        papers = self.scholar.search_with_rate_limit(query, limit=max_papers * 2)  # Get extra for filtering

        if not papers:
            return AgentOutput(
                success=False,
                results={"error": "No papers found"},
                educational_notes="Try a more specific or different query.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"   Found {len(papers)} candidate papers")

        # Step 2: Score relevance using Claude
        print(f"   Scoring relevance with Claude...")
        scored_papers = []
        total_tokens = 0
        total_cost = 0.0

        for paper in papers[:max_papers * 2]:  # Score more than we need
            relevance_score, tokens, cost = self._score_relevance(paper, query)
            total_tokens += tokens
            total_cost += cost

            scored_papers.append({
                **self.scholar.format_paper(paper),
                "relevance_score": relevance_score
            })

        # Step 3: Select top papers
        scored_papers.sort(key=lambda p: p["relevance_score"], reverse=True)
        top_papers = scored_papers[:max_papers]

        print(f"   Selected top {len(top_papers)} papers (avg relevance: {sum(p['relevance_score'] for p in top_papers) / len(top_papers):.1f}/10)")

        # Step 4: Save to database
        for paper in top_papers:
            db.add_paper(
                arxiv_id=paper["semantic_scholar_id"],
                title=paper["title"],
                authors=paper["authors"],
                abstract=paper["abstract"],
                project_id=project_id,
                relevance_score=paper["relevance_score"],
                published_date=paper.get("publication_date"),
                pdf_url=paper.get("url")
            )

        # Step 5: Extract concepts and build knowledge graph
        print(f"   Extracting key concepts...")
        concepts = self._extract_concepts(top_papers, query)
        concepts_text, concept_tokens, concept_cost = concepts
        total_tokens += concept_tokens
        total_cost += concept_cost

        # Step 6: Save summaries to Obsidian
        print(f"   Saving to Obsidian vault...")
        saved_files = []
        for paper in top_papers:
            try:
                file_path = self.obsidian.save_paper_summary(
                    paper_id=paper["semantic_scholar_id"],
                    title=paper["title"],
                    authors=paper["authors"],
                    abstract=paper["abstract"],
                    relevance_score=paper["relevance_score"]
                )
                saved_files.append(str(file_path))
            except Exception as e:
                print(f"   Warning: Could not save {paper['title']}: {e}")

        # Generate educational notes
        educational_notes = self._generate_educational_notes(top_papers, concepts_text, query)

        return AgentOutput(
            success=True,
            results={
                "papers": top_papers,
                "paper_count": len(top_papers),
                "key_concepts": concepts_text,
                "query": query,
                "average_relevance": sum(p["relevance_score"] for p in top_papers) / len(top_papers)
            },
            artifacts=saved_files,
            metadata={
                "search_query": query,
                "total_candidates": len(papers),
                "selected_count": len(top_papers)
            },
            educational_notes=educational_notes,
            next_steps=[
                "Review the papers in your Obsidian vault",
                "Run Idea Generation Agent to identify research opportunities",
                "Explore key concepts in the knowledge graph"
            ],
            tokens_used=total_tokens,
            cost_usd=total_cost
        )

    def _score_relevance(self, paper: Dict[str, Any], query: str) -> tuple[float, int, float]:
        """
        Score paper relevance to query using Claude.

        Args:
            paper: Paper dictionary
            query: Research query

        Returns:
            Tuple of (relevance_score, tokens_used, cost)
        """
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        if not abstract:
            return 3.0, 0, 0.0  # Default low score if no abstract

        prompt = f"""Rate the relevance of this paper to the research query on a scale of 1-10.

Research Query: "{query}"

Paper Title: {title}

Abstract: {abstract}

Consider:
- How directly does it address the query?
- Is it a seminal work in the field?
- Does it provide useful methods or insights?

Respond with ONLY a number from 1-10, nothing else."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=10)

        try:
            score = float(response.strip())
            score = max(1.0, min(10.0, score))  # Clamp to 1-10
        except ValueError:
            score = 5.0  # Default if parsing fails

        return score, tokens, cost

    def _extract_concepts(self, papers: List[Dict[str, Any]], query: str) -> tuple[str, int, float]:
        """
        Extract key concepts from papers using Claude.

        Args:
            papers: List of paper dictionaries
            query: Research query

        Returns:
            Tuple of (concepts_text, tokens_used, cost)
        """
        # Create summary of abstracts
        abstracts_summary = "\n\n".join([
            f"Paper {i+1}: {p['title']}\n{p['abstract'][:300]}..."
            for i, p in enumerate(papers[:5])  # Use top 5 papers
        ])

        prompt = f"""Analyze these research papers and identify 5-10 key concepts, methods, or themes.

Research Query: "{query}"

Papers:
{abstracts_summary}

List the key concepts as a bullet-point list. Be specific and use domain terminology.
Focus on concepts that connect multiple papers or are central to the research area."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=500)

        return response, tokens, cost

    def _generate_educational_notes(
        self,
        papers: List[Dict[str, Any]],
        concepts: str,
        query: str
    ) -> str:
        """
        Generate educational notes for the user.

        Args:
            papers: Selected papers
            concepts: Extracted concepts
            query: Research query

        Returns:
            Formatted educational notes
        """
        return self.format_educational_note(f"""
**What just happened:**

I searched Semantic Scholar's database of 200M+ academic papers for your query: "{query}"

**Process:**
1. Retrieved {len(papers)} candidate papers
2. Used Claude to score each paper's relevance (1-10 scale)
3. Selected the top {len(papers)} most relevant papers
4. Extracted key concepts that connect these papers
5. Saved everything to your Obsidian vault and knowledge graph

**Key Concepts Identified:**
{concepts}

**Why this matters:**
These papers form the foundation of your research. They represent:
- Current state of the art
- Common methods and approaches
- Open problems and research gaps

**Next step:** Review the papers in your Obsidian vault. Pay special attention to:
- Methodology sections (how they solved problems)
- Limitations sections (what they couldn't solve)
- Future work sections (research opportunities)
""")
