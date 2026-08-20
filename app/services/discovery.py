class DiscoveryService:

    SIGNAL_GRAMMAR = {
        "office_expansion": {
            "phrases": [
                "expanding office",
                "office expansion",
                "setting up office",
                "new office",
                "opening office",
                "expanding operations",
                "new corporate office",
                "new headquarters",
                "setting up operations",
                "expanding presence",
            ],
            "hashtags": [
                "#OfficeExpansion",
                "#BusinessExpansion",
                "#CorporateExpansion",
                "#OfficeSpace",
                "#NewOffice",
                "#Expansion",
                "#GCC",
                "#GCCIndia",
                "#GCCExpansion",
            ],
        },

        "new_facility": {
            "phrases": [
                "new facility",
                "new campus",
                "new location",
                "new site",
                "setting up facility",
                "opening facility",
                "expanding facility",
            ],
            "hashtags": [
                "#NewFacility",
                "#NewCampus",
                "#Expansion",
                "#BusinessExpansion",
                "#FacilityExpansion",
            ],
        },

        "market_expansion": {
            "phrases": [
                "expanding into",
                "entering new market",
                "new market",
                "expanding presence",
                "launching in",
                "expanding operations",
            ],
            "hashtags": [
                "#MarketExpansion",
                "#BusinessExpansion",
                "#Expansion",
                "#Growth",
            ],
        },

        "hiring_expansion": {
            "phrases": [
                "rapidly hiring",
                "expanding team",
                "growing team",
                "hiring in",
                "new team",
                "building a team",
            ],
            "hashtags": [
                "#Hiring",
                "#Expansion",
                "#TeamExpansion",
                "#Growth",
            ],
        },
    }

    def __init__(
        self,
        linkedin_provider,
        web_search_service
    ):
        self.linkedin = linkedin_provider
        self.web_search = web_search_service

    async def discover_opportunities(self, criteria: dict):

        location = criteria.get("location")
        signal_types = criteria.get("signal_types", [])
        industry = criteria.get("industry")

        results = []

        for signal_type in signal_types:

            queries = self._build_queries(
                signal_type=signal_type,
                location=location,
                industry=industry
            )

            for query in queries:

                print(f"\n[DISCOVERY] {query}")

                # LinkedIn MCP
                linkedin_results = await self.linkedin.search_posts(
                    query,
                    limit=20
                )

                # Web search
                web_results = self.web_search.search(query)

                # Normalize both sources
                results.extend(
                    self._normalize_linkedin_results(
                        linkedin_results,
                        signal_type,
                        query
                    )
                )

                results.extend(
                    self._normalize_web_results(
                        web_results,
                        signal_type,
                        query
                    )
                )

        return self._deduplicate(results)

    @classmethod
    def _build_queries(
        cls,
        signal_type: str,
        location: str | None,
        industry: str | None = None
    ):

        grammar = cls.SIGNAL_GRAMMAR.get(signal_type)

        if not grammar:
            return []

        queries = []

        # --------------------------------
        # Phrase-based queries
        # --------------------------------

        for phrase in grammar["phrases"]:

            query_parts = [
                f'"{phrase}"'
            ]

            if location:
                query_parts.append(
                    f'"{location}"'
                )

            if industry:
                query_parts.append(
                    f'"{industry}"'
                )

            queries.append(
                " ".join(query_parts)
            )

        # --------------------------------
        # Hashtag-based queries
        # --------------------------------

        for hashtag in grammar["hashtags"]:

            query_parts = [
                hashtag
            ]

            if location:
                query_parts.append(
                    location
                )

            if industry:
                query_parts.append(
                    industry
                )

            queries.append(
                " ".join(query_parts)
            )

        return queries

    @staticmethod
    def _normalize_linkedin_results(
        result,
        signal_type,
        query
    ):

        return [{
            "source": "linkedin",
            "signal_type": signal_type,
            "query": query,
            "raw_result": result,
        }]

    @staticmethod
    def _normalize_web_results(
        result,
        signal_type,
        query
    ):

        return [{
            "source": "web",
            "signal_type": signal_type,
            "query": query,
            "raw_result": result,
        }]

    @staticmethod
    def _deduplicate(results):

        seen = set()
        unique = []

        for result in results:

            raw = result.get("raw_result")

            # Prefer a stable representation where possible
            key = (
                result.get("source"),
                result.get("signal_type"),
                str(raw)
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(result)

        return unique