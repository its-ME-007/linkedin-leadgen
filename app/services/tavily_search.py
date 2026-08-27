"""Tavily web search service for executive discovery."""

import os
import httpx


class TavilySearchService:
    """Web search service using Tavily API.
    
    Implements the search(query) interface expected by ExecutiveDiscoveryService.
    """

    def __init__(self, api_key: str | None = None):
        """Initialize with Tavily API key.
        
        Args:
            api_key: Tavily API key. If not provided, loads from TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY is not configured. "
                "Provide api_key parameter or set TAVILY_API_KEY environment variable."
            )

    async def search(self, query: str):
        """Search the web using Tavily API.
        
        Args:
            query: Search query string
            
        Returns:
            dict with "results" key containing list of search results
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "max_results": 20,
            "include_answer": False,
            "include_raw_content": False,  # Don't need raw content for executive discovery
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
            )

        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])

        return {"results": results}
