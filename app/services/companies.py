class CompanyService:

    def __init__(
        self,
        linkedin_provider,
        web_search_service,
        apollo_provider,
        repository
    ):
        self.linkedin = linkedin_provider
        self.web_search = web_search_service
        self.apollo = apollo_provider
        self.repository = repository

    async def research_company(
        self,
        company_identifier
    ):
        pass

    async def research_from_signal(
        self,
        signal
    ):
        pass

    async def enrich_company(
        self,
        company
    ):
        pass