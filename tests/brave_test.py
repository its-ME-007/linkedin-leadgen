import asyncio
import json
import os
import sys
from pathlib import Path
import dotenv
from app.services.tavily_executive_discovery import TavilyExecutiveDiscoveryService

dotenv.load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

INPUT_FILE = Path("tests/output/extracted_signals.json")
OUTPUT_FILE = Path("tests/output/executive_discovery.json")


async def main():
    print("==============================")
    print("EXECUTIVE DISCOVERY TEST (TAVILY + GEMINI)")
    print("==============================")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    signals = data.get("signals", [])
    qualified_signals = [signal for signal in signals if signal.get("status") == "qualified"]

    # Limit to first 2 signals for quota testing
    qualified_signals = qualified_signals[:2]

    print(f"Qualified signals loaded: {len(qualified_signals)}\n")

    service = TavilyExecutiveDiscoveryService()
    all_results = []

    try:
        for index, signal in enumerate(qualified_signals, start=1):
            print(f"--- Signal {index}/{len(qualified_signals)} ---")
            print(f"Company: {signal.get('company_name')}")
            print(f"Location: {signal.get('location')}")
            print(f"Signal: {signal.get('signal_type')}\n")

            executives = await service.discover_executives(signal)

            result = {
                "signal": signal,
                "executives": executives,
                "executive_count": len(executives),
            }
            all_results.append(result)

            print(f"Executives found: {len(executives)}")
            for executive in executives:
                print(f"  - {executive.get('name')} ({executive.get('title')})")
                if executive.get('linkedin_url'):
                    print(f"    LinkedIn: {executive['linkedin_url']}")
                print(f"    Evidence URLs: {len(executive.get('evidence_urls', []))} sources")
                print(f"    Confidence: {executive.get('confidence_score', 0)}")
                print(f"    Source types: {', '.join(executive.get('source_types', []))}\n")

            # Delay between signals to avoid quota exhaustion
            if index < len(qualified_signals):
                print("[DELAY] Waiting 15s before next signal...\n")
                await asyncio.sleep(15)

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "input_signal_count": len(qualified_signals),
                "company_count": len(all_results),
                "results": all_results,
            }, f, indent=4, ensure_ascii=False, default=str)

        print("==============================")
        print("EXECUTIVE DISCOVERY COMPLETE")
        print("==============================")
        print(f"Output written to: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
