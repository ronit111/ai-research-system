"""Idea Generation Agent - Agent 2."""

from typing import List, Dict, Any, Optional
import json

from .base_agent import BaseAgent, AgentInput, AgentOutput
from ..storage.database import db
from ..integrations.obsidian_client import ObsidianClient
from ..integrations.mcp_knowledge_graph import KnowledgeGraphClient


class IdeaGenerationAgent(BaseAgent):
    """
    Agent 2: Idea Generation

    Analyzes literature to identify research gaps and generate novel ideas.
    Scores ideas by novelty, feasibility, and potential impact.
    """

    # Scoring weights
    NOVELTY_WEIGHT = 0.35
    FEASIBILITY_WEIGHT = 0.35
    IMPACT_WEIGHT = 0.30

    # Analysis limits
    MAX_PAPERS_FOR_GAPS = 10
    MAX_PAPERS_FOR_SCORING = 5
    MAX_ENTITY_NAME_LENGTH = 50

    def __init__(self):
        """Initialize Idea Generation Agent."""
        super().__init__(name="IdeaGenerationAgent")
        self.obsidian = ObsidianClient()
        self.knowledge_graph = KnowledgeGraphClient()

    def _sanitize_for_prompt(self, text: str, max_length: int = 500) -> str:
        """
        Sanitize text for use in LLM prompts to prevent injection.

        Args:
            text: Text to sanitize
            max_length: Maximum length to truncate to

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove non-printable characters except newlines and tabs
        sanitized = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."

        return sanitized

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute idea generation.

        Args:
            input_data: Contains project_id and optional context

        Returns:
            AgentOutput with generated ideas, scores, and metadata
        """
        project_id = input_data.project_id
        domain = input_data.domain
        num_ideas = input_data.context.get("num_ideas", 7)

        if not project_id:
            return AgentOutput(
                success=False,
                results={"error": "project_id required"},
                educational_notes="Agent 2 needs papers from Agent 1 to generate ideas.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"\n💡 Generating research ideas for project: {project_id}")

        # Step 1: Load papers from database
        print(f"   Loading papers from database...")
        papers = db.get_papers(project_id)

        if not papers:
            return AgentOutput(
                success=False,
                results={"error": "No papers found for this project"},
                educational_notes="Run Agent 1 (Literature Review) first to gather papers.",
                tokens_used=0,
                cost_usd=0.0
            )

        print(f"   Found {len(papers)} papers from literature review")

        # Step 2: Analyze papers for research gaps
        print(f"   Analyzing research gaps and limitations...")
        gaps_analysis, tokens_gaps, cost_gaps = self._analyze_research_gaps(papers, domain)

        # Step 3: Generate research ideas
        print(f"   Generating {num_ideas} novel research ideas...")
        ideas_raw, tokens_ideas, cost_ideas = self._generate_ideas(
            papers, gaps_analysis, domain, num_ideas
        )

        # Step 4: Parse and structure ideas
        ideas = self._parse_ideas(ideas_raw)

        if not ideas:
            return AgentOutput(
                success=False,
                results={"error": "Failed to generate valid ideas"},
                educational_notes="The LLM output was malformed. Try again.",
                tokens_used=tokens_gaps + tokens_ideas,
                cost_usd=cost_gaps + cost_ideas
            )

        # Step 5: Score each idea
        print(f"   Scoring ideas for novelty, feasibility, and impact...")
        scored_ideas = []
        total_tokens = tokens_gaps + tokens_ideas
        total_cost = cost_gaps + cost_ideas

        for i, idea in enumerate(ideas, 1):
            print(f"   Scoring idea {i}/{len(ideas)}...")
            scores, tokens, cost = self._score_idea(idea, papers, domain)
            total_tokens += tokens
            total_cost += cost

            scored_ideas.append({
                **idea,
                "novelty_score": scores["novelty"],
                "feasibility_score": scores["feasibility"],
                "impact_score": scores["impact"],
                "overall_score": scores["overall"]
            })

        # Step 6: Rank ideas
        scored_ideas.sort(key=lambda x: x["overall_score"], reverse=True)

        # Step 7: Save to Obsidian
        print(f"   Saving ideas to Obsidian vault...")
        try:
            ideas_file = self.obsidian.save_research_ideas(
                project_id=project_id,
                domain=domain,
                ideas=scored_ideas,
                gaps_analysis=gaps_analysis
            )
            artifacts = [str(ideas_file)]
        except Exception as e:
            print(f"   Warning: Could not save to Obsidian: {e}")
            artifacts = []

        # TODO: Step 8: Save to knowledge graph (MCP integration)
        # Will be implemented in Phase 2 when MCP client is fully integrated

        # Generate educational notes
        educational_notes = self._generate_educational_notes(
            scored_ideas, gaps_analysis, len(papers)
        )

        # Calculate averages safely (avoid division by zero)
        idea_count = len(scored_ideas)
        avg_novelty = sum(i["novelty_score"] for i in scored_ideas) / idea_count if idea_count else 0.0
        avg_feasibility = sum(i["feasibility_score"] for i in scored_ideas) / idea_count if idea_count else 0.0
        avg_impact = sum(i["impact_score"] for i in scored_ideas) / idea_count if idea_count else 0.0

        return AgentOutput(
            success=True,
            results={
                "ideas": scored_ideas,
                "idea_count": idea_count,
                "gaps_analysis": gaps_analysis,
                "top_idea": scored_ideas[0] if scored_ideas else None,
                "average_novelty": avg_novelty,
                "average_feasibility": avg_feasibility,
                "average_impact": avg_impact
            },
            artifacts=artifacts,
            metadata={
                "project_id": project_id,
                "domain": domain,
                "papers_analyzed": len(papers),
                "ideas_generated": len(scored_ideas)
            },
            educational_notes=educational_notes,
            next_steps=[
                "Review the top 3 ideas in your Obsidian vault",
                "Select 1-2 ideas for hypothesis formation (Agent 3)",
                "Consider resource requirements before proceeding",
                "Discuss ideas with domain experts for validation"
            ],
            tokens_used=total_tokens,
            cost_usd=total_cost
        )

    def _analyze_research_gaps(
        self,
        papers: List[Dict[str, Any]],
        domain: str
    ) -> tuple[str, int, float]:
        """
        Analyze papers to identify research gaps and limitations.

        Args:
            papers: List of paper dictionaries from database
            domain: Research domain

        Returns:
            Tuple of (gaps_analysis_text, tokens_used, cost)
        """
        # Prepare paper summaries (sanitized)
        paper_summaries = []
        for paper in papers[:self.MAX_PAPERS_FOR_GAPS]:
            # Sanitize inputs to prevent prompt injection
            title = self._sanitize_for_prompt(paper.get('title', ''), 200)
            abstract = self._sanitize_for_prompt(paper.get('abstract', ''), 400)
            authors = ', '.join(paper.get('authors', [])[:3])

            summary = f"""
Title: {title}
Authors: {authors}
Abstract: {abstract}
Relevance: {paper.get('relevance_score', 0):.1f}/10
"""
            paper_summaries.append(summary)

        papers_text = "\n\n---\n\n".join(paper_summaries)
        sanitized_domain = self._sanitize_for_prompt(domain, 50)

        prompt = f"""Analyze these research papers from the {sanitized_domain} domain and identify research gaps, limitations, and open problems.

Papers:
{papers_text}

Please identify:
1. **Explicit Limitations**: What do the papers say they couldn't solve or didn't address?
2. **Implicit Gaps**: What's missing from the current approaches?
3. **Contradictions**: Do papers disagree on any findings or methods?
4. **Scalability Issues**: What prevents these methods from scaling?
5. **Open Questions**: What questions do the papers raise for future work?

Format your response as a structured analysis with clear sections.
Be specific and cite which papers mentioned each limitation/gap."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=1500)

        return response, tokens, cost

    def _generate_ideas(
        self,
        papers: List[Dict[str, Any]],
        gaps_analysis: str,
        domain: str,
        num_ideas: int
    ) -> tuple[str, int, float]:
        """
        Generate novel research ideas based on gaps analysis.

        Args:
            papers: List of paper dictionaries
            gaps_analysis: Research gaps analysis from previous step
            domain: Research domain
            num_ideas: Number of ideas to generate

        Returns:
            Tuple of (ideas_json_text, tokens_used, cost)
        """
        prompt = f"""Based on the research gaps identified, generate {num_ideas} novel research ideas for the {domain} domain.

Research Gaps Analysis:
{gaps_analysis}

For each idea, provide:
1. **Title**: Concise, descriptive title (max 100 chars)
2. **Description**: Detailed explanation of the idea (2-3 sentences)
3. **Approach**: High-level method or approach to pursue this idea
4. **Why Novel**: What makes this idea different from existing work?
5. **Potential Impact**: What problem would this solve?
6. **Resources Needed**: Data, compute, expertise, time estimates
7. **Risks**: What could go wrong?

Format your response as a JSON array of objects with these exact keys:
- title
- description
- approach
- why_novel
- potential_impact
- resources_needed
- risks

Example format:
[
  {{
    "title": "Example Research Idea",
    "description": "This idea proposes...",
    "approach": "We would use X method to...",
    "why_novel": "Unlike existing work which...",
    "potential_impact": "This could solve...",
    "resources_needed": "Dataset X, GPU cluster, ML expertise, 3-6 months",
    "risks": "May not generalize to..."
  }}
]

Respond with ONLY valid JSON, no other text."""

        response, tokens, cost = self.call_llm(prompt, max_tokens=3000)

        return response, tokens, cost

    def _parse_ideas(self, ideas_raw: str) -> List[Dict[str, Any]]:
        """
        Parse JSON ideas from LLM response.

        Args:
            ideas_raw: Raw LLM response

        Returns:
            List of parsed idea dictionaries
        """
        try:
            # Try to extract JSON from response
            ideas_raw = ideas_raw.strip()

            # Sometimes LLM wraps JSON in ```json ... ```
            if ideas_raw.startswith("```"):
                lines = ideas_raw.split("\n")
                ideas_raw = "\n".join(lines[1:-1])  # Remove first and last line

            ideas = json.loads(ideas_raw)

            if not isinstance(ideas, list):
                print(f"   Warning: Expected list, got {type(ideas)}")
                return []

            # Validate each idea has required keys
            required_keys = ["title", "description", "approach", "why_novel",
                           "potential_impact", "resources_needed", "risks"]

            valid_ideas = []
            for idea in ideas:
                if all(key in idea for key in required_keys):
                    valid_ideas.append(idea)
                else:
                    print(f"   Warning: Idea missing keys: {idea.get('title', 'Unknown')}")

            return valid_ideas

        except json.JSONDecodeError as e:
            print(f"   Error parsing ideas JSON: {e}")
            print(f"   Raw response: {ideas_raw[:200]}...")
            return []

    def _score_idea(
        self,
        idea: Dict[str, Any],
        papers: List[Dict[str, Any]],
        domain: str
    ) -> tuple[Dict[str, float], int, float]:
        """
        Score an idea for novelty, feasibility, and impact.

        Args:
            idea: Idea dictionary
            papers: Reference papers
            domain: Research domain

        Returns:
            Tuple of (scores_dict, tokens_used, cost)
        """
        # Create abbreviated paper list for context (sanitized)
        paper_titles = [
            self._sanitize_for_prompt(p.get("title", ""), 100)
            for p in papers[:self.MAX_PAPERS_FOR_SCORING]
        ]
        papers_context = "\n".join([f"- {t}" for t in paper_titles])

        # Sanitize idea fields
        sanitized_domain = self._sanitize_for_prompt(domain, 50)
        sanitized_title = self._sanitize_for_prompt(idea.get('title', ''), 150)
        sanitized_description = self._sanitize_for_prompt(idea.get('description', ''), 300)
        sanitized_approach = self._sanitize_for_prompt(idea.get('approach', ''), 300)
        sanitized_why_novel = self._sanitize_for_prompt(idea.get('why_novel', ''), 300)

        prompt = f"""Score this research idea across three dimensions on a scale of 1-10.

Domain: {sanitized_domain}

Idea:
**Title**: {sanitized_title}
**Description**: {sanitized_description}
**Approach**: {sanitized_approach}
**Why Novel**: {sanitized_why_novel}

Context - Existing Papers:
{papers_context}

Score the idea on:

1. **Novelty** (1-10): How original/unique is this idea?
   - 1-3: Incremental/obvious extension
   - 4-6: Moderate novelty, combines existing ideas
   - 7-9: Highly novel, new perspective
   - 10: Groundbreaking, paradigm-shifting

2. **Feasibility** (1-10): Can this be realistically accomplished?
   - 1-3: Requires unavailable resources/impossible
   - 4-6: Challenging but possible with effort
   - 7-9: Feasible with standard resources
   - 10: Easy to implement immediately

3. **Impact** (1-10): How significant would success be?
   - 1-3: Minor improvement
   - 4-6: Useful contribution to field
   - 7-9: Major advancement
   - 10: Revolutionary breakthrough

Respond with ONLY three numbers separated by commas (novelty,feasibility,impact).
Example: 7.5,6.0,8.5"""

        response, tokens, cost = self.call_llm(prompt, max_tokens=50)

        try:
            scores_str = response.strip()
            novelty, feasibility, impact = map(float, scores_str.split(","))

            # Clamp scores
            novelty = max(1.0, min(10.0, novelty))
            feasibility = max(1.0, min(10.0, feasibility))
            impact = max(1.0, min(10.0, impact))

            # Calculate overall score (weighted average using class constants)
            overall = (novelty * self.NOVELTY_WEIGHT +
                      feasibility * self.FEASIBILITY_WEIGHT +
                      impact * self.IMPACT_WEIGHT)

            return {
                "novelty": novelty,
                "feasibility": feasibility,
                "impact": impact,
                "overall": overall
            }, tokens, cost

        except (ValueError, AttributeError) as e:
            print(f"   Warning: Could not parse scores: {e}")
            # Return middle-of-road scores
            return {
                "novelty": 5.0,
                "feasibility": 5.0,
                "impact": 5.0,
                "overall": 5.0
            }, tokens, cost

    def _generate_educational_notes(
        self,
        ideas: List[Dict[str, Any]],
        gaps_analysis: str,
        num_papers: int
    ) -> str:
        """
        Generate educational notes for the user.

        Args:
            ideas: List of generated ideas with scores
            gaps_analysis: Research gaps analysis
            num_papers: Number of papers analyzed

        Returns:
            Formatted educational notes
        """
        top_3_titles = [idea["title"] for idea in ideas[:3]]
        idea_count = len(ideas)
        avg_novelty = sum(i["novelty_score"] for i in ideas) / idea_count if idea_count else 0.0
        avg_feasibility = sum(i["feasibility_score"] for i in ideas) / idea_count if idea_count else 0.0

        return self.format_educational_note(f"""
**What just happened:**

I analyzed {num_papers} papers from your literature review and identified research gaps, limitations, and open problems in the field. Then I generated {idea_count} novel research ideas to address these gaps.

**Process:**
1. Analyzed papers for explicit limitations and implicit gaps
2. Generated {idea_count} research ideas targeting these gaps
3. Scored each idea for novelty (originality), feasibility (doability), and impact (importance)
4. Ranked ideas by overall score (weighted: {self.NOVELTY_WEIGHT*100:.0f}% novelty, {self.FEASIBILITY_WEIGHT*100:.0f}% feasibility, {self.IMPACT_WEIGHT*100:.0f}% impact)

**Top 3 Ideas:**
1. {top_3_titles[0] if len(top_3_titles) > 0 else 'N/A'}
2. {top_3_titles[1] if len(top_3_titles) > 1 else 'N/A'}
3. {top_3_titles[2] if len(top_3_titles) > 2 else 'N/A'}

**Quality Metrics:**
- Average Novelty: {avg_novelty:.1f}/10
- Average Feasibility: {avg_feasibility:.1f}/10

**Scoring Philosophy:**
- **High Novelty + High Feasibility** = Best ideas (innovative but achievable)
- **High Novelty + Low Feasibility** = Long-term moonshots
- **Low Novelty + High Feasibility** = Safe incremental work

**Why this matters:**
These ideas represent *opportunities* identified by analyzing what current research hasn't solved. The top-ranked ideas balance being novel (interesting) with being feasible (you can actually do them).

**Next step:** Review the ideas in your Obsidian vault. Pick 1-2 that excite you and align with your resources. Agent 3 will help you convert these into testable hypotheses.

**Pro tip:** Don't just chase high novelty scores. A feasible idea with moderate novelty that you can actually complete is better than a groundbreaking idea that's impossible.
""")
