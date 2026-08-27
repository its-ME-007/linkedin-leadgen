from typing import Any
import json
import re
from urllib.parse import urlparse


class ExecutiveDiscoveryProviderError(Exception):
    """Raised when an executive candidate provider cannot be queried."""


class ExecutiveDiscoveryService:
    """
    Signal-aware executive discovery.

    Discovery source:
        - Web-search/X-Ray provider

    IMPORTANT DESIGN RULE:

        Search sources discover PEOPLE.

        ROLE_GRAMMAR only classifies people that were actually discovered.

        The service must NEVER manufacture a person from a role.

    Flow:

        qualified signal
            |
            +--------------------+
            |                    |
            v                    v
                  Web/X-Ray search
                      |
                      v
                parse people
                      |
                      v
                  normalize
                      |
                      v
                 deduplicate
                      |
                      v
                role matching
                      |
                      v
             relevant executives
    """

    ROLE_GRAMMAR = {

        # Commercial property requirements are intentionally broader than
        # expansion announcements. A real requirement may be owned by a
        # founder, country head, leasing lead, or property/operations owner.
        "property_requirement": {
            "tier_1": [
                {
                    "role": "Real Estate / Property Lead",
                    "aliases": [
                        "Head of Real Estate", "Real Estate Director",
                        "Director of Real Estate", "Head of Property",
                        "Property Director", "Property Head",
                        "Head of Leasing", "Leasing Director",
                    ],
                    "reason": "Likely owner of property selection and leasing.",
                },
                {
                    "role": "Retail / Store Development Lead",
                    "aliases": [
                        "Head of Retail", "Retail Director",
                        "Head of Store Development", "Store Development Head",
                        "Retail Expansion Head", "Head of Expansion",
                    ],
                    "reason": "Likely owner of retail locations and rollout decisions.",
                },
                {
                    "role": "Operations Leader",
                    "aliases": [
                        "Chief Operating Officer", "COO",
                        "Head of Operations", "Operations Director",
                        "Operations Head", "Country Operations Head",
                    ],
                    "reason": "Often sponsors location and operating-footprint decisions.",
                },
            ],
            "tier_2": [
                {
                    "role": "Country / India Head",
                    "aliases": [
                        "Country Head", "India Head", "Managing Director",
                        "General Manager", "Regional Head", "Country Manager",
                    ],
                    "reason": "Regional decision-maker for local property requirements.",
                },
                {
                    "role": "Founder / Executive Leadership",
                    "aliases": [
                        "Founder", "Co-Founder", "Chief Executive Officer",
                        "CEO", "Chief Executive",
                    ],
                    "reason": "May approve or directly own the requirement.",
                },
                {
                    "role": "Business Development Lead",
                    "aliases": [
                        "Head of Business Development", "Business Development Director",
                        "VP Business Development", "Commercial Director",
                    ],
                    "reason": "May coordinate market entry and property sourcing.",
                },
            ],
            "tier_3": [
                {
                    "role": "Facilities / Workplace Lead",
                    "aliases": [
                        "Head of Facilities", "Facilities Director", "Facilities Manager",
                        "Workplace Manager", "Workplace Director", "Admin Head",
                    ],
                    "reason": "Relevant operator for site, facilities, and workplace execution.",
                },
                {
                    "role": "Finance / Procurement Lead",
                    "aliases": [
                        "CFO", "Chief Financial Officer", "Head of Finance",
                        "Procurement Head", "Head of Procurement", "Procurement Manager",
                    ],
                    "reason": "May control approval, vendor, or lease budgets.",
                },
            ],
        },

        # ============================================================
        # OFFICE EXPANSION
        # ============================================================

        "office_expansion": {

            "tier_1": [
                {
                    "role": "Head of Expansion",
                    "aliases": [
                        "Expansion Head",
                        "Head of Business Expansion",
                        "Expansion Director",
                        "Head of Expansion Strategy",
                    ],
                    "reason": (
                        "Directly responsible for expansion strategy "
                        "and execution."
                    ),
                },
                {
                    "role": "Real Estate Director",
                    "aliases": [
                        "Director of Real Estate",
                        "Head of Real Estate",
                        "Real Estate Head",
                        "VP Real Estate",
                        "Vice President of Real Estate",
                    ],
                    "reason": (
                        "Responsible for identifying, evaluating, "
                        "and securing office space."
                    ),
                },
                {
                    "role": "Chief Operating Officer",
                    "aliases": [
                        "COO",
                        "Chief Operations Officer",
                    ],
                    "reason": (
                        "Owns operational execution and major "
                        "office expansion decisions."
                    ),
                },
                {
                    "role": "Operations Director",
                    "aliases": [
                        "Director of Operations",
                        "Head of Operations",
                        "Operations Head",
                        "VP Operations",
                        "Vice President of Operations",
                    ],
                    "reason": (
                        "Responsible for operational implementation "
                        "of the expansion."
                    ),
                },
                {
                    "role": "Facilities Manager",
                    "aliases": [
                        "Head of Facilities",
                        "Facilities Director",
                        "Facilities Head",
                        "Workplace Manager",
                    ],
                    "reason": (
                        "Responsible for physical office setup "
                        "and facilities."
                    ),
                },
            ],

            "tier_2": [
                {
                    "role": "Chief Financial Officer",
                    "aliases": [
                        "CFO",
                        "Finance Director",
                        "Head of Finance",
                        "Finance Head",
                    ],
                    "reason": (
                        "Controls or influences expansion budgets "
                        "and financial approval."
                    ),
                },
                {
                    "role": "Procurement Director",
                    "aliases": [
                        "Head of Procurement",
                        "Procurement Head",
                        "Procurement Manager",
                    ],
                    "reason": (
                        "Handles vendors, purchasing, and "
                        "procurement for the expansion."
                    ),
                },
                {
                    "role": "Legal Director",
                    "aliases": [
                        "Head of Legal",
                        "Legal Counsel",
                        "General Counsel",
                    ],
                    "reason": (
                        "Handles contracts, leases, permits, "
                        "and local legal requirements."
                    ),
                },
                {
                    "role": "IT Director",
                    "aliases": [
                        "Head of IT",
                        "IT Head",
                        "VP Information Technology",
                        "Vice President of Information Technology",
                        "Technology Infrastructure Head",
                    ],
                    "reason": (
                        "Responsible for technology infrastructure "
                        "required for the new office."
                    ),
                },
            ],

            "tier_3": [
                {
                    "role": "Chief Executive Officer",
                    "aliases": [
                        "CEO",
                        "Chief Executive",
                    ],
                    "reason": (
                        "May approve major strategic "
                        "expansion decisions."
                    ),
                },
                {
                    "role": "Human Resources Director",
                    "aliases": [
                        "HR Director",
                        "Head of HR",
                        "HR Head",
                        "Human Resources Head",
                        "People Director",
                    ],
                    "reason": (
                        "Important for workforce scaling but "
                        "usually not the primary office expansion owner."
                    ),
                },
                {
                    "role": "Workplace Designer",
                    "aliases": [
                        "Workplace Strategy Director",
                        "Workplace Design Lead",
                        "Workplace Experience Lead",
                    ],
                    "reason": (
                        "Influences workspace design "
                        "and employee experience."
                    ),
                },
            ],
        },

        # ============================================================
        # NEW FACILITY
        # ============================================================

        "new_facility": {

            "tier_1": [
                {
                    "role": "Head of Facilities",
                    "aliases": [
                        "Facilities Director",
                        "Facilities Head",
                        "Facilities Manager",
                    ],
                    "reason": (
                        "Directly responsible for facility "
                        "setup and management."
                    ),
                },
                {
                    "role": "Operations Director",
                    "aliases": [
                        "Head of Operations",
                        "Operations Head",
                        "Director of Operations",
                    ],
                    "reason": (
                        "Responsible for operational "
                        "implementation."
                    ),
                },
                {
                    "role": "Head of Expansion",
                    "aliases": [
                        "Expansion Director",
                        "Business Expansion Head",
                    ],
                    "reason": (
                        "Owns or coordinates "
                        "expansion initiatives."
                    ),
                },
            ],

            "tier_2": [
                {
                    "role": "Real Estate Director",
                    "aliases": [
                        "Head of Real Estate",
                        "Director of Real Estate",
                        "Real Estate Head",
                    ],
                    "reason": (
                        "Responsible for property "
                        "and facility acquisition."
                    ),
                },
                {
                    "role": "Chief Financial Officer",
                    "aliases": [
                        "CFO",
                        "Finance Director",
                        "Head of Finance",
                    ],
                    "reason": (
                        "Controls facility "
                        "expansion budgets."
                    ),
                },
                {
                    "role": "Procurement Director",
                    "aliases": [
                        "Head of Procurement",
                        "Procurement Head",
                        "Procurement Manager",
                    ],
                    "reason": (
                        "Handles facility vendors "
                        "and purchasing."
                    ),
                },
            ],

            "tier_3": [
                {
                    "role": "IT Director",
                    "aliases": [
                        "Head of IT",
                        "IT Head",
                    ],
                    "reason": (
                        "Handles facility "
                        "technology infrastructure."
                    ),
                },
                {
                    "role": "Human Resources Director",
                    "aliases": [
                        "HR Director",
                        "Head of HR",
                        "People Director",
                    ],
                    "reason": (
                        "Handles workforce implications "
                        "of the new facility."
                    ),
                },
            ],
        },

        # ============================================================
        # MARKET EXPANSION
        # ============================================================

        "market_expansion": {

            "tier_1": [
                {
                    "role": "Head of Strategy",
                    "aliases": [
                        "Strategy Director",
                        "Chief Strategy Officer",
                        "CSO",
                    ],
                    "reason": (
                        "Directly involved in "
                        "market-entry strategy."
                    ),
                },
                {
                    "role": "Head of Expansion",
                    "aliases": [
                        "Expansion Director",
                        "Business Expansion Head",
                    ],
                    "reason": (
                        "Owns expansion initiatives."
                    ),
                },
                {
                    "role": "Chief Operating Officer",
                    "aliases": [
                        "COO",
                        "Chief Operations Officer",
                    ],
                    "reason": (
                        "Oversees operational execution "
                        "of market expansion."
                    ),
                },
            ],

            "tier_2": [
                {
                    "role": "Regional Director",
                    "aliases": [
                        "Regional Head",
                        "Country Manager",
                        "General Manager",
                    ],
                    "reason": (
                        "Owns or oversees operations "
                        "in the target market."
                    ),
                },
                {
                    "role": "Business Development Director",
                    "aliases": [
                        "VP Business Development",
                        "Vice President of Business Development",
                        "Head of Business Development",
                    ],
                    "reason": (
                        "Responsible for market development "
                        "and commercial expansion."
                    ),
                },
                {
                    "role": "Chief Financial Officer",
                    "aliases": [
                        "CFO",
                        "Finance Director",
                        "Head of Finance",
                    ],
                    "reason": (
                        "Influences market-entry "
                        "investment decisions."
                    ),
                },
            ],

            "tier_3": [
                {
                    "role": "Chief Executive Officer",
                    "aliases": [
                        "CEO",
                        "Chief Executive",
                    ],
                    "reason": (
                        "Provides strategic approval "
                        "for major market expansion."
                    ),
                },
            ],
        },

        # ============================================================
        # HIRING EXPANSION
        # ============================================================

        "hiring_expansion": {

            "tier_1": [
                {
                    "role": "Chief Human Resources Officer",
                    "aliases": [
                        "CHRO",
                        "Chief HR Officer",
                    ],
                    "reason": (
                        "Owns large-scale "
                        "workforce expansion."
                    ),
                },
                {
                    "role": "Human Resources Director",
                    "aliases": [
                        "HR Director",
                        "Head of HR",
                        "HR Head",
                        "Human Resources Head",
                        "People Director",
                    ],
                    "reason": (
                        "Directly manages "
                        "hiring expansion."
                    ),
                },
                {
                    "role": "Talent Acquisition Director",
                    "aliases": [
                        "Head of Talent Acquisition",
                        "TA Director",
                        "Recruiting Director",
                        "Head of Recruiting",
                    ],
                    "reason": (
                        "Owns recruitment execution."
                    ),
                },
            ],

            "tier_2": [
                {
                    "role": "Business Unit Head",
                    "aliases": [
                        "BU Head",
                        "General Manager",
                        "Business Director",
                    ],
                    "reason": (
                        "Often drives hiring requirements "
                        "for a growing business unit."
                    ),
                },
                {
                    "role": "Chief Operating Officer",
                    "aliases": [
                        "COO",
                        "Chief Operations Officer",
                    ],
                    "reason": (
                        "May oversee "
                        "organizational scaling."
                    ),
                },
            ],

            "tier_3": [
                {
                    "role": "Chief Executive Officer",
                    "aliases": [
                        "CEO",
                        "Chief Executive",
                    ],
                    "reason": (
                        "Provides strategic approval "
                        "for major workforce expansion."
                    ),
                },
            ],
        },
    }

    def __init__(
        self,
        web_search_services=None,
        linkedin_provider=None,
    ):
        """
        web_search_services:
            List of web search providers (Brave, Tavily, SearXNG).
            We iterate through these to find one that works.

        linkedin_provider is retained only for backward-compatible callers;
        executive discovery never invokes LinkedIn search.
        """
        self.web_search_services = web_search_services or []

    async def discover_executives(
        self,
        signal: dict[str, Any],
        max_tier: int = 3,
        per_title_limit: int = 20,
        use_web_fallback: bool = False,
        ai_review_fallback_limit: int = 25,
    ) -> list[dict[str, Any]]:
        """
        Discover actual people from LinkedIn and optionally
        Google/X-Ray web search.

        Existing interface is preserved.

        IMPORTANT:

        No role is ever converted into a person.

        People must originate from one of the discovery sources.
        """

        signal_type = signal.get("signal_type")
        company = signal.get("company_name")
        location = signal.get("location")

        if not signal_type or not company:
            return []

        roles = self.get_target_roles(
            signal_type=signal_type,
            max_tier=max_tier,
        )

        if not roles:
            return []

        role_patterns = self._build_role_patterns(roles)

        all_people = []

        # ============================================================
        # SOURCE: GOOGLE X-RAY / WEB SEARCH
        # ============================================================

        for web_service in self.web_search_services:
            xray_query = self._build_xray_query(
                company=company,
                location=location,
            )

            print(
                f"[EXECUTIVE DISCOVERY] "
                f"X-Ray search via {web_service.__class__.__name__}: {xray_query}"
            )

            try:
                # We need a unified way to search depending on the service signature
                raw_web_results = await self._search_web_with_service(
                    web_service, xray_query
                )

                web_people = self._extract_web_people(
                    raw_web_results
                )

                print(
                    f"[EXECUTIVE DISCOVERY] "
                    f"X-Ray returned "
                    f"{len(web_people)} people"
                )

                all_people.extend(
                    self._tag_source(
                        web_people,
                        "google_xray",
                    )
                )
                
                # Stop if we got results, else try the next provider
                if web_people:
                    break

            except Exception as exc:
                print(
                    f"[EXECUTIVE DISCOVERY] "
                    f"X-Ray search via {web_service.__class__.__name__} failed: {exc}"
                )

        if not all_people:
            print(
                "[EXECUTIVE DISCOVERY] "
                "No people discovered from any source."
            )

        # ============================================================
        # NORMALIZE + DEDUPLICATE
        # ============================================================

        normalized_people = []

        for person in all_people:

            normalized = self._normalize_person(
                person,
                company=company,
            )

            if not normalized:
                continue

            # A real identity is mandatory.
            if not normalized.get("name"):
                continue

            normalized_people.append(
                normalized
            )

        normalized_people = (
            self._deduplicate_raw_people(
                normalized_people
            )
        )

        print(
            f"[EXECUTIVE DISCOVERY] "
            f"Unique discovered people: "
            f"{len(normalized_people)}"
        )

        # ============================================================
        # ROLE MATCHING
        # ============================================================

        candidates = []

        for person in normalized_people:

            matched = self._match_person_to_roles(
                person,
                role_patterns,
            )

            if not matched:
                continue

            best_match = matched[0]

            candidate = {
                "name": person.get("name"),
                "role": person.get("role"),
                "headline": person.get("headline"),
                "linkedin_url": person.get("linkedin_url"),
                "company_name": company,
                "location": person.get("location"),
                "tier": best_match["tier"],
                "matched_role": best_match["role"],
                "matched_title": best_match["term"],
                "reason": best_match.get("reason"),
                "confidence": best_match["confidence"],
                "source": person.get(
                    "source",
                    "unknown",
                ),
            }

            candidates.append(
                candidate
            )

        # Keep the web-discovered shortlist even when only some candidates
        # match a narrow role term. Property requirements are often posted by
        # brokers or founders, so title matching is a ranking signal, not a
        # hard eligibility gate.
        fallback_candidates = (
            self._build_ai_review_candidates(
                people=normalized_people,
                company=company,
                limit=ai_review_fallback_limit,
                fallback_tier=max_tier,
            )
        )

        if fallback_candidates:
            print(
                "[EXECUTIVE DISCOVERY] "
                f"Keeping {len(fallback_candidates)} broader "
                "web-discovered candidate(s) for review."
            )

        return self._deduplicate_people(
            [*candidates, *fallback_candidates]
        )

    # ================================================================
    # ROLE HELPERS
    # ================================================================

    @staticmethod
    def _build_role_patterns(
        roles,
    ):
        patterns = []

        for role in roles:

            canonical_role = role.get(
                "role",
                "",
            )

            terms = [
                canonical_role,
                *role.get(
                    "aliases",
                    [],
                ),
            ]

            for term in terms:

                if not term:
                    continue

                patterns.append(
                    {
                        "tier": role.get("tier"),
                        "role": canonical_role,
                        "term": term,
                        "reason": role.get(
                            "reason"
                        ),
                    }
                )

        return patterns

    @classmethod
    def get_target_roles(
        cls,
        signal_type: str,
        max_tier: int = 3,
    ) -> list[dict[str, Any]]:

        signal_type = {
            "commercial_property_requirement": "property_requirement",
            "office_space_requirement": "property_requirement",
            "retail_space_requirement": "property_requirement",
            "NEW_STORE": "property_requirement",
        }.get(signal_type, signal_type)

        grammar = cls.ROLE_GRAMMAR.get(
            signal_type
        )

        if not grammar:
            return []

        roles = []

        for tier_number in range(
            1,
            max_tier + 1,
        ):

            tier_key = (
                f"tier_{tier_number}"
            )

            for role in grammar.get(
                tier_key,
                [],
            ):

                roles.append(
                    {
                        **role,
                        "tier": tier_number,
                    }
                )

        return roles

    # ================================================================
    # GOOGLE X-RAY
    # ================================================================

    @staticmethod
    def _build_xray_query(
        company: str,
        location: str | None = None,
    ) -> str:
        """
        Build a broad LinkedIn X-Ray query.

        IMPORTANT:

        We intentionally do NOT put individual role names into
        this query.

        The search engine should discover people first.

        Role filtering happens later against actual profiles.

        This avoids the old architecture where:
            role -> search -> fake role record

        and instead gives:
            company -> people -> role classification
        """

        company_clean = (
            str(company)
            .strip()
            .replace('"', "")
        )

        location_part = ""

        if location:
            location_clean = (
                str(location)
                .strip()
                .replace('"', "")
            )

            if location_clean:
                location_part = (
                    f' "{location_clean}"'
                )

        return (
            '!g site:linkedin.com/in/ '
            f'"{company_clean}"'
            f'{location_part} '
            '-intitle:"profiles"'
        )

    async def _search_web_with_service(
        self,
        web_service,
        query: str,
    ):
        """
        Call the injected web-search provider.

        Supports both synchronous and asynchronous providers.

        Expected common interface:

            service.search(query)

        The returned value is passed to the literal parser.
        """

        search_method = getattr(
            web_service,
            "search",
            None,
        )

        if not callable(search_method):
            raise TypeError(
                f"{web_service.__class__.__name__} must expose "
                "a callable search(query) method"
            )

        result = search_method(
            query
        )

        if hasattr(
            result,
            "__await__",
        ):
            result = await result

        return result

    @classmethod
    def _extract_web_people(
        cls,
        raw_result,
    ):
        """
        Extract actual people from search-engine results.

        This parser is deliberately conservative.

        A search result becomes a person when it contains an explicit human
        name plus either a LinkedIn profile URL or a credible role/headline.

        We never infer a person merely from:
            - a company name
            - a role
            - a search query
        """

        if not raw_result:
            return []

        results = cls._flatten_web_results(
            raw_result
        )

        people = []

        for result in results:

            if isinstance(
                result,
                str,
            ):
                candidate = cls._parse_xray_result_text(
                    result
                )

                if candidate:
                    people.append(
                        candidate
                    )

                continue

            if not isinstance(
                result,
                dict,
            ):
                continue

            candidate = (
                cls._parse_xray_result_dict(
                    result
                )
            )

            if candidate:
                people.append(
                    candidate
                )

        return people

    @staticmethod
    def _flatten_web_results(
        raw_result,
    ):
        """
        Normalize common search-provider envelopes.

        This does not use an LLM.
        """

        if isinstance(
            raw_result,
            list,
        ):
            return raw_result

        if isinstance(
            raw_result,
            dict,
        ):

            for key in (
                "results",
                "organic_results",
                "items",
                "data",
                "web",
            ):

                value = raw_result.get(
                    key
                )

                if isinstance(
                    value,
                    list,
                ):
                    return value

            return [
                raw_result
            ]

        return [raw_result]

    @classmethod
    def _parse_xray_result_dict(
        cls,
        result,
    ):
        """
        Parse a typical search-engine result.

        Common fields:

            title
            url
            link
            snippet
            description
        """

        url = (
            result.get("url")
            or result.get("link")
            or result.get("href")
        )

        title = (
            result.get("title")
            or result.get("name")
        )

        snippet = (
            result.get("snippet")
            or result.get("description")
            or result.get("text")
            or ""
        )

        # Prefer a LinkedIn profile URL, but do not require it. Web results
        # with an explicit human name and role/headline are useful leads too.
        linkedin_url = (
            cls._extract_linkedin_profile_url(
                url
            )
        )

        if not linkedin_url:

            linkedin_url = (
                cls._extract_linkedin_profile_url(
                    str(snippet)
                )
            )

        name = cls._extract_name_from_xray(
            title,
            snippet,
        )

        if not name:
            return None

        role = cls._extract_role_from_xray(
            title,
            snippet,
            name,
        )

        if not linkedin_url and not role:
            return None

        location = (
            cls._extract_location_from_xray(
                snippet
            )
        )

        return {
            "name": name,
            "role": role,
            "headline": (
                str(snippet).strip()
                if snippet
                else None
            ),
            "linkedin_url": linkedin_url,
            "location": location,
            "raw_text": (
                f"{title or ''} "
                f"{snippet or ''}"
            ).strip(),
        }

    @classmethod
    def _parse_xray_result_text(
        cls,
        text,
    ):
        """
        Parse a raw search result string.

        This exists for search providers that return text rather
        than structured dictionaries.
        """

        if not text:
            return None

        linkedin_url = (
            cls._extract_linkedin_profile_url(
                text
            )
        )

        lines = [
            line.strip()
            for line in str(text).splitlines()
            if line.strip()
        ]

        title = (
            lines[0]
            if lines
            else None
        )

        name = cls._extract_name_from_xray(
            title,
            text,
        )

        if not name:
            return None

        role = cls._extract_role_from_xray(
            title,
            text,
            name,
        )

        if not linkedin_url and not role:
            return None

        return {
            "name": name,
            "role": role,
            "headline": text.strip(),
            "linkedin_url": linkedin_url,
            "location": (
                cls._extract_location_from_xray(
                    text
                )
            ),
            "raw_text": text.strip(),
        }

    @staticmethod
    def _extract_linkedin_profile_url(
        value,
    ):
        if not value:
            return None

        text = str(value)

        match = re.search(
            r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9%_\-./]+',
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        url = match.group(0)

        # Remove trailing punctuation commonly attached
        # to URLs in snippets.
        url = url.rstrip(
            ".,);]}>\"'"
        )

        return url

    @staticmethod
    def _extract_name_from_xray(
        title,
        snippet,
    ):
        """
        Extract a likely person name from a Google/X-Ray result.

        We deliberately avoid trying to infer a name from arbitrary
        prose. LinkedIn result titles are usually:

            John Smith - Director of Operations - SAP

        or:

            John Smith - SAP | LinkedIn
        """

        candidates = []

        if title:
            candidates.append(
                str(title)
            )

        if snippet:
            candidates.append(
                str(snippet)
            )

        for text in candidates:

            # Remove LinkedIn branding.
            cleaned = re.sub(
                r"\s*\|\s*LinkedIn.*$",
                "",
                text,
                flags=re.IGNORECASE,
            )

            # Split common LinkedIn title format.
            first_part = re.split(
                r"\s+-\s+|\s+\|\s+",
                cleaned,
                maxsplit=1,
            )[0].strip()

            # Strip common search-result prefixes.
            first_part = re.sub(
                r"^(profiles?|people)\s*:\s*",
                "",
                first_part,
                flags=re.IGNORECASE,
            ).strip()

            words = first_part.split()

            if not (
                2 <= len(words) <= 6
            ):
                continue

            # Conservative human-name validation.
            if not all(
                re.search(
                    r"[A-Za-z]",
                    word,
                )
                for word in words
            ):
                continue

            # Do not accept obvious non-person titles.
            lowered = first_part.lower()

            if any(
                blocked in lowered
                for blocked in (
                    "linkedin",
                    "company",
                    "jobs",
                    "search",
                    "profile",
                )
            ):
                continue

            return first_part

        return None

    @staticmethod
    def _extract_role_from_xray(
        title,
        snippet,
        name,
    ):
        """
        Extract an explicit title from the search result.

        This is extraction, not role classification.

        Actual classification is done later by
        _match_person_to_roles().
        """

        texts = []

        if title:
            texts.append(
                str(title)
            )

        if snippet:
            texts.append(
                str(snippet)
            )

        for text in texts:

            cleaned = text

            if name:
                cleaned = cleaned.replace(
                    name,
                    "",
                )

            cleaned = re.sub(
                r"\|\s*LinkedIn.*$",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

            parts = re.split(
                r"\s+-\s+|\s+\|\s+",
                cleaned,
            )

            for part in parts:

                part = part.strip()

                if not part:
                    continue

                lowered = part.lower()

                # Company-only fragments should not become roles.
                if lowered in {
                    "linkedin",
                    "linkedin member",
                }:
                    continue

                # A title normally contains one of these
                # occupational indicators.
                if any(
                    token in lowered
                    for token in (
                        "director",
                        "manager",
                        "head",
                        "chief",
                        "president",
                        "vice president",
                        "vp ",
                        "officer",
                        "counsel",
                        "lead",
                        "strategy",
                        "operations",
                        "facilities",
                        "real estate",
                        "finance",
                        "procurement",
                        "legal",
                        "information technology",
                        "technology",
                        "workplace",
                        "human resources",
                        "hr ",
                        "talent",
                        "business development",
                        "expansion",
                    )
                ):
                    return part

        return None

    @staticmethod
    def _extract_location_from_xray(
        text,
    ):
        if not text:
            return None

        location_patterns = [
            r"\bBangalore\b",
            r"\bBengaluru\b",
            r"\bMumbai\b",
            r"\bDelhi\b",
            r"\bHyderabad\b",
            r"\bChennai\b",
            r"\bPune\b",
            r"\bNoida\b",
            r"\bGurugram\b",
        ]

        for pattern in location_patterns:

            match = re.search(
                pattern,
                str(text),
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    # ================================================================
    # LINKEDIN RESPONSE PARSING
    # ================================================================

    @staticmethod
    def _extract_people(raw_result):
        """Extract actual people from the LinkedIn MCP response."""
        if not raw_result:
            return []

        # MCP CallToolResult -> TextContent -> JSON payload.
        if hasattr(raw_result, "content"):
            content = raw_result.content
            if content:
                first = content[0]
                if hasattr(first, "text"):
                    text = first.text
                    try:
                        raw_result = json.loads(text)
                    except (json.JSONDecodeError, TypeError):
                        return ExecutiveDiscoveryService._parse_people_text(text)

        if not isinstance(raw_result, dict) and hasattr(raw_result, "structured_content"):
            structured = raw_result.structured_content
            if isinstance(structured, dict):
                raw_result = structured

        if isinstance(raw_result, dict):
            for key in ("people", "results", "profiles", "items"):
                value = raw_result.get(key)
                if isinstance(value, list):
                    return value

            sections = raw_result.get("sections")
            references = raw_result.get("references")
            if isinstance(sections, dict):
                search_results = sections.get("search_results")
                if isinstance(search_results, str):
                    return ExecutiveDiscoveryService._parse_people_text(
                        search_results,
                        references=references,
                    )

            data = raw_result.get("data")
            if isinstance(data, dict):
                sections = data.get("sections")
                if isinstance(sections, dict):
                    search_results = sections.get("search_results")
                    if isinstance(search_results, str):
                        return ExecutiveDiscoveryService._parse_people_text(
                            search_results,
                            references=data.get("references", references),
                        )
            return []

        if isinstance(raw_result, list):
            return raw_result

        return []

    @staticmethod
    def _parse_people_text(
        text: str,
        references=None,
    ):
        """
        Conservative parser for LinkedIn MCP's semi-structured
        search-results text.
        """

        if not text:
            return []

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        people = []

        # LinkedIn may display "LinkedIn Member" in the text while the MCP
        # still exposes the real identity in references.search_results.
        if isinstance(references, dict):
            person_references = references.get("search_results", []) or []
        elif isinstance(references, list):
            person_references = references
        else:
            person_references = []
        person_reference_index = 0

        ignored_lines = {
            "LinkedIn Member",
            "View",
            "Message",
        }

        noise_phrases = (
            "you've reached the monthly limit",
            "you’ve reached the monthly limit",
            "upgrade to premium",
            "try premium",
            "unlimited search",
            "1-month free trial",
        )

        current = None

        def flush():

            nonlocal current

            if not current:
                return

            name = current.get("name")
            if not name:
                current = None
                return

            if name.lower() in {"view", "message"}:
                current = None
                return

            if name.lower() == "linkedin member":
                reference = current.get("_reference")
                if isinstance(reference, dict):
                    ref_name = reference.get("text") or reference.get("name")
                    ref_url = reference.get("url") or reference.get("link")
                    if ref_name:
                        current["name"] = str(ref_name).strip()
                    if ref_url:
                        current["linkedin_url"] = str(ref_url).strip()

            if not current.get("name") or current["name"].lower() == "linkedin member":
                current = None
                return

            current.pop("_reference", None)
            people.append(current)
            current = None

        i = 0

        while i < len(lines):

            line = lines[i]
            lower = line.lower()

            if any(
                phrase in lower
                for phrase in noise_phrases
            ):
                i += 1
                continue

            if line in ignored_lines:
                i += 1
                continue

            # Standard LinkedIn block:
            #
            # Name
            # • 3rd+
            # Headline
            # Location

            if (
                i + 2 < len(lines)
                and "•" in lines[i + 1]
            ):

                flush()

                reference = None
                if person_reference_index < len(person_references):
                    reference = person_references[person_reference_index]
                person_reference_index += 1

                current = {
                    "name": line,
                    "headline": lines[i + 2],
                    "linkedin_url": (
                        reference.get("url") or reference.get("link")
                        if isinstance(reference, dict) else None
                    ),
                    "location": None,
                    "raw_text": "",
                    "_reference": reference,
                }

                if isinstance(reference, dict):
                    ref_name = reference.get("text") or reference.get("name")
                    if ref_name:
                        current["name"] = str(ref_name).strip()

                if i + 3 < len(lines):

                    possible_location = (
                        lines[i + 3]
                    )

                    if (
                        possible_location
                        not in ignored_lines
                        and "•"
                        not in possible_location
                    ):

                        current["location"] = (
                            possible_location
                        )

                i += 3
                continue

            # Fallback block when connection degree
            # is missing.

            if (
                i + 1 < len(lines)
                and not line.startswith("--")
                and "current:" not in lower
                and "past:" not in lower
            ):

                next_line = (
                    lines[i + 1]
                )

                if (
                    len(line) <= 100
                    and len(next_line) <= 200
                    and not next_line.startswith(
                        (
                            "Current:",
                            "Past:",
                            "Summary:",
                        )
                    )
                    and "•"
                    not in next_line
                ):

                    words = line.split()

                    if (
                        2 <= len(words) <= 6
                        and all(
                            any(
                                char.isalpha()
                                for char in word
                            )
                            for word in words
                        )
                    ):

                        flush()

                        current = {
                            "name": line,
                            "headline": next_line,
                            "linkedin_url": None,
                            "location": (
                                lines[i + 2]
                                if i + 2 < len(lines)
                                else None
                            ),
                            "raw_text": "",
                        }

                        i += 2
                        continue

            if current:

                if lower.startswith(
                    "current:"
                ):

                    current["current"] = (
                        line[
                            len("Current:"):
                        ].strip()
                    )

                elif lower.startswith(
                    "past:"
                ):

                    current["past"] = (
                        line[
                            len("Past:"):
                        ].strip()
                    )

                elif lower.startswith(
                    "summary:"
                ):

                    current["summary"] = (
                        line[
                            len("Summary:"):
                        ].strip()
                    )

                current["raw_text"] = (
                    current.get(
                        "raw_text",
                        "",
                    )
                    + " "
                    + line
                ).strip()

            i += 1

        flush()

        return people

    # ================================================================
    # NORMALIZATION
    # ================================================================

    @staticmethod
    def _tag_source(
        people,
        source,
    ):
        tagged = []

        for person in people:

            if not isinstance(
                person,
                dict,
            ):
                continue

            copy = dict(
                person
            )

            copy["source"] = source

            tagged.append(
                copy
            )

        return tagged

    @staticmethod
    def _normalize_person(
        person,
        company: str,
    ):
        """
        Convert a discovered person into a stable internal shape.

        Missing fields remain None.

        No person is invented here.
        """

        if not isinstance(
            person,
            dict,
        ):
            return None

        name = (
            person.get("name")
            or person.get("full_name")
            or person.get("fullName")
        )

        role = (
            person.get("role")
            or person.get("title")
            or person.get("job_title")
            or person.get("jobTitle")
        )

        headline = person.get(
            "headline"
        )

        linkedin_url = (
            person.get("linkedin_url")
            or person.get("linkedinUrl")
            or person.get("profile_url")
            or person.get("profileUrl")
            or person.get("url")
        )

        location = (
            person.get("location")
            or person.get("geo")
            or person.get("city")
        )

        if not role:

            current_role = (
                person.get(
                    "current_role"
                )
            )

            if isinstance(
                current_role,
                dict,
            ):

                role = (
                    current_role.get(
                        "title"
                    )
                    or current_role.get(
                        "role"
                    )
                )

        if not name:
            return None

        returned_company = (
            person.get("company")
            or person.get("company_name")
            or person.get("companyName")
        )

        return {
            "name": str(
                name
            ).strip(),

            "role": (
                str(role).strip()
                if role
                else None
            ),

            "headline": (
                str(
                    headline
                ).strip()
                if headline
                else None
            ),

            "linkedin_url": (
                linkedin_url
            ),

            "location": location,

            "company": (
                returned_company
            ),

            "current": person.get("current"),
            "past": person.get("past"),
            "summary": person.get("summary"),
            "current_role": person.get("current_role"),

            "source": person.get(
                "source",
                "unknown",
            ),

            "raw": person,
        }

    # ================================================================
    # ROLE MATCHING
    # ================================================================

    @staticmethod
    def _match_person_to_roles(
        person,
        role_patterns,
    ):
        """
        Match an ACTUAL discovered person against role vocabulary.

        Deterministic matching is used first.

        No role -> person generation is possible here.
        """

        text_parts = [
            person.get("role") or "",
            person.get("headline") or "",
            person.get("current") or "",
            person.get("summary") or "",
        ]

        current_role = person.get("current_role")
        if isinstance(current_role, dict):
            text_parts.extend([
                current_role.get("title") or "",
                current_role.get("role") or "",
                current_role.get("company") or "",
            ])
        elif current_role:
            text_parts.append(str(current_role))

        haystack = " ".join(
            text_parts
        ).lower()

        if not haystack.strip():
            return []

        matches = []

        for pattern in role_patterns:

            term = (
                pattern["term"]
                .lower()
                .strip()
            )

            if not term:
                continue

            if term not in haystack:
                continue

            confidence = min(
                0.99,
                0.70
                + (
                    len(
                        term.split()
                    )
                    * 0.06
                ),
            )

            matches.append(
                {
                    "tier": pattern[
                        "tier"
                    ],
                    "role": pattern[
                        "role"
                    ],
                    "term": pattern[
                        "term"
                    ],
                    "reason": pattern.get(
                        "reason"
                    ),
                    "confidence": confidence,
                }
            )

        matches.sort(
            key=lambda item: (
                item["tier"],
                -len(
                    item["term"]
                ),
            )
        )

        return matches

    # ================================================================
    # RAW PEOPLE DEDUPLICATION
    # ================================================================

    @staticmethod
    def _deduplicate_raw_people(
        people,
    ):
        """
        Merge the same person discovered through LinkedIn and X-Ray.

        LinkedIn URL is preferred as the stable identity.

        If no URL exists, use normalized name + location.
        """

        seen = set()
        unique = []

        for person in people:

            linkedin_url = (
                person.get(
                    "linkedin_url"
                )
            )

            if linkedin_url:

                key = (
                    "url",
                    str(
                        linkedin_url
                    ).strip().lower(),
                )

            else:

                name = (
                    person.get(
                        "name"
                    )
                    or ""
                )

                location = (
                    person.get(
                        "location"
                    )
                    or ""
                )

                key = (
                    "name",
                    re.sub(
                        r"\s+",
                        " ",
                        str(
                            name
                        ).strip().lower(),
                    ),
                    re.sub(
                        r"\s+",
                        " ",
                        str(
                            location
                        ).strip().lower(),
                    ),
                )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                person
            )

        return unique

    # ================================================================
    # FINAL DEDUPLICATION
    # ================================================================

    @staticmethod
    def _deduplicate_people(
        candidates,
    ):
        """
        Deduplicate final executive candidates.

        Same person may have been discovered by:
            - LinkedIn MCP
            - Google X-Ray

        Prefer LinkedIn identity where available.
        """

        by_key = {}

        for candidate in candidates:

            linkedin_url = (
                candidate.get(
                    "linkedin_url"
                )
            )

            if linkedin_url:

                key = (
                    "url",
                    str(
                        linkedin_url
                    ).strip().lower(),
                )

            else:

                key = (
                    "name",
                    str(
                        candidate.get(
                            "name",
                            "",
                        )
                    ).strip().lower(),
                )

            existing = by_key.get(
                key
            )

            if existing is None:

                by_key[key] = (
                    candidate
                )
                continue

            # Prefer LinkedIn over X-Ray when both
            # identify the same person.

            if (
                existing.get(
                    "source"
                )
                != "linkedin"
                and candidate.get(
                    "source"
                )
                == "linkedin"
            ):

                by_key[key] = (
                    candidate
                )

        return list(
            by_key.values()
        )

    @staticmethod
    def _build_ai_review_candidates(
        people,
        company,
        limit=25,
        fallback_tier=3,
    ):
        candidates = []

        for person in people:
            if len(candidates) >= max(1, int(limit)):
                break

            if not ExecutiveDiscoveryService._is_plausible_ai_review_candidate(
                person
            ):
                continue

            candidates.append(
                {
                    "name": person.get("name"),
                    "role": person.get("role"),
                    "headline": person.get("headline"),
                    "linkedin_url": person.get("linkedin_url"),
                    "company_name": company,
                    "location": person.get("location"),
                    "tier": fallback_tier,
                    "matched_role": "AI Review",
                    "matched_title": "ai_review_fallback",
                    "reason": (
                        "No deterministic role keyword matched. "
                        "Candidate kept for AI-assisted prioritization."
                    ),
                    "confidence": 0.35,
                    "source": person.get(
                        "source",
                        "unknown",
                    ),
                }
            )

        return candidates

    @staticmethod
    def _is_plausible_ai_review_candidate(
        person,
    ):
        name = str(
            person.get("name") or ""
        ).strip()
        headline = str(
            person.get("headline") or ""
        ).strip()
        linkedin_url = person.get("linkedin_url")

        if not name:
            return False

        blocked_names = (
            "are these results helpful",
            "message",
            "view",
            "linkedin member",
        )

        lowered_name = name.lower()
        if lowered_name in blocked_names:
            return False

        if lowered_name.startswith("education:"):
            return False

        if lowered_name.startswith("current:"):
            return False

        if (
            headline.lower() in {
                "message",
                "view",
                "linkedin member",
            }
        ):
            return False

        if (
            not linkedin_url
            and len(name.split()) < 2
        ):
            return False

        return True
