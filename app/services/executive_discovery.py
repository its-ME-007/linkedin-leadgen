from typing import Any


class ExecutiveDiscoveryService:
    """
    Signal-aware executive discovery role grammar.

    This service determines which leadership roles should be searched
    for a particular business signal.

    Design principle:

        Signal type
            ↓
        Canonical target roles
            ↓
        Search aliases
            ↓
        Contact discovery providers

    Canonical role names are used throughout the application.

    Aliases are ONLY alternate search terms and must never become
    separate canonical roles.
    """

    ROLE_GRAMMAR = {

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

    def __init__(self):
        pass

    def get_target_roles(
        self,
        signal_type: str,
        max_tier: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Return prioritized canonical roles for a signal type.

        Lower tier number means higher priority.

        Every returned role has exactly one canonical `role` name.
        Alternate titles are stored separately under `aliases`.
        """

        grammar = self.ROLE_GRAMMAR.get(signal_type)

        if not grammar:
            return []

        roles = []

        for tier in range(1, max_tier + 1):

            tier_name = f"tier_{tier}"

            for role in grammar.get(tier_name, []):

                roles.append({
                    **role,
                    "priority": tier,
                })

        return roles

    def get_search_titles(
        self,
        signal_type: str,
        max_tier: int = 3,
    ) -> list[str]:
        """
        Return canonical titles and aliases for searching.

        Canonical titles remain the application's normalized role
        representation. Aliases are search-only alternatives.
        """

        roles = self.get_target_roles(
            signal_type=signal_type,
            max_tier=max_tier,
        )

        titles = []

        for role in roles:

            titles.append(
                role["role"]
            )

            titles.extend(
                role.get("aliases", [])
            )

        # Preserve order while removing duplicates.
        return list(
            dict.fromkeys(titles)
        )

    def get_roles_by_priority(
        self,
        signal_type: str,
    ) -> dict[int, list[dict[str, Any]]]:
        """
        Return canonical roles grouped by priority tier.
        """

        grammar = self.ROLE_GRAMMAR.get(signal_type)

        if not grammar:
            return {}

        return {
            1: grammar.get("tier_1", []),
            2: grammar.get("tier_2", []),
            3: grammar.get("tier_3", []),
        }