import inspect

from db.database import repository

class PipelineOrchestrator:
    SIGNAL_TYPE_ALIASES = {
        "NEW_STORE": "commercial_property_requirement",
        "OFFICE_REQUIREMENT": "office_space_requirement",
        "RETAIL_REQUIREMENT": "retail_space_requirement",
    }

    def __init__(
        self,
        discovery_service,
        signal_extractor,
        company_service,
        people_service,
        contact_service
    ):
        self.discovery = discovery_service
        self.extractor = signal_extractor
        self.company = company_service
        self.people = people_service
        self.contact = contact_service

    async def run_full_pipeline(self, criteria: dict):
        """
        Run the end-to-end pipeline:
        Discovery -> Signal Extraction -> Company -> People -> DB

        Contact discovery is intentionally excluded. It is an explicit action
        on a persisted person exposed by the API.
        """
        criteria = dict(criteria or {})
        criteria["signal_types"] = [
            self.SIGNAL_TYPE_ALIASES.get(signal_type, signal_type)
            for signal_type in criteria.get("signal_types", [])
        ]

        results = {
            "criteria": criteria,
            "raw_posts_found": 0,
            "signals_extracted": 0,
            "companies_processed": 0,
            "people_discovered": 0,
            "contacts_found": 0,
            "errors": []
        }
        
        # 1. Discovery
        if not self.discovery:
            results["errors"].append("DiscoveryService not available (missing providers).")
            return results
            
        print(f"[PIPELINE] Starting discovery for criteria: {criteria}")
        try:
            discovered_posts = await self.discovery.discover_opportunities(
                criteria
            )
            results["raw_posts_found"] = len(discovered_posts)
            print(
                f"[PIPELINE][discovery] normalized candidates: "
                f"{len(discovered_posts)}"
            )
        except Exception as e:
            results["errors"].append(f"Discovery failed: {e}")
            return results

        if not discovered_posts:
            return results

        # 2. Signal Extraction
        if self.extractor:
            print(f"[PIPELINE] Extracting signals from {len(discovered_posts)} posts...")
            try:
                extracted_signals = self.extractor.extract(discovered_posts)
                if inspect.isawaitable(extracted_signals):
                    extracted_signals = await extracted_signals
                
                # Filter to qualified signals (strength >= 0.6)
                qualified_signals = [
                    s for s in extracted_signals
                    if s.get("signal_strength", s.get("confidence", 0)) >= 0.6
                ]
                
                # Further filter by requested signal types if provided
                target_types = criteria.get("signal_types", [])
                if target_types:
                    qualified_signals = [s for s in qualified_signals if s.get("signal_type") in target_types]
                    
                results["signals_extracted"] = len(qualified_signals)
                print(
                    f"[PIPELINE][extraction] extracted={len(extracted_signals)} "
                    f"qualified={len(qualified_signals)}"
                )
            except Exception as e:
                print(f"[PIPELINE][extraction] failed: {e}")
                results["errors"].append(f"Signal extraction failed: {e}")
                qualified_signals = []
        else:
            print("[PIPELINE] SignalExtractor not available. Passing raw posts as generic signals.")
            # Graceful degradation: treat raw posts as generic signals
            qualified_signals = []
            for post in discovered_posts:
                qualified_signals.append({
                    "signal_type": "UNKNOWN",
                    "company_name": "Unknown Company (Raw)",
                    "title": post.get("text", "")[:50],
                    "description": post.get("text"),
                    "location": criteria.get("location"),
                    "source_url": post.get("url"),
                    "signal_strength": 1.0
                })
            results["signals_extracted"] = len(qualified_signals)

        # 3. Process each signal
        for signal in qualified_signals:
            try:
                await self.process_signal(signal, results)
            except Exception as e:
                print(f"[PIPELINE] Failed to process signal for {signal.get('company_name')}: {e}")
                results["errors"].append(f"Signal processing error ({signal.get('company_name')}): {e}")
                
        return results

    async def process_signal(self, signal: dict, results_tracker: dict):
        """
        Process a single signal through Company, People, and Contact services.
        """
        company_name = signal.get("company_name")
        if not company_name:
            return
            
        print(f"[PIPELINE] Processing signal for company: {company_name}")
        
        # Upsert Signal
        signal_id = repository.create_expansion_signal(
            signal_type=signal.get("signal_type"),
            source_url=(
                signal.get("source_url")
                or signal.get("url")
                or signal.get("discovery_query")
                or "about:blank"
            ),
            title=signal.get("title"),
            description=signal.get("description"),
            location=signal.get("location"),
            source_name=signal.get("source_name") or "web",
            author_name=signal.get("author_name"),
            author_linkedin_url=signal.get("author_linkedin_url"),
            signal_strength=signal.get(
                "signal_strength",
                signal.get("confidence"),
            )
        )

        # Company Service
        company_id = None
        if self.company:
            comp_result = await self.company.research_from_signal(signal) or {}
            company_id = comp_result.get("company_id")
            if company_id:
                # Link signal to company
                repository.update_signal_company(signal_id=signal_id, company_id=company_id)
                results_tracker["companies_processed"] += 1

        if not company_id:
            # Fallback if CompanyService is missing or failed, just upsert name
            company_id = repository.upsert_company(name=company_name)
            repository.update_signal_company(signal_id=signal_id, company_id=company_id)
            results_tracker["companies_processed"] += 1

        print(
            f"[PIPELINE][company] {company_name} -> company_id={company_id}"
        )

        # People Service
        discovered_people = []
        if self.people:
            print(f"[PIPELINE] Discovering people for {company_name}...")
            discovered_people = await self.people.find_people(
                company_id=company_id,
                company_name=company_name,
                signal_type=signal.get("signal_type"),
                location=signal.get("location")
            )
            results_tracker["people_discovered"] += len(discovered_people)
            print(
                f"[PIPELINE][people] {company_name} -> "
                f"{len(discovered_people)} persisted candidate(s)"
            )

        # Contact discovery is deliberately not part of the default waterfall.
        # The UI/API invokes ContactService for one person on demand.
