import os
from typing import Any

from app.services.contact_provider import ContactProvider


class TavilyContactProvider(ContactProvider):

    def __init__(
        self,
        api_key: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("TAVILY_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY is not configured."
            )

    async def search_contact(
        self,
        name: str,
        company: str,
        linkedin_url: str | None = None,
    ) -> dict[str, Any]:

        # TODO:
        # Implement Tavily API call here.
        #
        # Search should be constructed from:
        #   - person's name
        #   - company
        #   - optionally LinkedIn URL
        #
        # Example conceptual query:
        #
        #   "Person Name" "Company Name"
        #   email OR contact OR "@company.com"
        #
        # Do NOT infer an email address here.
        # Return only information supported by
        # the search results.

        return {
            "name": name,
            "company": company,
            "linkedin_url": linkedin_url,
            "email": None,
            "phone": None,
            "source": "tavily",
            "confidence": None,
            "evidence": [],
        }