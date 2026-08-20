class PeopleService:

    def __init__(
        self,
        linkedin_provider,
        apollo_provider,
        repository
    ):
        self.linkedin = linkedin_provider
        self.apollo = apollo_provider
        self.repository = repository

    async def find_people(
        self,
        company_identifier,
        roles=None
    ):
        pass

    async def find_expansion_contacts(
        self,
        company_identifier
    ):
        pass

    async def enrich_person(
        self,
        person
    ):
        pass