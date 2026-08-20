# Tests

This directory contains integration and component-level tests for the LinkedIn Lead Generation Engine.

The tests are designed to validate the pipeline incrementally, without requiring the entire system to be operational at once.

---

## Test Structure

    tests/
    ├── README.md
    ├── test_linkedin_connection.py
    ├── test_discovery.py
    ├── test_signal_extractor.py
    └── output/
        ├── discovery_results.json
        └── extracted_signals.json

---

## Testing Philosophy

The project is being developed as a staged pipeline.

Each stage should be tested independently before moving to the next stage.

    LinkedIn MCP
         ↓
    Discovery
         ↓
    Raw Discovery Results
         ↓
    Signal Extraction / Classification
         ↓
    Qualified Signals
         ↓
    Company Research
         ↓
    Person Research
         ↓
    Contact Discovery

The tests preserve intermediate outputs so that downstream components can be developed without repeatedly querying external services.

---

# 1. LinkedIn Connection Test

### File

    test_linkedin_connection.py

### Purpose

Validates that the application can:

- Start the LinkedIn MCP server
- Establish an MCP client session
- Initialize the session
- Discover the available MCP tools
- Execute a basic LinkedIn search
- Close the MCP session correctly

### Run

    python -m tests.test_linkedin_connection

### Expected behavior

The test should establish a connection similar to:

    Connected to LinkedIn MCP server.

and display the available LinkedIn MCP tools.

A successful search should return a completed MCP response.

---

# 2. Discovery Test

### File

    test_discovery.py

### Purpose

Tests the `DiscoveryService`.

The discovery layer is responsible for generating searches based on the requested signal type and sending those searches to:

- LinkedIn MCP
- Web search

For example:

    {
        "location": "Bangalore",
        "signal_types": [
            "office_expansion"
        ],
        "industry": "technology"
    }

The discovery service expands this into multiple search queries using the signal grammar.

### Current Signal Grammar

The discovery layer currently supports:

    office_expansion
    new_facility
    market_expansion
    hiring_expansion

Each signal type contains:

- Phrase-based queries
- Hashtag-based queries

Example:

    "new office" "Bangalore" "technology"

    #OfficeExpansion Bangalore technology

    #GCC Bangalore technology

### Run

    python -m tests.test_discovery

### Output

The test stores the raw discovery response in:

    tests/output/discovery_results.json

This file contains:

    criteria
    result_count
    results

Each normalized discovery result contains:

    {
        "source": "linkedin",
        "signal_type": "office_expansion",
        "query": "\"new office\" \"Bangalore\" \"technology\"",
        "raw_result": "..."
    }

The raw response is intentionally preserved because the exact MCP response structure is required when developing downstream extraction logic.

---

# 3. Signal Extraction Test

### File

    test_signal_extractor.py

### Purpose

Tests the first filtering/classification layer after discovery.

It does NOT query LinkedIn again.

Instead, it reads:

    tests/output/discovery_results.json

and passes those results to:

    SignalExtractor

This allows the classifier to be repeatedly modified and tested against the same discovery dataset.

### Run

    python -m tests.test_signal_extractor

### Output

Qualified signals are written to:

    tests/output/extracted_signals.json

The output contains:

    input_result_count
    qualified_signal_count
    signals

A qualified signal currently follows this structure:

    {
        "signal_type": "office_expansion",
        "company_name": "Example Corp",
        "location": "Bangalore",
        "confidence": 0.91,
        "status": "qualified",
        "evidence": "...",
        "source": "linkedin",
        "source_url": "...",
        "discovery_query": "..."
    }

---

# Test Data Flow

The intended development workflow is:

    LinkedIn MCP
         │
         ▼
    test_discovery.py
         │
         ▼
    discovery_results.json
         │
         ▼
    test_signal_extractor.py
         │
         ▼
    extracted_signals.json

This separation is intentional.

Once `discovery_results.json` has been generated, the signal classifier can be developed offline without repeatedly consuming LinkedIn searches.

---

# External Dependencies

The LinkedIn connection and discovery tests require the LinkedIn MCP server to be available.

The current provider starts it using:

    uvx mcp-server-linkedin@latest

The LinkedIn MCP authentication profile must already be configured on the development machine.

The signal extraction test does NOT require an active LinkedIn connection because it works from the saved discovery output.

---

# Recommended Testing Order

Run the tests in this order.

### Step 1 — Verify MCP

    python -m tests.test_linkedin_connection

### Step 2 — Generate Discovery Data

    python -m tests.test_discovery

This updates:

    tests/output/discovery_results.json

### Step 3 — Test Classification

    python -m tests.test_signal_extractor

This updates:

    tests/output/extracted_signals.json

---

# Why Intermediate JSON Files Are Kept

The raw discovery output is useful for debugging the boundary between the external search systems and our internal pipeline.

It allows us to inspect:

- Search quality
- LinkedIn MCP response structure
- Duplicate results
- False positives
- Relevant expansion signals
- Missing company information
- Missing location information
- Source URLs
- Author information

The saved data also provides a reproducible dataset for improving the signal classifier.

---

# Current Scope

The tests currently cover:

    ✓ LinkedIn MCP connection
    ✓ LinkedIn MCP search
    ✓ Discovery query generation
    ✓ LinkedIn discovery
    ✓ Web-search interface stub
    ✓ Discovery result normalization
    ✓ Discovery result persistence
    ✓ Signal classification
    ✓ Signal filtering
    ✓ Signal persistence

The following stages are NOT yet covered:

    □ Company research
    □ Company profile enrichment
    □ Person discovery
    □ Decision-maker identification
    □ Web credential discovery
    □ Contact evidence
    □ Lead scoring
    □ Database persistence
    □ End-to-end lead generation

These will be added as the corresponding services are implemented.

---

# Important Development Rule

When modifying a pipeline stage, prefer testing it against the saved output of the previous stage.

For example:

    Discovery changes
            ↓
    Regenerate discovery_results.json
            ↓
    Signal extractor tests

but:

    Signal extractor changes
            ↓
    Do NOT repeatedly query LinkedIn
            ↓
    Use discovery_results.json

This keeps development faster, reproducible, and easier to debug.

---

# Future Test Structure

As the project grows, the test directory is expected to evolve toward:

    tests/
    ├── README.md
    │
    ├── test_linkedin_connection.py
    ├── test_discovery.py
    ├── test_signal_extractor.py
    ├── test_company_research.py
    ├── test_person_research.py
    ├── test_contact_discovery.py
    ├── test_lead_scoring.py
    │
    ├── fixtures/
    │   ├── discovery_results.json
    │   ├── linkedin_posts.json
    │   └── company_profiles.json
    │
    └── output/
        ├── discovery_results.json
        ├── extracted_signals.json
        └── ...

The `fixtures/` directory can eventually contain stable test datasets, while `output/` remains useful for generated debugging artifacts.

For now, do NOT create the `fixtures/` directory unless we intentionally freeze a representative dataset for regression testing.