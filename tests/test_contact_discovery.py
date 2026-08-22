import asyncio
import json
from pathlib import Path

from app.services.contact_discovery import (
    ContactDiscoveryService,
)
from app.services.contact_provider import (
    ContactProvider,
)


INPUT_FILE = Path(
    "tests/output/executive_discovery.json"
)

OUTPUT_FILE = Path(
    "tests/output/contact_discovery.json"
)


class MockContactProvider(ContactProvider):

    async def search_contact(
        self,
        name,
        company,
        linkedin_url=None,
    ):

        return {
            "name": name,
            "company": company,
            "linkedin_url": linkedin_url,
            "email": None,
            "phone": None,
            "source": "mock",
            "confidence": None,
            "evidence": [],
        }


async def main():

    print("==============================")
    print("CONTACT DISCOVERY TEST")
    print("==============================")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    executives = []

    for result in data.get("results", []):

        signal = result.get(
            "signal",
            {},
        )

        company = signal.get(
            "company_name"
        )

        for executive in result.get(
            "executives",
            [],
        ):

            # Phase 2 records may not currently
            # contain company directly.
            #
            # Phase 3 normalizes that dependency here.

            executive = {
                **executive,
                "company": company,
            }

            executives.append(
                executive
            )

    print(
        f"Executives loaded: "
        f"{len(executives)}"
    )

    provider = MockContactProvider()

    service = ContactDiscoveryService(
        contact_provider=provider
    )

    results = (
        await service.discover_contacts(
            executives
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "input_executive_count": len(
                    executives
                ),
                "contact_count": len(
                    results
                ),
                "results": results,
            },
            f,
            indent=4,
            ensure_ascii=False,
            default=str,
        )

    print(
        f"Contacts discovered: "
        f"{len(results)}"
    )

    print(
        f"Output written to: "
        f"{OUTPUT_FILE}"
    )

    print("==============================")
    print("CONTACT DISCOVERY COMPLETE")
    print("==============================")


if __name__ == "__main__":
    asyncio.run(main())