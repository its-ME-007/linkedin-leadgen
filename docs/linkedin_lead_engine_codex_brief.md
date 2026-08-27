# LinkedIn Lead Engine — Codex Development Brief

## Goal

Build an AI-assisted lead/opportunity discovery system for finding companies showing expansion/GCC/new-office/hiring signals in Bangalore/Bengaluru, identifying relevant decision-makers, and discovering evidence-backed public contact points.

Primary workflow:

```text
ICP
 -> opportunity/signal discovery
 -> company
 -> executive discovery
 -> contact discovery
 -> evidence/verification
 -> lead scoring
 -> SQLite/API/UI
```

## Three-Phase Model

### Phase 1 — Signal Extraction / Opportunity Discovery

Input:

```text
location = Bangalore/Bengaluru
signal types = office expansion / GCC / new office / hiring
industry = optional
company size = optional
```

Output:

```text
candidate posts/pages
 -> qualified signal
 -> company
```

Example signal:

```json
{
  "signal_type": "office_expansion",
  "company_name": "SAP",
  "location": "Bangalore",
  "intent": "completed",
  "confidence": 1.0,
  "status": "qualified",
  "evidence": {
    "text": "...",
    "reason": "..."
  },
  "source": "linkedin",
  "source_url": null,
  "discovery_query": "..."
}
```

Important business rule:

```text
actively looking/evaluating office space > planned/in-progress expansion > completed opening
```

A completed office opening is still a useful signal, but may mean the original office transaction has already happened.

### Phase 2 — Executive Discovery

Input: qualified signal.

Output: relevant executives.

Target roles:

```text
CEO / Founder
Country Head
India Head
APAC Head
CTO
VP Engineering
Engineering Director
Strategy / Expansion leadership
```

Current conceptual pipeline:

```text
Signal
 -> LinkedIn people search
 -> web/X-Ray search
 -> candidate normalization
 -> role matching
 -> tier/confidence ranking
 -> executives
```

LinkedIn is primary for LinkedIn-specific people discovery; web/X-Ray is supplementary.

### Phase 3 — Contact Discovery

Input: executive.

Output:

```text
email / phone / public contact point
+ source evidence
+ confidence
+ verification status
```

Current direction:

```text
Executive
 -> Tavily/public-web discovery
 -> candidate contact
 -> verification if required
```

Apollo is a possible alternative/fallback because it could potentially cover both Phase 2 and Phase 3. RocketReach may be added later for verification.

Do not treat an inferred email as publicly sourced or verified.

---

# Critical Current Idea: LinkedIn Content Search

The LinkedIn MCP being used is:

```text
mcp-server-linkedin@latest
```

It exposes a `search_posts` capability in addition to `search_people`.

This should be tested as the primary Phase 1 discovery mechanism.

Instead of:

```text
search_people("Bangalore office expansion")
```

for opportunity discovery, test:

```text
search_posts("Bangalore office expansion")
search_posts("Bengaluru new office")
search_posts("Bangalore GCC")
search_posts("Bengaluru GCC expansion")
search_posts("Bangalore office opening")
search_posts("Bengaluru new campus")
search_posts("Bangalore office space")
search_posts("Bengaluru expansion")
```

Desired architecture:

```text
ICP / criteria
      |
      v
LinkedIn search_posts()
      |
      v
Candidate Posts
      |
      v
Signal Extraction
      |
      v
Company
      |
      v
Executive Discovery
      |
      v
Contact Discovery
```

Before changing the architecture, directly test the MCP's actual `search_posts` behavior and save its raw response.

Determine:
- exact parameters
- result structure
- recency support
- pagination
- whether it really searches post content globally
- how well it handles location/company keywords

---

# Existing LinkedIn Provider Issue

There is an implementation mismatch to investigate.

The provider has a method conceptually like:

```python
async def search_people(self, query, limit=20):
    result = await self.session.call_tool(
        "search_people",
        {
            "keywords": query,
        },
    )
```

The `limit` argument may not actually be passed to the MCP.

Meanwhile executive discovery may call:

```python
await self.linkedin.search_people(
    f"{company} {location}",
    limit=40,
)
```

If the adapter ignores `limit`, asking for 40 does not guarantee 40 MCP results.

Fix/verify this before concluding LinkedIn discovery quality is poor.

Do not redesign ranking until the raw candidate pool is known to be correct.

---

# Debugging Strategy

Always preserve raw provider responses while debugging.

Current test structure:

```text
tests/output/raw_discovery/
    <company>/
        signal.json
        linkedin_raw.json
        xray_raw.json
```

Capture raw results before parsing/ranking.

This lets us distinguish:

```text
candidate absent from provider
```

from:

```text
candidate returned by provider
but discarded downstream
```

Never remove this debugging capability.

---

# Brave Search Findings

Brave Search API is used for web/X-Ray discovery.

A practical finding from testing:

```text
count=50
```

caused a 422 for Web Search, while:

```text
count=20
```

worked.

Do not use `count=50`. If more results are needed, use the API's supported pagination mechanism.

Google-oriented searches can be attempted through Brave's `!g` bang, e.g.:

```text
!g site:linkedin.com/in/ "SAP" "Bangalore" -intitle:"profiles"
```

Normal Brave search and `!g` Google search can be compared as separate discovery strategies.

---

# Current Executive Discovery Test

The test loads:

```text
tests/output/extracted_signals.json
```

and selects:

```python
signal.get("status") == "qualified"
```

It initializes:

```python
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
```

Then:

```python
await linkedin.connect()
```

and:

```python
executives = await service.discover_executives(signal)
```

Final results go to:

```text
tests/output/executive_discovery.json
```

Raw provider results go to:

```text
tests/output/raw_discovery/
```

---

# Current Phase 3 Test

Tavily contact testing reads:

