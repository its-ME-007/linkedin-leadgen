import asyncio
import json
from pathlib import Path

from app.services.linkedin import LinkedInProvider
from app.services.discovery import DiscoveryService


class WebSearchStub:
    """
    Temporary web-search implementation.

    Replace this with the real WebSearchService later.
    """

    def search(self, query):
        print(f"[WEB SEARCH] {query}")
        return []


async def main():

    linkedin = LinkedInProvider(
        ["uvx", "mcp-server-linkedin@latest"]
    )

    web_search = WebSearchStub()

    discovery = DiscoveryService(
        linkedin_provider=linkedin,
        web_search_service=web_search
    )

    try:

        print("Connecting to LinkedIn MCP...")
        await linkedin.connect()

        print("Connected.\n")

        criteria = {
            "location": "Bangalore",
            "signal_types": [
                "office_expansion"
            ],
            "industry": "technology"
        }

        print("Discovery criteria:")
        print(criteria)

        print("\nStarting discovery...\n")

        results = await discovery.discover_opportunities(
            criteria
        )

        # --------------------------------
        # Write results to JSON
        # --------------------------------

        output_dir = Path("tests/output")
        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            output_dir / "discovery_results.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "criteria": criteria,
                    "result_count": len(results),
                    "results": results
                },
                f,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        # --------------------------------
        # Terminal summary
        # --------------------------------

        print("\n==============================")
        print("DISCOVERY COMPLETE")
        print("==============================")

        print(
            f"Results returned: {len(results)}"
        )

        print(
            f"Output written to: {output_file}"
        )

        for index, result in enumerate(
            results,
            start=1
        ):

            print(
                f"\n[{index}] "
                f"{result['source']} | "
                f"{result['signal_type']}"
            )

            print(
                f"Query: {result['query']}"
            )

    finally:

        print(
            "\nClosing LinkedIn MCP..."
        )

        await linkedin.close()

        print("Closed.")


if __name__ == "__main__":
    asyncio.run(main())