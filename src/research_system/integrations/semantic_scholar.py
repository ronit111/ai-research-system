"""Semantic Scholar API integration for paper search."""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import time


class SemanticScholarClient:
    """
    Client for Semantic Scholar Academic Graph API.

    Free tier: 100 requests per 5 minutes
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers["x-api-key"] = api_key

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using keyword query.

        Args:
            query: Search query
            limit: Maximum number of results
            fields: Fields to return (defaults to common fields)

        Returns:
            List of paper dictionaries
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "year",
                "authors",
                "url",
                "citationCount",
                "publicationDate"
            ]

        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": ",".join(fields)
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

        except requests.RequestException as e:
            print(f"Error searching Semantic Scholar: {e}")
            return []

    def get_paper_details(
        self,
        paper_id: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: Semantic Scholar paper ID
            fields: Fields to return

        Returns:
            Paper dictionary or None if not found
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "year",
                "authors",
                "url",
                "citationCount",
                "publicationDate",
                "venue",
                "citations.title",
                "citations.authors",
                "references.title"
            ]

        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": ",".join(fields)}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Error getting paper details: {e}")
            return None

    def search_with_rate_limit(
        self,
        query: str,
        limit: int = 10,
        delay: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search papers with rate limiting to avoid hitting API limits.

        Args:
            query: Search query
            limit: Maximum results
            delay: Delay between requests in seconds

        Returns:
            List of papers
        """
        # Respect rate limits: 100 req per 5 min = 1 req every 3 seconds safe
        time.sleep(delay)
        return self.search_papers(query, limit)

    @staticmethod
    def format_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Semantic Scholar paper into standard format.

        Args:
            paper: Raw paper data from API

        Returns:
            Formatted paper dictionary
        """
        authors = paper.get("authors", [])
        author_names = [a.get("name", "Unknown") for a in authors]

        return {
            "semantic_scholar_id": paper.get("paperId"),
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "authors": author_names,
            "year": paper.get("year"),
            "publication_date": paper.get("publicationDate"),
            "url": paper.get("url"),
            "citation_count": paper.get("citationCount", 0),
            "venue": paper.get("venue"),
        }
