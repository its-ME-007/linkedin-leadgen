"""
Full end-to-end pipeline test:
LinkedIn Discovery → Signal Extraction → Executive Discovery → Employee Names
"""

import asyncio
import json
from pathlib import Path
import sys
import dotenv

from app.services.signal_extractor import SignalExtractor
from app.services.tavily_executive_discovery import TavilyExecutiveDiscoveryService

dotenv.load_dotenv()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


async def main():
    print("=" * 70)
    print("FULL PIPELINE TEST: Discovery → Signals → Executives")
    print("=" * 70)

    # ========================================
    # Stage 1: Load discovery results
    # ========================================
    print("\n[STAGE 1] Loading discovery results...")

    discovery_file = Path("tests/output/discovery_results.json")
    if not discovery_file.exists():
        print(f"ERROR: Discovery file not found: {discovery_file}")
        return

    with open(discovery_file, "r", encoding="utf-8") as f:
        discovery_data = json.load(f)

    discovery_results = discovery_data.get("results", [])
    print(f"✓ Loaded {len(discovery_results)} discovery results")

    # ========================================
    # Stage 2: Signal extraction
    # ========================================
    print("\n[STAGE 2] Extracting signals from discovery results...")

    extractor = SignalExtractor()
    signals = await extractor.extract(discovery_results)

    qualified_signals = [
        s for s in signals
        if s.get("status") == "qualified"
    ]

    print(f"✓ Extracted {len(signals)} signals")
    print(f"✓ Qualified signals: {len(qualified_signals)}")

    if not qualified_signals:
        print("ERROR: No qualified signals found")
        return

    # Save extracted signals
    signals_output = Path("tests/output/extracted_signals_pipeline_test.json")
    signals_output.parent.mkdir(parents=True, exist_ok=True)
    with open(signals_output, "w", encoding="utf-8") as f:
        json.dump({
            "input_result_count": len(discovery_results),
            "retained_signal_count": len(signals),
            "qualified_signal_count": len(qualified_signals),
            "signals": signals,
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"✓ Signals saved to: {signals_output}")

    # ========================================
    # Stage 3: Executive discovery
    # ========================================
    print("\n[STAGE 3] Discovering executives from signals...")

    # Limit to first signal to test full pipeline
    test_signal = qualified_signals[0]
    print(f"\nProcessing signal: {test_signal.get('company_name')}")
    print(f"  Location: {test_signal.get('location')}")
    print(f"  Type: {test_signal.get('signal_type')}")

    service = TavilyExecutiveDiscoveryService()

    try:
        executives = await service.discover_executives(test_signal)

        print(f"\n✓ Executive discovery complete")
        print(f"✓ Found {len(executives)} executives")

        if executives:
            print("\nExecutives discovered:")
            for i, exec_data in enumerate(executives, 1):
                print(f"\n  {i}. {exec_data.get('name')}")
                print(f"     Title: {exec_data.get('title')}")
                print(f"     LinkedIn: {exec_data.get('linkedin_url', 'N/A')}")
                print(f"     Evidence sources: {len(exec_data.get('evidence_urls', []))}")
                print(f"     Confidence: {exec_data.get('confidence_score', 0)}")
                print(f"     Source types: {', '.join(exec_data.get('source_types', []))}")
                print(f"     Evidence: {exec_data.get('evidence_text', '')[:100]}...")

        # ========================================
        # Stage 4: Save full pipeline output
        # ========================================
        print("\n[STAGE 4] Saving full pipeline output...")

        output_file = Path("tests/output/full_pipeline_result.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        pipeline_output = {
            "pipeline_stages": {
                "stage_1_discovery": {
                    "input_results": len(discovery_results),
                    "status": "complete",
                },
                "stage_2_signal_extraction": {
                    "input_signals": len(signals),
                    "qualified_signals": len(qualified_signals),
                    "status": "complete",
                },
                "stage_3_executive_discovery": {
                    "input_signal": test_signal.get("company_name"),
                    "executives_found": len(executives),
                    "status": "complete",
                },
            },
            "test_signal": test_signal,
            "discovered_executives": executives,
            "summary": {
                "total_qualified_signals": len(qualified_signals),
                "executives_discovered_sample": len(executives),
                "pipeline_status": "SUCCESS" if executives else "SUCCESS (0 executives - valid)",
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(pipeline_output, f, indent=2, ensure_ascii=False, default=str)

        print(f"✓ Full pipeline output saved to: {output_file}")

        # ========================================
        # Summary
        # ========================================
        print("\n" + "=" * 70)
        print("PIPELINE TEST COMPLETE")
        print("=" * 70)
        print(f"Stage 1 (Discovery):      ✓ {len(discovery_results)} results")
        print(f"Stage 2 (Signals):        ✓ {len(qualified_signals)} qualified signals")
        print(f"Stage 3 (Executives):     ✓ {len(executives)} executives found")
        print(f"\nOutput files:")
        print(f"  - Signals:        {signals_output}")
        print(f"  - Full pipeline:  {output_file}")
        print("=" * 70)

    except Exception as e:
        print(f"\nERROR in executive discovery: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
