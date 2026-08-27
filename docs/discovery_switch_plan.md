# Discovery-to-People Switch Plan

Status: prepared, not implemented.

This plan is based on the validated LinkedIn requirement-post grammar in
`docs/claude_notes.md` and the architectural constraints in
`docs/linkedin_lead_engine_codex_brief.md`.

## Target behavior

The default waterfall should be:

```text
ICP criteria
  -> LinkedIn post/web discovery
  -> raw candidate persistence
  -> signal extraction and qualification
  -> company upsert
  -> people/executive discovery
  -> people upsert
  -> API response / person search UI
```

Contact discovery must not run as part of that default waterfall. It should be
an explicit, idempotent action initiated from a person card, for example:

```text
POST /api/people/{person_id}/discover-contact
  -> contact provider
  -> contact point + evidence persistence
  -> updated contact response
```

## Implementation sequence

1. Reconcile the request contract across `static/index.html`, `routes.py`,
   `DiscoveryService`, `PipelineOrchestrator`, and `SignalExtractor`.
2. Add a `commercial_property_requirement` grammar based on the confirmed
   phrase/spec pattern:
   requirement phrases AND (`sq ft`/`carpet area`/`frontage`/similar), with
   location and industry templating, plus supply-side exclusions.
3. Preserve raw provider payloads and normalize provider result lists before
   extraction; do not lose the source query or source URL.
4. Fix the orchestration contract so the pipeline passes one criteria object
   to discovery and handles missing providers explicitly.
5. Initialize and close the LinkedIn provider through application lifespan or a
   provider manager; never silently use `None` for the primary discovery source.
6. Make the waterfall stop after people persistence. Remove contact discovery
   from `process_signal` and expose it only through the person action route.
7. Add person search endpoints (by name, title, company, and location) and a
   response shape suitable for the UI; add a UI search/filter control and a
   per-person “Find contact” action.
8. Persist contact evidence against the specific contact point instead of
   creating unattached web sources.
9. Add focused tests for query generation, orchestration order, no-contact
   default behavior, person persistence/search, and explicit contact action.
10. Run the provider-independent test suite, then perform a live provider pass
    with raw responses saved under `tests/output/raw_discovery/`.

## API shape after the switch

```text
POST /api/discover
GET  /api/signals
GET  /api/signals/{signal_id}
GET  /api/companies/{company_id}
GET  /api/companies/{company_id}/people
GET  /api/people/search?q=&company_id=&location=&title=
GET  /api/people/{person_id}
GET  /api/people/{person_id}/contacts
POST /api/people/{person_id}/discover-contact
GET  /api/contacts/{contact_id}
```

`POST /api/discover` should return run-level counts and IDs/statuses, while the
UI reads persisted signals, companies, and people through query endpoints.
The contact action should return only the requested person's contact result and
never trigger contact searches for other people.

## Acceptance criteria

- A discovery run can complete through stored people without a contact
  provider or contact API key.
- The default run performs zero contact-provider calls.
- A person card can trigger exactly one contact search for that person and show
  persisted results/evidence afterward.
- The UI's submitted signal values are recognized by the backend.
- Discovery, extraction, people persistence, and person search each have
  independently testable service/API boundaries.
- Raw provider responses remain available for debugging and audit.

## UI wrapper update

The static wrapper now treats location as the primary search control and
submits the commercial-property requirement signal by default. The main action
is labeled as the discovery waterfall and renders persisted people as cards.
Each card exposes a `Find public contact` button that calls the explicit contact
route only when clicked; contact resolution is not performed while rendering a
waterfall result.

## Current API critique snapshot (2026-08-26)

The current routes expose most read operations, but the write path is not yet a
working waterfall:

- `POST /api/discover` constructs a pipeline, but
  `PipelineOrchestrator.run_full_pipeline` calls discovery with keyword
  arguments while `DiscoveryService.discover_opportunities` accepts one
  `criteria` dictionary. The first run therefore fails before discovery.
- The API explicitly sets `linkedin_provider = None`, so the primary LinkedIn
  content-search provider is never used by the live route.
- The executive service is wired with web-search providers only; the LinkedIn
  people-search branch described in the brief is not connected.
- `process_signal` currently invokes contact discovery for every persisted
  person. This violates the desired optional contact route and makes a contact
  provider a hidden dependency of the default run.
- `/api/people/{person_id}` and `/api/companies/{company_id}/people` exist, but
  there is no person-search endpoint and the UI has no person-search control.
  The current UI only loads people indirectly after fetching signals.
- The contact action calls the provider and `ContactService` upserts contact
  points, but evidence URLs are saved without being linked through
  `create_contact_evidence`; the evidence chain is therefore incomplete.
- Provider instances are created per request and the LinkedIn MCP lifecycle is
  not managed by FastAPI lifespan. A long-running or queued waterfall needs a
  provider manager and explicit cleanup.
- The route is synchronous from the client's perspective and has no run ID,
  progress state, retry boundary, or resumability. A production waterfall
  should return a run/job identifier and expose run status, even if the first
  implementation executes inline.
- Request/UI signal names (`NEW_STORE`, `EXEC_MOVE`, `FUNDING`) do not match the
  discovery grammar keys, so the current form does not select valid discovery
  queries.
