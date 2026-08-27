import asyncio
import json
import os
import sys
from pathlib import Path
import dotenv
from app.services.linkedin import LinkedInProvider
from app.services.executive_discovery import (
    ExecutiveDiscoveryService,
)
from app.services.brave import BraveSearchService

dotenv.load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

INPUT_FILE = Path(
    "tests/output/extracted_signals.json"
)

OUTPUT_FILE = Path(
    "tests/output/executive_discovery.json"
)

RAW_OUTPUT_DIR = Path("tests/output/raw_discovery")


def _safe_name(value):
    value = str(value or "unknown_company").strip()
    safe = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in value)
    return "_".join(safe.split()) or "unknown_company"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False, default=str)


async def _capture_raw_provider_results(linkedin, xray, service, signal):
    company = signal.get("company_name")
    location = signal.get("location")
    company_dir = RAW_OUTPUT_DIR / _safe_name(company)

    _write_json(company_dir / "signal.json", signal)

    print("\n[DEBUG] Capturing raw LinkedIn response...")
    linkedin_query = company if not location else f"{company} {location}"
    linkedin_raw = await linkedin.search_people(query=linkedin_query)
    _write_json(company_dir / "linkedin_raw.json", linkedin_raw)
    print(f"[DEBUG] LinkedIn raw response written to: {company_dir / 'linkedin_raw.json'}")

    print("[DEBUG] Capturing raw X-Ray response...")
    xray_query = service._build_xray_query(
        company=company,
        location=location,
    )
    xray_raw = await xray.search(query=xray_query)
    _write_json(company_dir / "xray_raw.json", xray_raw)
    print(f"[DEBUG] X-Ray raw response written to: {company_dir / 'xray_raw.json'}")


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
        api_key=os.getenv("BRAVE_API_KEY")
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

            await _capture_raw_provider_results(
                linkedin=linkedin,
                xray=xray,
                service=service,
                signal=signal,
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