from abc import ABC, abstractmethod
from typing import Any


class ContactProvider(ABC):

    @abstractmethod
    async def search_contact(
        self,
        name: str,
        company: str,
        linkedin_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Search for publicly available professional
        contact information for a person.
        """
        raise NotImplementedError