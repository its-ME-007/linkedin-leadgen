class DiscoveryService:

    def __init__(
        self,
        linkedin_provider,
        web_search_service
    ):
        self.linkedin = linkedin_provider
        self.web_search = web_search_service

    def discover_opportunities(self, criteria: dict):
        location = criteria.get("location")
        signal_types = criteria.get("signal_types", [])
        industry = criteria.get("industry")

        results = []

        for signal_type in signal_types:

            query = self._build_query(
                signal_type=signal_type,
                location=location,
                industry=industry
            )

            linkedin_results = self.linkedin.search_posts(query)

            web_results = self.web_search.search(query)

            results.extend(linkedin_results)
            results.extend(web_results)

        return results

    @staticmethod
    def _build_query(
        signal_type: str,
        location: str,
        industry: str | None = None
    ):
        query = f'"{signal_type}" "{location}"'

        if industry:
            query += f' "{industry}"'

        return query