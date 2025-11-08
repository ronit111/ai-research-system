"""MCP Knowledge Graph integration wrapper."""

from typing import List, Dict, Any, Optional


class KnowledgeGraphClient:
    """
    Wrapper for MCP Knowledge Graph operations.

    Uses the aim_* MCP tools that are available in Claude Code.
    """

    def __init__(self, context: str = "ai-research"):
        """
        Initialize knowledge graph client.

        Args:
            context: Knowledge graph database context
        """
        self.context = context

    def add_paper(
        self,
        paper_id: str,
        title: str,
        authors: List[str],
        abstract: str,
        year: Optional[int] = None,
        url: Optional[str] = None
    ) -> None:
        """
        Add a paper entity to the knowledge graph.

        Args:
            paper_id: Unique paper identifier
            title: Paper title
            authors: List of author names
            abstract: Paper abstract
            year: Publication year
            url: Paper URL
        """
        # Note: This will be called via MCP tools in actual execution
        # For now, we'll create a structure that agents can use
        observations = [
            f"Title: {title}",
            f"Authors: {', '.join(authors)}",
            f"Abstract: {abstract[:200]}..." if len(abstract) > 200 else f"Abstract: {abstract}"
        ]

        if year:
            observations.append(f"Year: {year}")
        if url:
            observations.append(f"URL: {url}")

        # This would be called via MCP in actual execution:
        # aim_create_entities({
        #     "context": self.context,
        #     "entities": [{
        #         "name": paper_id,
        #         "entityType": "paper",
        #         "observations": observations
        #     }]
        # })

        return {
            "context": self.context,
            "entity": {
                "name": paper_id,
                "entityType": "paper",
                "observations": observations
            }
        }

    def add_concept(self, concept_name: str, description: str) -> None:
        """
        Add a concept entity to the knowledge graph.

        Args:
            concept_name: Name of the concept
            description: Concept description
        """
        return {
            "context": self.context,
            "entity": {
                "name": concept_name,
                "entityType": "concept",
                "observations": [description]
            }
        }

    def link_paper_to_concept(self, paper_id: str, concept: str) -> None:
        """
        Create relationship between paper and concept.

        Args:
            paper_id: Paper identifier
            concept: Concept name
        """
        return {
            "context": self.context,
            "relation": {
                "from": paper_id,
                "to": concept,
                "relationType": "mentions"
            }
        }

    def link_papers_citation(self, citing_paper: str, cited_paper: str) -> None:
        """
        Create citation relationship between papers.

        Args:
            citing_paper: Paper that cites
            cited_paper: Paper being cited
        """
        return {
            "context": self.context,
            "relation": {
                "from": citing_paper,
                "to": cited_paper,
                "relationType": "cites"
            }
        }

    def search_papers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for papers in knowledge graph.

        Args:
            query: Search query

        Returns:
            List of matching papers
        """
        # This would be called via MCP:
        # aim_search_nodes({"context": self.context, "query": query})

        return {
            "context": self.context,
            "query": query
        }

    def get_paper_concepts(self, paper_id: str) -> List[str]:
        """
        Get concepts mentioned in a paper.

        Args:
            paper_id: Paper identifier

        Returns:
            List of concept names
        """
        # This would query the graph for all concepts linked to paper
        return {
            "context": self.context,
            "paper_id": paper_id,
            "query_type": "concepts"
        }

    def get_related_papers(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Get papers related through citations or shared concepts.

        Args:
            paper_id: Paper identifier

        Returns:
            List of related papers
        """
        return {
            "context": self.context,
            "paper_id": paper_id,
            "query_type": "related_papers"
        }
