from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional

from db.database import repository

# Service imports for wiring
from app.services.provider_factory import create_providers
from app.services.discovery import DiscoveryService
from app.services.executive_discovery import ExecutiveDiscoveryService
from app.services.companies import CompanyService
from app.services.people import PeopleService
from app.services.contacts import ContactService
from app.services.pipeline import PipelineOrchestrator

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================


class DiscoveryRequest(BaseModel):
    location: str
    signal_types: list[str] = []
    industry: Optional[str] = None
    company_size: Optional[str] = None


# ============================================================
# HELPERS
# ============================================================


def row_to_dict(row):
    """
    Convert sqlite3.Row / dict-like objects into
    JSON-serializable dictionaries.
    """

    if row is None:
        return None

    if isinstance(row, dict):
        return row

    return dict(row)


def rows_to_dict(rows):
    return [
        row_to_dict(row)
        for row in rows
    ]


# ============================================================
# HEALTH
# ============================================================


@router.get("/health")
async def health():
    return {
        "status": "ok"
    }


# ============================================================
# DISCOVERY
# ============================================================


@router.post("/discover")
async def discover(request: DiscoveryRequest):
    """
    Entry point for opportunity discovery.

    The actual discovery orchestration will remain inside
    DiscoveryService. The API should not directly call
    Brave/SearXNG/LinkedIn/etc.
    """

    providers = create_providers()
    
    # Initialize services
    # LinkedIn MCP is optional and asynchronous to connect
    linkedin_provider = providers.get("linkedin")
    if not linkedin_provider:
        raise HTTPException(
            status_code=503,
            detail=(
                "LinkedIn discovery is not configured. Set "
                "LINKEDIN_MCP_ENABLED=true and ensure uvx is available."
            ),
        )
    linkedin_connected = False
    if linkedin_provider:
        try:
            await linkedin_provider.connect()
            linkedin_connected = True
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"LinkedIn provider unavailable: {exc}",
            ) from exc
    
    discovery = DiscoveryService(
        linkedin_provider=linkedin_provider,
        web_search_service=None
    )
    
    exec_discovery = ExecutiveDiscoveryService(
        web_search_services=providers.get("web_search_list", []),
    )
    
    company_service = CompanyService(
        web_search_services=providers.get("web_search_list", [])
    )
    
    people_service = PeopleService(
        executive_discovery_service=exec_discovery
    )
    
    contact_service = ContactService(
        contact_provider=providers.get("tavily")
    )
    
    pipeline = PipelineOrchestrator(
        discovery_service=discovery,
        signal_extractor=providers.get("signal_extractor"),
        company_service=company_service,
        people_service=people_service,
        contact_service=contact_service
    )
    
    try:
        results = await pipeline.run_full_pipeline(request.model_dump())
        print(
            "[API][discover] completed: "
            f"raw={results.get('raw_posts_found', 0)} "
            f"signals={results.get('signals_extracted', 0)} "
            f"companies={results.get('companies_processed', 0)} "
            f"people={results.get('people_discovered', 0)} "
            f"errors={len(results.get('errors', []))}"
        )

        if results.get("errors"):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Discovery waterfall failed",
                    "errors": results["errors"],
                    "results": results,
                },
            )

        return {
            "status": "success",
            "results": results
        }
    finally:
        if linkedin_connected:
            await linkedin_provider.close()


@router.get("/discovery/state")
async def get_discovery_state(
    location: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    """Return the current persisted waterfall state for the UI."""
    signals = (
        repository.get_signals_by_location(location)
        if location
        else repository.get_all_signals(limit=limit)
    )[:limit]

    company_ids = {
        signal["company_id"]
        for signal in signals
        if signal["company_id"] is not None
    }
    companies = []
    people = []
    for company_id in company_ids:
        company = repository.get_company(company_id)
        if company:
            companies.append(row_to_dict(company))
        people.extend(
            row_to_dict(person)
            for person in repository.get_people_by_company(company_id)
        )

    return {
        "location": location,
        "counts": {
            "signals": len(signals),
            "companies": len(companies),
            "people": len(people),
        },
        "signals": rows_to_dict(signals),
        "companies": companies,
        "people": people,
    }


# ============================================================
# EXPANSION SIGNALS
# ============================================================


@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int):

    signal = repository.get_expansion_signal(
        signal_id
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Expansion signal not found",
        )

    return row_to_dict(signal)


