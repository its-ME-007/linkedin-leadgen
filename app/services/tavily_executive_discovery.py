"""Executive discovery using Tavily search + Gemini parsing with evidence grounding."""

import os
import json
import asyncio
import re
from typing import Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from difflib import SequenceMatcher

import httpx
from google import genai
from google.genai import types


class TavilyExecutiveDiscoveryService:
    """
    Executive discovery pipeline:
    1. Generate query series (quality-based iterative deepening)
    2. Aggregate Tavily results
    3. URL-level deduplication (preserve distinct pages)
    4. Source prioritization (metadata only)
    5. Gemini evidence extraction (strict, no hallucination)
    6. Entity-level deduplication (merge multi-source mentions)
    7. Source-weighted confidence scoring
    """

    EVIDENCE_KEYWORDS = [
        "ceo", "founder", "managing director", "md", "vp", "vice president",
        "head of", "chief", "president", "director", "co-founder", "partner",
        "executive", "leadership", "co-founder", "owner"
    ]

    COMPANY_DOMAINS = [
        "linkedin.com", "crunchbase.com", "bloomberg.com", "techcrunch.com",
        "forbes.com", "businessinsider.com", "venturebeat.com", "reuters.com",
        "cnbc.com", "inc.com", "entrepreneur.com"
    ]

    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY is not configured.")
        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        self.gemini_client = genai.Client(api_key=self.gemini_api_key)

    async def discover_executives(self, signal, **kwargs):
        """
        Main discovery pipeline: query → search → deduplicate → prioritize → parse → score.
        """
        company = signal.get("company_name")

        if not company:
            return []

        print(f"[TAVILY EXECUTIVE DISCOVERY] Starting for {company}")

        try:
            # Step 1: Iterative quality-based search
            raw_results = await self._iterative_quality_search(company)
            print(f"[TAVILY] Aggregated {len(raw_results)} raw results")

            if not raw_results:
                print(f"[TAVILY] No results found for {company}")
                return []

            # Step 2: URL-level deduplication
            deduplicated = self._deduplicate_results(raw_results)
            print(f"[TAVILY] Deduplicated to {len(deduplicated)} unique URLs")

            # Step 3: Source prioritization
            prioritized = self._prioritize_results(deduplicated, company)

            # Step 4: Gemini evidence extraction
            executives = await self._extract_executives_with_gemini(
                company, prioritized
            )
            print(f"[GEMINI] Extracted {len(executives)} candidates")

            if not executives:
                return []

            # Step 5: Entity-level deduplication
            deduplicated_execs = self._deduplicate_executives(executives)
            print(f"[DEDUP] Merged to {len(deduplicated_execs)} unique people")

            # Step 6: Confidence scoring
            scored_execs = self._compute_confidence_scores(deduplicated_execs)

            return scored_execs

        except Exception as exc:
            print(f"[TAVILY EXECUTIVE DISCOVERY] Error: {exc}")
            import traceback
            traceback.print_exc()
            return []

    # ========================================
    # Task 1: Query generation + iterative search
    # ========================================

    def _generate_query_series(self, company: str) -> list:
        """Generate query variations for iterative deepening."""
        queries = [
            f'"{company}" India executives',
            f'"{company}" India leadership',
            f'"{company}" India head',
            f'"{company}" leadership team',
            f'"{company}" India CEO founder',
        ]
        return queries

    def _extract_evidence_heuristics(self, results: list) -> int:
        """
        Count evidence indicators (titles, roles) in result titles/snippets.
        Returns count of evidence pieces found.
        """
        evidence_count = 0
        for result in results:
            title = (result.get("title") or "").lower()
            snippet = (result.get("snippet") or "").lower()
            combined = title + " " + snippet

            for keyword in self.EVIDENCE_KEYWORDS:
                if keyword in combined:
                    evidence_count += 1

        return evidence_count

    async def _iterative_quality_search(self, company: str) -> list:
        """
        Execute queries iteratively, stopping when evidence quality threshold reached.
        Threshold: >2 pieces of evidence detected across results.
        """
        queries = self._generate_query_series(company)
        all_results = []
        queries_executed = 0

        for query in queries:
            print(f"[TAVILY] Query {queries_executed + 1}: {query}")
            results = await self._tavily_search(query)
            all_results.extend(results)
            queries_executed += 1

            # Check evidence quality
            evidence_count = self._extract_evidence_heuristics(all_results)
            print(f"[TAVILY] Evidence detected: {evidence_count}")

            if evidence_count > 2:
                print(f"[TAVILY] Quality threshold reached, stopping queries")
                break

        # Add metadata
        for result in all_results:
            result["_queries_executed"] = queries_executed

        return all_results

    async def _tavily_search(self, query: str) -> list:
        """Execute single Tavily search query."""
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": 10,
            "include_answer": False,
            "include_raw_content": False,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            print(f"[TAVILY] Search error: {e}")
            return []

    # ========================================
    # Task 2: URL-level deduplication
    # ========================================

    def _canonicalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        try:
            parsed = urlparse(url)
            # Remove tracking params
            query_dict = parse_qs(parsed.query, keep_blank_values=True)
            # Remove common tracking params
            for param in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid"]:
                query_dict.pop(param, None)

            # Rebuild query string
            new_query = urlencode(query_dict, doseq=True) if query_dict else ""
            canonical = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                parsed.params,
                new_query,
                "",  # no fragment
            ))
            return canonical
        except Exception:
            return url.lower()

    def _deduplicate_results(self, results: list) -> list:
        """
        Remove duplicate URLs while preserving distinct pages from same domain.
        """
        seen_urls = {}
        deduplicated = []

        for result in results:
            url = result.get("url", "")
            canonical = self._canonicalize_url(url)

            if canonical not in seen_urls:
                seen_urls[canonical] = True
                # Extract domain for metadata
                domain = urlparse(url).netloc
                result["_domain"] = domain
                deduplicated.append(result)

        return deduplicated

    # ========================================
    # Task 3: Source prioritization
    # ========================================

    def _prioritize_results(self, results: list, company: str) -> list:
        """
        Categorize results by source priority:
        1 = LinkedIn profile
        2 = Company domain
        3 = News/company directories
        4 = Other
        """
        for result in results:
            url = result.get("url", "").lower()
            domain = result.get("_domain", "").lower()

            if "linkedin.com/in/" in url:
                result["_priority"] = 1
                result["_source_type"] = "linkedin"
            elif company.lower() in domain or domain.endswith(".in"):
                result["_priority"] = 2
                result["_source_type"] = "company_domain"
            elif any(news_domain in domain for news_domain in self.COMPANY_DOMAINS):
                result["_priority"] = 3
                result["_source_type"] = "news_directory"
            else:
                result["_priority"] = 4
                result["_source_type"] = "other"

        # Sort by priority
        results.sort(key=lambda x: x.get("_priority", 4))
        return results

    # ========================================
    # Task 4: Gemini evidence extraction
    # ========================================

    async def _extract_executives_with_gemini(self, company: str, results: list) -> list:
        """
        Parse search results with Gemini to extract executives.
        Enforce evidence-backed extraction only (no hallucination).
        """
        # Build context from search results
        results_text = self._format_results_for_gemini(company, results)

        prompt = f"""From these search results, extract top-level executives (CEO, Founder, Managing Director, Partners, VP, Head of) of "{company}".

For each person found in the search results, return:
- name: Full name (required if found)
- title: Job title (null if not explicitly mentioned in search results)
- linkedin_url: LinkedIn profile URL (null if not in search results)
- evidence_urls: Array of result URLs that mention this person
- evidence_text: Relevant snippet from search results showing this person's role
- relevance: Why this person is relevant to the company

CRITICAL RULES:
1. ONLY extract when explicit evidence exists in the provided search results
2. Do NOT infer or fabricate any field
3. If a field cannot be verified from search results, return null
4. evidence_urls must contain actual URLs from the provided results below
5. evidence_text must be direct quotes or close paraphrases from search snippets

Return ONLY valid JSON with executives array. No other text.

SEARCH RESULTS:
{results_text}

Return JSON:
{{
  "executives": [
    {{"name": "...", "title": "...", "linkedin_url": "...", "evidence_urls": [...], "evidence_text": "...", "relevance": "..."}}
  ]
}}"""

        try:
            print(f"[GEMINI] Parsing {len(results)} search results for {company}")

            # Delay before Gemini call to avoid quota exhaustion
            print(f"[GEMINI] Waiting 5s before API call...")
            await asyncio.sleep(5)

            response = self.gemini_client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temp for stricter extraction
                    response_mime_type="application/json",
                ),
            )

            # Rate limit after Gemini call
            await asyncio.sleep(3)

            # Parse response
            try:
                response_text = response.text
                print(f"[GEMINI] Response received ({len(response_text)} chars): {response_text[:100]}")
                
                # Extract JSON block if embedded in text
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                else:
                    json_str = response_text

                print(f"[GEMINI] Parsing JSON from response...")
                parsed = json.loads(json_str)
                executives = parsed.get("executives", [])

                print(f"[GEMINI] Parsed {len(executives)} executives from response")

                # Validate evidence URLs exist in input results
                result_urls = {r.get("url") for r in results}
                for exec_data in executives:
                    evidence_urls = exec_data.get("evidence_urls", [])
                    # Filter to only valid URLs
                    valid_urls = [u for u in evidence_urls if u in result_urls]
                    exec_data["evidence_urls"] = valid_urls

                return executives

            except json.JSONDecodeError as e:
                print(f"[GEMINI] JSON parse error: {e}")
                print(f"[GEMINI] Response preview: {response_text[:300]}")
                return []

        except Exception as e:
            print(f"[GEMINI] Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _format_results_for_gemini(self, company: str, results: list) -> str:
        """Format Tavily results for Gemini context."""
        lines = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "")
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            lines.append(f"{i}. Title: {title}\n   URL: {url}\n   Snippet: {snippet}\n")
        return "\n".join(lines)

    # ========================================
    # Task 5: Source-weighted confidence
    # ========================================

    def _compute_confidence_scores(self, executives: list) -> list:
        """
        Apply source-weighted confidence scoring.
        Base confidence from Gemini + source bonuses.
        """
        for exec_data in executives:
            evidence_urls = exec_data.get("evidence_urls", [])

            # Count source types
            linkedin_count = sum(1 for u in evidence_urls if "linkedin.com" in u.lower())
            company_count = sum(1 for u in evidence_urls if u.lower().endswith(".in") or "company.com" in u.lower())
            news_count = sum(1 for u in evidence_urls if any(nd in u.lower() for nd in self.COMPANY_DOMAINS))

            # Base confidence (from Gemini extraction)
            base_confidence = 0.7

            # Source bonuses
            linkedin_bonus = linkedin_count * 0.15 if linkedin_count > 0 else 0
            company_bonus = company_count * 0.10 if company_count > 0 else 0
            news_bonus = news_count * 0.05 if news_count > 0 else 0

            # Multi-source bonus
            unique_sources = len(set(urlparse(u).netloc.lower() for u in evidence_urls))
            multi_source_bonus = 0.10 if unique_sources >= 2 else 0

            # Cap at 1.0
            confidence_score = min(
                1.0,
                base_confidence + linkedin_bonus + company_bonus + news_bonus + multi_source_bonus
            )

            # Build reasons
            confidence_reasons = [f"Base confidence: {base_confidence}"]
            if linkedin_bonus > 0:
                confidence_reasons.append(f"LinkedIn sources: +{linkedin_bonus}")
            if company_bonus > 0:
                confidence_reasons.append(f"Company domain: +{company_bonus}")
            if news_bonus > 0:
                confidence_reasons.append(f"News/directory: +{news_bonus}")
            if multi_source_bonus > 0:
                confidence_reasons.append(f"Multi-source verification: +{multi_source_bonus}")

            # Source types
            source_types = []
            if linkedin_count > 0:
                source_types.append("linkedin")
            if company_count > 0:
                source_types.append("company_domain")
            if news_count > 0:
                source_types.append("news_directory")

            exec_data["confidence_score"] = round(confidence_score, 2)
            exec_data["confidence_reasons"] = confidence_reasons
            exec_data["source_types"] = source_types

        return executives

    # ========================================
    # Task 6: Entity-level deduplication
    # ========================================

    def _deduplicate_executives(self, executives: list) -> list:
        """
        Merge duplicate executives (fuzzy name match + same company).
        Consolidate evidence URLs.
        """
        merged = []
        used_indices = set()

        for i, exec1 in enumerate(executives):
            if i in used_indices:
                continue

            merged_exec = dict(exec1)
            merged_from = [i]

            # Find similar executives
            for j in range(i + 1, len(executives)):
                if j in used_indices:
                    continue

                exec2 = executives[j]
                name1 = exec1.get("name", "").lower()
                name2 = exec2.get("name", "").lower()

                # Fuzzy name matching
                similarity = SequenceMatcher(None, name1, name2).ratio()
                if similarity > 0.8:
                    # Merge
                    merged_urls = list(set(
                        merged_exec.get("evidence_urls", []) +
                        exec2.get("evidence_urls", [])
                    ))
                    merged_exec["evidence_urls"] = merged_urls
                    merged_from.append(j)
                    used_indices.add(j)

            if len(merged_from) > 1:
                merged_exec["consolidated_from"] = merged_from

            merged.append(merged_exec)
            used_indices.add(i)

        return merged
