from db.database import repository

class PeopleService:
    def __init__(
        self,
        executive_discovery_service
    ):
        """
        executive_discovery_service: Instance of ExecutiveDiscoveryService
        """
        self.executive_discovery = executive_discovery_service

    async def find_people(
        self,
        company_id,
        company_name,
        signal_type="NEW_STORE",
        location=None
    ):
        """
        Discover people for a company using ExecutiveDiscoveryService,
        upsert them to the DB, and link them to the company.
        """
        if not self.executive_discovery:
            return []

        # Construct a synthetic signal for the discovery service
        signal = {
            "signal_type": signal_type,
            "company_name": company_name,
            "location": location
        }

        candidates = await self.executive_discovery.discover_executives(
            signal=signal,
            max_tier=3
        )

        persisted_people = []

        for candidate in candidates:
            # Upsert person
            person_id = repository.upsert_person(
                full_name=candidate.get("name"),
                company_id=company_id,
                current_title=candidate.get("role") or candidate.get("headline"),
                location=candidate.get("location"),
                linkedin_url=candidate.get("linkedin_url")
            )

            # Link to company
            repository.link_person_company(
                person_id=person_id,
                company_id=company_id,
                title=candidate.get("role") or candidate.get("headline"),
                relationship_type=candidate.get("matched_role") or "Discovered",
                is_current=True
            )

            candidate["person_id"] = person_id
            candidate["company_id"] = company_id
            persisted_people.append(candidate)

        return persisted_people

    async def find_expansion_contacts(
        self,
        company_id,
        company_name,
        location=None
    ):
        """
        Wrapper to find expansion-relevant contacts.
        """
        return await self.find_people(
            company_id=company_id,
            company_name=company_name,
            signal_type="NEW_STORE",
            location=location
        )

    async def enrich_person(
        self,
        person
    ):
        pass