from typing import Any

from app.services.contact_provider import ContactProvider


class ContactDiscoveryService:

    def __init__(
        self,
        contact_provider: ContactProvider,
    ):
        self.contact_provider = contact_provider

    async def discover_contact(
        self,
        executive: dict[str, Any],
    ) -> dict[str, Any]:

        name = executive.get("name")
        company = executive.get("company")
        linkedin_url = executive.get("linkedin_url")

        if not name:
            raise ValueError(
                "Executive record is missing 'name'."
            )

        if not company:
            raise ValueError(
                "Executive record is missing 'company'."
            )

        contact = await self.contact_provider.search_contact(
            name=name,
            company=company,
            linkedin_url=linkedin_url,
        )

        return {
            "executive": executive,
            "contact": contact,
        }

    async def discover_contacts(
        self,
        executives: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        results = []

        for executive in executives:

            result = await self.discover_contact(
                executive
            )

            results.append(result)

        return results