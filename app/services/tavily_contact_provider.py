import os
import re
from typing import Any

import httpx

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

        # Build a targeted public-web search.
        #
        # We deliberately do NOT infer an email address from
        # company naming conventions. Any returned contact point
        # must be supported by actual search-result content.

        query_parts = [
            f'"{name}"',
            f'"{company}"',
            '(email OR contact OR phone OR "contact information")',
        ]

        if linkedin_url:
            query_parts.append(
                f'"{linkedin_url}"'
            )

        query = " ".join(query_parts)

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": 10,
            "include_answer": False,
            "include_raw_content": True,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                "https://api.tavily.com/search",
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            [],
        )

        email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )

        phone_pattern = re.compile(
            r"(?<!\d)"
            r"(?:\+?\d[\d .()\-\u00a0]{7,}\d)"
            r"(?!\d)"
        )

        emails: list[str] = []
        phones: list[str] = []
        evidence: list[dict[str, Any]] = []

        for result in results:

            title = result.get(
                "title"
            ) or ""

            url = result.get(
                "url"
            ) or ""

            content = (
                result.get("raw_content")
                or result.get("content")
                or ""
            )

            searchable_text = (
                f"{title}\n{content}"
            )

            found_emails = (
                email_pattern.findall(
                    searchable_text
                )
            )

            found_phones = (
                phone_pattern.findall(
                    searchable_text
                )
            )

            for email in found_emails:

                if email.lower() not in {
                    existing.lower()
                    for existing in emails
                }:
                    emails.append(email)

            for phone in found_phones:

                normalized = re.sub(
                    r"\s+",
                    " ",
                    phone,
                ).strip()

                if normalized not in phones:
                    phones.append(
                        normalized
                    )

            if (
                found_emails
                or found_phones
            ):

                evidence.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": result.get(
                            "content"
                        ),
                        "emails": found_emails,
                        "phones": found_phones,
                    }
                )

        email = (
            emails[0]
            if emails
            else None
        )

        phone = (
            phones[0]
            if phones
            else None
        )

        # Conservative confidence:
        #
        # 0.8 -> explicit contact point found
        # 0.2 -> relevant search results but no contact point
        # 0.0 -> no results
        #
        # This is NOT a verification score. RocketReach or another
        # verifier can be added later.

        if email or phone:
            confidence = 0.8

        elif results:
            confidence = 0.2

        else:
            confidence = 0.0

        return {
            "name": name,
            "company": company,
            "linkedin_url": linkedin_url,
            "email": email,
            "phone": phone,
            "source": "tavily",
            "confidence": confidence,
            "evidence": evidence,
            "query": query,
            "result_count": len(results),
        }