@router.get("/signals")
async def get_signals(
    location: Optional[str] = None,
    company_id: Optional[int] = None,
):

    if company_id is not None:

        signals = repository.get_signals_by_company(
            company_id
        )

    elif location:

        signals = repository.get_signals_by_location(
            location
        )

    else:
        signals = repository.get_all_signals(limit=100)

    return {
        "count": len(signals),
        "signals": rows_to_dict(signals),
    }


# ============================================================
# COMPANIES
# ============================================================


@router.get("/companies/{company_id}")
async def get_company(company_id: int):

    company = repository.get_company(
        company_id
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return row_to_dict(company)


@router.get("/companies/{company_id}/signals")
async def get_company_signals(
    company_id: int
):

    company = repository.get_company(
        company_id
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    signals = repository.get_signals_by_company(
        company_id
    )

    return {
        "company_id": company_id,
        "count": len(signals),
        "signals": rows_to_dict(signals),
    }


@router.get("/companies/{company_id}/people")
async def get_company_people(
    company_id: int
):

    company = repository.get_company(
        company_id
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    people = repository.get_people_by_company(company_id)

    return {
        "company_id": company_id,
        "count": len(people),
        "people": rows_to_dict(people),
    }


@router.get("/companies/{company_id}/jobs")
async def get_company_jobs(
    company_id: int
):

    company = repository.get_company(
        company_id
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    jobs = repository.get_jobs_by_company(
        company_id
    )

    return {
        "company_id": company_id,
        "count": len(jobs),
        "jobs": rows_to_dict(jobs),
    }


# ============================================================
# PEOPLE
# ============================================================


@router.get("/people/search")
async def search_people(
    q: Optional[str] = None,
    company_id: Optional[int] = None,
    location: Optional[str] = None,
    title: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    people = repository.search_people(
        query=q,
        company_id=company_id,
        location=location,
        title=title,
        limit=limit,
    )
    return {
        "count": len(people),
        "people": rows_to_dict(people),
    }


@router.get("/people/{person_id}")
async def get_person(person_id: int):

    person = repository.get_person(
        person_id
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    return row_to_dict(person)


@router.get("/people/{person_id}/contacts")
async def get_person_contacts(
    person_id: int
):

    person = repository.get_person(
        person_id
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    contacts = repository.get_contacts_by_person(
        person_id
    )

    return {
        "person_id": person_id,
        "count": len(contacts),
        "contacts": rows_to_dict(contacts),
    }


# ============================================================
# CONTACT DISCOVERY
# ============================================================


@router.post("/people/{person_id}/discover-contact")
async def discover_contact(
    person_id: int
):

    person = repository.get_person(
        person_id
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    # Initialize contact service
    providers = create_providers()
    contact_service = ContactService(
        contact_provider=providers.get("tavily")
    )
    
    if not contact_service.contact_provider:
        raise HTTPException(status_code=500, detail="Contact provider (Tavily) is not configured.")
        
    company = repository.get_company(person["company_id"])
    company_name = company["name"] if company else ""

    result = await contact_service.discover_contacts(row_to_dict(person), company_name)

    return {
        "person_id": person_id,
        "status": "success" if result else "failed",
        "contact": result
    }


# ============================================================
# CONTACTS
# ============================================================


@router.get("/contacts/{contact_id}")
async def get_contact(
    contact_id: int
):

    contact = repository.get_contact(
        contact_id
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found",
        )

    return row_to_dict(contact)
