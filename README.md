# LinkedIn Lead Engine

AI-assisted lead/opportunity discovery system.

The system starts from an ICP/search requirement, discovers relevant public expansion or hiring signals, identifies the associated company, researches the company and relevant people, and finally searches the public web for evidence-backed contact points.

## Current Architecture

```text
User / ICP
    |
    v
Opportunity Discovery
    |
    +--> LinkedIn MCP
    +--> Web Search
    +--> Web Crawler
    |
    v
Candidate Signals
    |
    v
Signal Classification
    |
    v
Company Identification
    |
    v
Company Research
    |
    +--> Apollo
    +--> LinkedIn MCP
    +--> Web Search
    |
    v
Relevant People
    |
    v
Public Contact Discovery
    |
    +--> Web Search
    +--> Web Crawler / ScrapeGraphAI
    +--> Public profile data
    |
    v
Contact Extraction + Validation
    |
    v
SQLite
    |
    v
Backend API
    |
    v
UI
```

## Database

The MVP uses SQLite.

```text
db/
├── schema.sql
├── init_db.py
├── contact_discovery.db
└── database/
    ├── connection.py
    └── repository.py
```

The current repository provides the initial write operations:

```python
create_company()
create_expansion_signal()
create_job()
create_person()
create_contact()
create_web_source()
create_contact_evidence()
```

## Development Plan

### Phase 1 — Database Layer
- [x] Define SQLite schema
- [x] Create database initialization script
- [x] Create database connection module
- [x] Implement initial create/repository functions
- [ ] Add read/update/delete functions as required
- [ ] Add database tests

### Phase 2 — Provider Interfaces
Create an abstraction between application logic and external tools.

Planned interfaces:

```text
LinkedInProvider
WebSearchProvider
CrawlerProvider
ApolloProvider
```

The application should depend on these interfaces rather than directly depending on a particular MCP/server/provider.

### Phase 3 — Opportunity Discovery
Implement:

```python
discover_opportunities(criteria)
```

Initial inputs should support things such as:

```text
location = Bangalore
signal types = expansion / GCC / new office / hiring
industry = optional
company size = optional
```

The discovery service should:
1. Generate targeted search queries.
2. Search LinkedIn posts through the LinkedIn provider.
3. Search the broader web.
4. Collect candidate posts/pages.
5. Extract possible expansion/hiring signals.
6. Deduplicate candidates.
7. Store validated signals in `expansion_signals`.

### Phase 4 — Company Identification & Research
For each useful signal:
1. Identify the company.
2. Resolve it against existing companies.
3. Create/update the company record.
4. Enrich the company using Apollo, LinkedIn and web sources.
5. Discover relevant job openings where applicable.

Target data:

```text
company
industry
size
revenue
location
description
jobs
expansion signals
sources
```

### Phase 5 — Person Discovery
Implement:

```python
find_relevant_people(company)
```

Use LinkedIn and enrichment providers to identify relevant decision makers.

Potential roles include:

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

Store people and company relationships in:

```text
people
person_company
```

### Phase 6 — Public Contact Discovery
Implement:

```python
discover_contacts(person)
```

This is separate from LinkedIn discovery.

Search the public web for publicly available contact points using:
- web search
- public company pages
- personal websites
- conference/speaker pages
- public profiles
- GitHub and other relevant public sources

Use a crawler/extraction provider such as ScrapeGraphAI where structured extraction is useful.

Store:

```text
contact_points
web_sources
contact_evidence
```

Every contact should ideally have source evidence and a confidence score.

### Phase 7 — Lead Scoring
Score opportunities/people using factors such as:
- strength of expansion signal
- Bangalore relevance
- company fit
- job/hiring activity
- decision-maker relevance
- contact confidence

Do not treat an unverified contact as verified merely because a search result contains a similar name.

### Phase 8 — API
Expose the core workflow through a backend API.

Initial endpoints can be:

```text
POST /discover
GET  /signals
GET  /companies/{id}
GET  /companies/{id}/people
GET  /people/{id}
GET  /people/{id}/contacts
```

### Phase 9 — UI
Build a minimal UI around the discovery workflow.

Initial flow:

```text
Criteria
    |
    v
Discover
    |
    v
Expansion Signals
    |
    v
Company
    |
    v
People
    |
    v
Contact Points
    |
    v
Evidence
```

Do not optimize visual design before the end-to-end workflow works.

## MVP Vertical Slice

The first end-to-end milestone should be:

```text
"Bangalore + expansion"
        |
        v
LinkedIn/Web discovery
        |
        v
Candidate post
        |
        v
Expansion signal
        |
        v
Company
        |
        v
SQLite
```

Once this works reliably, add:

```text
Company
   -> People
   -> Public Contact Discovery
   -> Evidence
```

Only after that should the full UI and sophisticated scoring be added.

## Provider Strategy

External tools are replaceable components.

### LinkedIn MCP
Primary source for LinkedIn-specific post and people discovery.

### Apollo
Company/person enrichment after a prospect has been discovered. It should not be the sole source of truth.

### Web Search / Agent-Reach
Broad public-web discovery and webpage reading.

### ScrapeGraphAI
Structured extraction and multi-page crawling when a normal search result is not enough.

### Google Maps
Optional location/office verification and enrichment. Not part of the core opportunity-discovery loop.

## Future / Optional Search Infrastructure

### Self-Hosted Search Alternative

The initial implementation will use a hosted web-search provider (currently planned around Tavily) so that Phase 3 can be developed and tested quickly.

If time permits after the core end-to-end workflow is stable, evaluate replacing or supplementing the hosted search layer with an open-source/self-hosted alternative such as `tavily-open`, potentially backed by SearXNG or another search backend.

This is explicitly a **later optimization**, not a prerequisite for the MVP.

Goals of this optional work:
- reduce dependence on paid search APIs
- provide a replaceable self-hosted search backend
- preserve the existing `WebSearchProvider` interface
- compare search quality, latency, reliability, and maintenance cost against the hosted provider

The architecture should therefore keep search-provider implementations interchangeable:

```text
WebSearchProvider
    |
    +--> TavilyProvider              # initial implementation
    |
    +--> SelfHostedSearchProvider    # future / optional
             |
             +--> tavily-open
             +--> SearXNG / other backend
```

Do not block Phase 3 development on this work. Implement the hosted provider first, then evaluate the self-hosted option once the pipeline is functioning end-to-end.

## Core Design Principle

The system should discover opportunities first rather than requiring the user to provide a company list.

Two modes can eventually be supported:

```text
Discovery Mode:
ICP -> opportunities -> companies -> people -> contacts

Enrichment Mode:
user-provided companies -> research -> people -> contacts
```

Discovery Mode is the primary MVP.

## Next Immediate Task

Implement the provider interfaces and the first discovery service:

```text
app/
├── services/
│   ├── discovery.py
│   ├── companies.py
│   ├── people.py
│   ├── contacts.py
│   ├── search.py
│   └── crawler.py
│
├── api/
└── main.py
```

The first real test should be:

```text
criteria
    -> LinkedIn/web search
    -> candidate signal
    -> expansion_signals table
```

Do not start with full agent orchestration or UI polish.
