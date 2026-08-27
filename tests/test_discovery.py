import asyncio
import json
from pathlib import Path

from app.services.linkedin import LinkedInProvider
from app.services.discovery import DiscoveryService, LinkedInDiscoveryConfig


async def main():

    linkedin = LinkedInProvider(
        ["uvx", "mcp-server-linkedin@latest"]
    )

    discovery = DiscoveryService(
        linkedin_provider=linkedin,
        config=LinkedInDiscoveryConfig(
            raw_output_dir=Path("tests/output/raw_discovery"),
        ),
    )

    try:

        print("Connecting to LinkedIn MCP...")
        await linkedin.connect()

        print("Connected.\n")

        criteria = {
            "location": "Bengaluru",
            "signal_types": [
                "commercial_property_requirement"
            ],
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
                f"Hashtag: {result['discovery_query']}"
            )

    finally:

        print(
            "\nClosing LinkedIn MCP..."
        )

        await linkedin.close()

        print("Closed.")


if __name__ == "__main__":
    asyncio.run(main())