```text
tests/output/executive_discovery.json
```

It extracts executives from each result and passes:

```python
provider.search_contact(
    name=executive.get("name"),
    company=executive.get("company") or executive.get("company_name"),
    linkedin_url=executive.get("linkedin_url"),
)
```

So Phase 3 intentionally consumes Phase 2 output.

Current unit expectations include:

- contact data found -> extract email/phone and confidence
- results with no contact data -> low confidence
- no results -> zero confidence

Live Tavily output should be written separately for inspection.

---

# Provider Architecture

External tools are replaceable.

Application logic should depend on service/provider abstractions.

Relevant components:

```text
LinkedInProvider
BraveSearchService
TavilyContactProvider
ApolloProvider (optional)
CrawlerProvider
```

SearXNG and Brave are replaceable web-search implementations.

Tavily is currently being evaluated mainly for Phase 3.

An open-source Tavily-compatible alternative was considered but is a later/time-permitting change. Do not prioritize it now.

---

# Database

MVP uses SQLite:

```text
db/
├── schema.sql
├── init_db.py
└── database/
    ├── connection.py
    └── repository.py
```

Existing repository writes include:

```python
create_company()
create_expansion_signal()
create_job()
create_person()
create_contact()
create_web_source()
create_contact_evidence()
```

Eventually add read/update/delete functions and tests as required.

---

# API

There is an `api/routes.py` and main application entrypoint.

Planned endpoints:

```text
POST /discover
GET  /signals
GET  /companies/{id}
GET  /companies/{id}/people
GET  /people/{id}
GET  /people/{id}/contacts
```

Keep routes thin. Orchestration belongs in services, not provider-specific logic inside routes.

Keep `main.py` thin as well.

---

# Roadmap

## Phase 1

```text
ICP
 -> LinkedIn content search
 -> web search
 -> candidate posts/pages
 -> signal extraction
 -> qualified signal
 -> company
```

Immediate priority: test pure LinkedIn `search_posts` with realistic Bangalore expansion queries.

## Phase 2

```text
company
 -> LinkedIn people search
 + web/X-Ray search
 -> executives
```

First fix/verify provider limits and inspect raw responses.

## Phase 3

```text
executive
 -> Tavily/public web
 -> candidate contact
 -> evidence
 -> verification if needed
```

Apollo/RocketReach can be added later.

## Phase 4

Lead scoring using:

```text
signal strength
Bangalore relevance
company fit
hiring activity
executive relevance
contact confidence
```

Never equate unverified contacts with verified contacts.

## Phase 5

API.

## Phase 6

Minimal UI.

Do not polish UI before the end-to-end workflow works.

---

# MVP Vertical Slice

First reliable milestone:

```text
"Bangalore + expansion"
        |
        v
LinkedIn content search
        |
        v
Candidate post
        |
        v
Signal extraction
        |
        v
Company
        |
        v
SQLite
```

Then:

```text
Company
 -> People
 -> Public Contact Discovery
 -> Evidence
```

Only afterward add sophisticated scoring/UI.

---

# Engineering Rules

1. Providers are replaceable.
2. Keep raw evidence/results.
3. Separate discovery from verification.
4. Signal intent matters.
5. Discover opportunities before people.
6. Do not over-engineer prematurely.
7. Test providers independently.
8. When results are wrong, isolate provider -> query -> raw response -> parser -> ranking.
9. Preserve interfaces while swapping providers.
10. Prefer evidence-backed quality over raw result volume.

---

# Immediate Coding Tasks

## A. Verify LinkedIn MCP content search

Directly test:

```text
search_posts("Bangalore office expansion")
search_posts("Bengaluru new office")
search_posts("Bangalore GCC")
search_posts("Bengaluru expansion")
```

Save raw responses.

Determine exact tool contract, result structure, recency and pagination behavior.

## B. Compare with Brave

Run equivalent searches and save raw results.

Compare LinkedIn raw content with Brave raw content.

## C. Fix LinkedIn people-search limit handling

Confirm whether:

```python
search_people(..., limit=40)
```

actually produces more results.

Implement correct adapter behavior according to the real MCP contract.

## D. Only then adjust ExecutiveDiscoveryService

Do not rewrite parsing/ranking until the raw candidate pool is known to be correct.

---

# Desired End State

```text
                  USER / ICP
                      |
                      v
              OPPORTUNITY DISCOVERY
                      |
          +-----------+-----------+
          |                       |
          v                       v
   LinkedIn content          Web search
       search                 / crawler
          |                       |
          +-----------+-----------+
                      |
                      v
              SIGNAL EXTRACTION
                      |
                      v
                   COMPANY
                      |
                      v
             EXECUTIVE DISCOVERY
                      |
          +-----------+-----------+
          |                       |
          v                       v
       LinkedIn              X-Ray/Web
       people                  search
          |                       |
          +-----------+-----------+
                      |
                      v
                 EXECUTIVES
                      |
                      v
              CONTACT DISCOVERY
                      |
          +-----------+-----------+
          |                       |
          v                       v
       Tavily                  Apollo
     / public web             (optional)
          |                       |
          +-----------+-----------+
                      |
                      v
              CONTACT EVIDENCE
                      |
                      v
                VERIFICATION
                      |
                      v
                 LEAD SCORE
                      |
                      v
                   SQLite
                      |
                      v
                 API / UI
```

## Bottom Line

Do not rewrite the whole system.

First verify and improve the existing LinkedIn MCP integration, especially `search_posts`, because pure LinkedIn content search may be a much better Phase 1 opportunity-discovery mechanism than inferring opportunities from person search or relying entirely on Brave X-Ray.

Then stabilize Phase 2 executive discovery, then complete Phase 3 contact discovery.

Keep the architecture provider-agnostic throughout.
