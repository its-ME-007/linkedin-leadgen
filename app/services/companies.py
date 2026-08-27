from db.database import repository
import re

class CompanyService:
    def __init__(
        self,
        web_search_services=None,
    ):
        """
        web_search_services: list of instantiated search providers.
        """
        self.web_search_services = web_search_services or []

    async def _search_web_with_service(self, web_service, query: str):
        search_method = getattr(web_service, "search", None)
        if not callable(search_method):
            return []
        
        result = search_method(query)
        if hasattr(result, "__await__"):
            result = await result
        return result

    async def research_company(
        self,
        company_identifier
    ):
        """
        Find company by identifier (name or domain), enrich via web, upsert to DB.
        """
        company_name = company_identifier
        description = None
        domain = None
        
        # Try to find some basic info via web search
        for web_service in self.web_search_services:
            try:
                raw_results = await self._search_web_with_service(web_service, f'"{company_name}" about company')
                results = raw_results.get("results", []) if isinstance(raw_results, dict) else raw_results
                
                if results and len(results) > 0:
                    first = results[0]
                    description = first.get("snippet", "") or first.get("description", "")
                    url = first.get("url", "")
                    
                    if url:
                        # Extract domain from URL
                        match = re.search(r"https?://(?:www\.)?([^/]+)", url)
                        if match:
                            domain = match.group(1)
                            
                if description or domain:
                    break
            except Exception as e:
                print(f"[COMPANY SERVICE] Enrichment failed via {web_service.__class__.__name__}: {e}")
                
        # Upsert to DB
        company_id = repository.upsert_company(
            name=company_name,
            domain=domain,
            description=description
        )
        
        return {
            "company_id": company_id,
            "name": company_name,
            "domain": domain,
            "description": description
        }

    async def research_from_signal(
        self,
        signal
    ):
        """
        Extract company from signal, enrich, and upsert.
        """
        company_name = signal.get("company_name")
        if not company_name:
            raise ValueError("Signal missing company_name")
            
        return await self.research_company(company_name)

    async def enrich_company(
        self,
        company
    ):
        """
        Further enrichment if needed.
        """
        return company