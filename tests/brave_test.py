import asyncio
import json
import os
from pathlib import Path

from app.services.linkedin import LinkedInProvider
from app.services.executive_discovery import (
    ExecutiveDiscoveryService,
)
from app.services.brave import BraveSearchService


INPUT_FILE = Path(
    "tests/output/extracted_signals.json"
)

OUTPUT_FILE = Path(
    "tests/output/executive_discovery.json"
)


async def main():

    print("==============================")
    print("EXECUTIVE DISCOVERY TEST")
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

    signals = data.get(
        "signals",
        [],
    )

    qualified_signals = [
        signal
        for signal in signals
        if signal.get("status") == "qualified"
    ]

    print(
        f"Qualified signals loaded: "
        f"{len(qualified_signals)}"
    )

    linkedin = LinkedInProvider(
        ["uvx", "mcp-server-linkedin@latest"]
    )

    xray = BraveSearchService(
        api_key=os.environ["BRAVE_API_KEY"]
    )

    service = ExecutiveDiscoveryService(
        linkedin_provider=linkedin,
        web_search_service=xray,
    )

    all_results = []

    try:

        print("\nConnecting to LinkedIn MCP...")

        await linkedin.connect()

        print("Connected.\n")

        for index, signal in enumerate(
            qualified_signals,
            start=1,
        ):

            print(
                "\n------------------------------"
            )

            print(
                f"Signal {index}/"
                f"{len(qualified_signals)}"
            )

            print(
                f"Company: "
                f"{signal.get('company_name')}"
            )

            print(
                f"Signal: "
                f"{signal.get('signal_type')}"
            )

            executives = (
                await service.discover_executives(
                    signal
                )
            )

            result = {
                "signal": signal,
                "executives": executives,
                "executive_count": len(
                    executives
                ),
            }

            all_results.append(
                result
            )

            print(
                f"\nExecutives found: "
                f"{len(executives)}"
            )

            for executive in executives:

                print(
                    f"  [{executive.get('tier')}] "
                    f"{executive.get('name')} "
                    f"| "
                    f"{executive.get('role')}"
                )

                print(
                    f"      Headline: "
                    f"{executive.get('headline')}"
                )

                print(
                    f"      LinkedIn: "
                    f"{executive.get('linkedin_url')}"
                )

                print(
                    f"      Matched title: "
                    f"{executive.get('matched_title')}"
                )

                print(
                    f"      Confidence: "
                    f"{executive.get('confidence')}"
                )

                print(
                    f"      Source: "
                    f"{executive.get('source')}"
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
                    "input_signal_count": len(
                        qualified_signals
                    ),
                    "company_count": len(
                        all_results
                    ),
                    "results": all_results,
                },
                f,
                indent=4,
                ensure_ascii=False,
                default=str,
            )

        print(
            "\n=============================="
        )

        print(
            "EXECUTIVE DISCOVERY COMPLETE"
        )

        print(
            "=============================="
        )

        print(
            f"Output written to: "
            f"{OUTPUT_FILE}"
        )

    finally:

        print(
            "\nClosing LinkedIn MCP..."
        )

        await linkedin.close()

        print("Closed.")


if __name__ == "__main__":
    asyncio.run(main())