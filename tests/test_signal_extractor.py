import json
from pathlib import Path

from app.services.signal_extractor import SignalExtractor


def main():

    # ----------------------------------------
    # Load saved discovery output
    # ----------------------------------------

    input_file = Path(
        "tests/output/discovery_results.json"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Discovery output not found: {input_file}"
        )

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as f:

        discovery_data = json.load(f)

    discovery_results = discovery_data.get(
        "results",
        []
    )

    print("==============================")
    print("SIGNAL EXTRACTION TEST")
    print("==============================")

    print(
        f"Discovery results loaded: "
        f"{len(discovery_results)}"
    )

    # ----------------------------------------
    # Run extractor
    # ----------------------------------------

    extractor = SignalExtractor()

    signals = extractor.extract(
        discovery_results
    )

    # ----------------------------------------
    # Classify retained signals by status
    # ----------------------------------------

    qualified_signals = [
        signal
        for signal in signals
        if signal.get("status") == "qualified"
    ]

    enrichment_signals = [
        signal
        for signal in signals
        if signal.get("status") == "needs_enrichment"
    ]

    # ----------------------------------------
    # Save extracted signals
    # ----------------------------------------

    output_dir = Path(
        "tests/output"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "extracted_signals.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "input_result_count": len(
                    discovery_results
                ),

                "retained_signal_count": len(
                    signals
                ),

                "qualified_signal_count": len(
                    qualified_signals
                ),

                "needs_enrichment_count": len(
                    enrichment_signals
                ),

                "signals": signals,
            },
            f,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    # ----------------------------------------
    # Print summary
    # ----------------------------------------

    print(
        f"\nRetained signals: "
        f"{len(signals)}"
    )

    print(
        f"Qualified signals: "
        f"{len(qualified_signals)}"
    )

    print(
        f"Needs enrichment: "
        f"{len(enrichment_signals)}"
    )

    print(
        f"Output written to: "
        f"{output_file}"
    )

    # ----------------------------------------
    # Print signals
    # ----------------------------------------

    for index, signal in enumerate(
        signals,
        start=1
    ):

        print(
            f"\n--- Signal {index} ---"
        )

        print(
            f"Type: "
            f"{signal.get('signal_type')}"
        )

        print(
            f"Status: "
            f"{signal.get('status')}"
        )

        print(
            f"Company: "
            f"{signal.get('company_name')}"
        )

        print(
            f"Location: "
            f"{signal.get('location')}"
        )

        print(
            f"Intent: "
            f"{signal.get('intent')}"
        )

        print(
            f"Confidence: "
            f"{signal.get('confidence')}"
        )

        print(
            f"Source: "
            f"{signal.get('source')}"
        )

        print(
            f"URL: "
            f"{signal.get('source_url')}"
        )

        print(
            f"Discovery query: "
            f"{signal.get('discovery_query')}"
        )

        # ----------------------------------------
        # Evidence
        # ----------------------------------------

        evidence = signal.get(
            "evidence",
            {}
        )

        if isinstance(evidence, dict):
            evidence_text = evidence.get(
                "text",
                ""
            )
        else:
            evidence_text = str(
                evidence
            )

        print(
            f"Evidence: "
            f"{evidence_text[:300]}"
        )



        # ----------------------------------------
        # Recency
        # ----------------------------------------

        recency = signal.get(
            "recency"
        )

        if isinstance(recency, dict):

            print(
                f"Published at: "
                f"{recency.get('published_at')}"
            )

            print(
                f"Age days: "
                f"{recency.get('age_days')}"
            )

    # ----------------------------------------
    # Completion
    # ----------------------------------------

    print(
        "\n=============================="
    )

    print(
        "SIGNAL EXTRACTION COMPLETE"
    )

    print(
        "=============================="
    )


if __name__ == "__main__":
    main()