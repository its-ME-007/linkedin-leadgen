import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class SignalExtractor:
    """
    AI-assisted business signal extractor.

    Pipeline:

        DiscoveryService results
                ↓
        Candidate post extraction
                ↓
        Deterministic noise filtering
                ↓
        Batched Gemini classification
                ↓
        Signal normalization
                ↓
        Deduplication

    Gemini is used for semantic classification while cheap,
    deterministic filtering is performed before the API call.
    """

    DEFAULT_MODEL = "gemini-3.1-flash-lite"
    DEFAULT_BATCH_SIZE = 4

    # ----------------------------------------
    # Initialization
    # ----------------------------------------

    def __init__(
        self,
        model=None,
        batch_size=None
    ):

        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                self.DEFAULT_MODEL
            )
        )

        try:
            self.batch_size = int(
                batch_size
                or os.getenv(
                    "BATCH_SIZE",
                    self.DEFAULT_BATCH_SIZE
                )
            )
        except (
            ValueError,
            TypeError
        ):
            self.batch_size = self.DEFAULT_BATCH_SIZE

        self.batch_size = max(
            1,
            self.batch_size
        )

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    # ----------------------------------------
    # Public extraction method
    # ----------------------------------------

    def extract(
        self,
        discovery_results
    ):

        candidates = []

        # ----------------------------------------
        # Step 1: Extract candidate posts
        # ----------------------------------------

        for discovery_result in (
            discovery_results or []
        ):

            posts = self._extract_posts(
                discovery_result
            )

            for post in posts:

                text = self._get_post_text(
                    post
                )

                if not text:
                    continue

                # Location is passed to Gemini via the candidate block for
                # semantic evaluation. A hard pre-filter here discards all
                # posts that do not mention the target city verbatim, which
                # eliminates the entire result set for hashtag-based searches
                # (LinkedIn returns global results regardless of geography).
                # Gemini rule 5 handles location relevance instead.
                target_location = discovery_result.get("target_location")

                # Cheap deterministic filtering
                if self._is_obvious_noise(
                    text
                ):
                    continue

                candidates.append(
                    {
                        "post": post,
                        "text": text,
                        "discovery_result": (
                            discovery_result
                        ),
                    }
                )

        if not candidates:
            print(
                "[SIGNAL EXTRACTION] "
                "No candidates after filtering."
            )
            return []

        print(
            "[SIGNAL EXTRACTION] "
            f"Candidates after filtering: "
            f"{len(candidates)}"
        )

        # ----------------------------------------
        # Step 2: Process candidates in batches
        # ----------------------------------------

        signals = []

        for start in range(
            0,
            len(candidates),
            self.batch_size
        ):

            batch = candidates[
                start:
                start + self.batch_size
            ]

            print(
                "[SIGNAL EXTRACTION] "
                f"Processing candidates "
                f"{start + 1}-"
                f"{start + len(batch)} "
                f"of {len(candidates)}"
            )

            classifications = (
                self._classify_batch_with_gemini(
                    batch
                )
            )

            if not classifications:
                continue

            # ------------------------------------
            # Step 3: Map classifications
            # back to original candidates
            # ------------------------------------

            for classification in (
                classifications
            ):

                if not isinstance(
                    classification,
                    dict
                ):
                    continue

                if not classification.get(
                    "is_relevant",
                    False
                ):
                    continue

                candidate_index = (
                    classification.get(
                        "candidate_index"
                    )
                )

                if not isinstance(
                    candidate_index,
                    int
                ):
                    continue

                # Gemini indexes candidates from 1
                candidate_position = (
                    candidate_index - 1
                )

                if (
                    candidate_position < 0
                    or
                    candidate_position >= len(batch)
                ):
                    continue

                candidate = batch[
                    candidate_position
                ]

                normalized = (
                    self._normalize_signal(
                        signal=classification,
                        post=candidate["post"],
                        text=candidate["text"],
                        discovery_result=(
                            candidate[
                                "discovery_result"
                            ]
                        )
                    )
                )

                if normalized:
                    signals.append(
                        normalized
                    )

        # ----------------------------------------
        # Step 4: Deduplicate
        # ----------------------------------------

        return self._deduplicate(
            signals
        )

    # ----------------------------------------
    # Candidate post extraction
    # ----------------------------------------

    @staticmethod
    def _extract_posts(
        discovery_result
    ):

        if not isinstance(
            discovery_result,
            dict
        ):
            return []

        raw_result = (
            discovery_result.get(
                "raw_result"
            )
        )

        if not raw_result:
            return []

        # MCP returns CallToolResult objects in the live API, while unit
        # fixtures commonly provide the already-unwrapped dictionary. Unwrap
        # both forms before applying the existing post parser.
        if not isinstance(raw_result, (dict, str)):
            structured = getattr(raw_result, "structured_content", None)
            if structured is None:
                structured = getattr(raw_result, "structuredContent", None)
            if structured:
                raw_result = structured
            else:
                content = getattr(raw_result, "content", None)
                text_parts = []
                for item in content or []:
                    text = getattr(item, "text", None)
                    if text:
                        text_parts.append(text)
                if text_parts:
                    joined = "\n".join(text_parts)
                    try:
                        raw_result = json.loads(joined)
                    except (TypeError, ValueError):
                        raw_result = joined

        # ----------------------------------------
        # LinkedIn MCP structured result
        # ----------------------------------------

        if isinstance(
            raw_result,
            dict
        ):

            references = (
                raw_result.get(
                    "references"
                )
            )

            search_results = (
                references.get(
                    "search_results",
                    []
                )
                if isinstance(
                    references,
                    dict
                )
                else []
            )

            if search_results:

                posts = []

                for item in search_results:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    posts.append(
                        {
                            "text": item.get(
                                "text",
                                ""
                            ),
                            "url": item.get(
                                "url"
                            ),
                            "kind": item.get(
                                "kind"
                            ),
                            "context": item.get(
                                "context"
                            ),
                        }
                    )

                if posts:
                    return posts

            # ------------------------------------
            # Fallback to sections.search_results
            # ------------------------------------

            sections = (
                raw_result.get(
                    "sections"
                )
            )

            if isinstance(
                sections,
                dict
            ):

                search_text = (
                    sections.get(
                        "search_results"
                    )
                )

                if search_text:

                    return [
                        {
                            "text": search_text,
                            "url": raw_result.get(
                                "url"
                            ),
                        }
                    ]

            # ------------------------------------
            # Generic structured result
            # ------------------------------------

            return [
                {
                    "text": json.dumps(
                        raw_result,
                        ensure_ascii=False
                    ),
                    "url": raw_result.get(
                        "url"
                    ),
                }
            ]

        # ----------------------------------------
        # String result
        # ----------------------------------------

        if isinstance(
            raw_result,
            str
        ):

            return [
                {
                    "text": raw_result
                }
            ]

        return []

    # ----------------------------------------
    # Extract text from post
    # ----------------------------------------

    @staticmethod
    def _get_post_text(
        post
    ):

        if not isinstance(
            post,
            dict
        ):
            return ""

        text = post.get(
            "text"
        )

        if isinstance(
            text,
            str
        ):
            return text.strip()

        content = post.get(
            "content"
        )

        if isinstance(
            content,
            str
        ):
            return content.strip()

        return ""

    # ----------------------------------------
    # Deterministic noise filter
    # ----------------------------------------

    @staticmethod
    def _is_obvious_noise(
        text
    ):

        normalized = (
            text.lower().strip()
        )

        if not normalized:
            return True

        # Very short content
        if len(normalized) < 30:
            return True

        # Generic engagement content
        noise_phrases = [
            "congratulations",
            "well deserved",
            "happy birthday",
            "great post",
            "thanks for sharing",
            "looking forward",
            "well said",
            "thank you",
        ]

        if any(
            phrase in normalized
            for phrase in noise_phrases
        ):
            return True

        supply_phrases = [
            "property available",
            "office available for lease",
            "space available",
            "market update",
            "real estate news",
        ]
        demand_phrases = [
            "looking for",
            "seeking",
            "requirement",
            "need office space",
            "looking to lease",
            "client is looking for",
        ]
        if any(phrase in normalized for phrase in supply_phrases) and not any(
            phrase in normalized for phrase in demand_phrases
        ):
            return True

        return False

    @staticmethod
    def _matches_target_location(text, target_location):
        """Case-insensitive location gate, including Bangalore/Bengaluru."""
        normalized = str(text).lower()
        target = str(target_location).strip().lower()
        if target in {"bangalore", "bengaluru"}:
            return any(term in normalized for term in ("bangalore", "bengaluru"))
        return target in normalized

    # ----------------------------------------
    # Gemini batch classifier
    # ----------------------------------------

    def _classify_batch_with_gemini(
        self,
        candidates
    ):

        if not candidates:
            return []

        candidate_blocks = []

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            discovery_result = (
                candidate[
                    "discovery_result"
                ]
            )

            signal_type = (
                discovery_result.get(
                    "signal_type",
                    "unknown"
                )
            )

            source = (
                discovery_result.get(
                    "source"
                )
            )

            discovery_query = (
                discovery_result.get(
                    "query"
                )
            )

            target_location = discovery_result.get("target_location")

            candidate_blocks.append(
                f"""
CANDIDATE {index}

Expected signal type:
{signal_type}

Discovery source:
{source}

Discovery query:
{discovery_query}

Target location:
{target_location}

Post content:
{candidate["text"]}
"""
            )

        candidates_text = "\n".join(
            candidate_blocks
        )

        # ----------------------------------------
        # System prompt
        # ----------------------------------------

        system_prompt = """
You are a business intelligence signal extraction system.

You receive multiple candidate social-media or web posts.

For EACH candidate, determine whether it contains a genuine
business expansion signal.

Relevant signals include only demand-side commercial property requirements:

- office space requirement
- retail space requirement
- property requirement
- commercial property requirement
- space requirement

The post should also contain a concrete property qualifier such as
"sq ft", "sq. ft", "carpet area", or "frontage".

IMPORTANT RULES:

1. Extract the COMPANY actually associated with the expansion.

2. Do NOT treat the post author as the company unless the
   content clearly establishes that relationship.

3. Do NOT invent a company.

4. If the company cannot be determined, return null.

5. Extract the location of the requirement. It is relevant only when it
   matches the target location supplied with the candidate. Treat Bangalore
   and Bengaluru as the same location.

6. Distinguish planned, active and completed expansion.

   The intent field MUST be exactly one of:
   - "planned"
   - "active"
   - "completed"
   - "unknown"

   Do not use variants such as "planned_expansion" or
   "completed_expansion".

7. Distinguish demand from supply. A post where a company,
   brand, broker, or consultant is actively seeking a property
   for a named business is a relevant commercial property
   requirement. A post merely advertising available inventory,
   "for lease" space, or market commentary is not relevant.

   For demand-side requirement posts, signal_type should be
   "commercial_property_requirement".

   actor_type must be exactly one of:
   - "DIRECT_OCCUPIER"
   - "BROKER_CLIENT_REQUIREMENT"
   - "PROPERTY_SUPPLY"
   - "MARKET_COMMENTARY"
   - "UNKNOWN"

8. A post saying "if your company is expanding" is NOT
   evidence that the author's company is expanding.

9. A company mentioned as an example, customer, partner,
   advertiser or unrelated entity should NOT automatically
   become company_name.

10. Evidence must come directly from the supplied post.

11. Do not invent evidence.

12. Confidence must reflect the quality of the evidence.

13. Do not infer facts that are not supported by the post.

14. Return exactly one classification for every supplied
    candidate.

15. candidate_index must correspond to the candidate number.

16. If a candidate is not relevant, set is_relevant to false.

17. If a relevant signal exists but the company cannot be
    reliably identified, company_name must be null.

18. Prefer precision over recall.

Return only valid JSON matching the supplied schema.
"""

        user_prompt = f"""
Analyze the following candidate business signals.

{candidates_text}
"""

        # ----------------------------------------
        # Gemini JSON schema
        # ----------------------------------------

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "classifications": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {

                            "candidate_index": {
                                "type": "INTEGER"
                            },

                            "is_relevant": {
                                "type": "BOOLEAN"
                            },

                            "signal_type": {
                                "type": "STRING"
                            },

                            "company_name": {
                                "type": "STRING",
                                "nullable": True
                            },

                            "location": {
                                "type": "STRING",
                                "nullable": True
                            },

                            "actor_type": {
                                "type": "STRING",
                                "enum": [
                                    "DIRECT_OCCUPIER",
                                    "BROKER_CLIENT_REQUIREMENT",
                                    "PROPERTY_SUPPLY",
                                    "MARKET_COMMENTARY",
                                    "UNKNOWN"
                                ]
                            },

                            "intent": {
                                "type": "STRING",
                                "enum": [
                                    "planned",
                                    "active",
                                    "completed",
                                    "unknown"
                                ]
                            },

                            "confidence": {
                                "type": "NUMBER"
                            },

                            "evidence": {
                                "type": "STRING"
                            },

                            "reason": {
                                "type": "STRING"
                            }
                        },
                        "required": [
                            "candidate_index",
                            "is_relevant",
                            "signal_type",
                            "company_name",
                            "location",
                            "actor_type",
                            "intent",
                            "confidence",
                            "evidence",
                            "reason"
                        ]
                    }
                }
            },
            "required": [
                "classifications"
            ]
        }

        # ----------------------------------------
        # Gemini request
        # ----------------------------------------

        try:

            print(
                "[GEMINI] Sending batch request..."
            )

            response = (
                self.client.models.generate_content(
                    model=self.model,

                    contents=[
                        system_prompt,
                        user_prompt
                    ],

                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            response_schema
                        ),
                    )
                )
            )

            print(
                "[GEMINI] Batch response received."
            )

            content = (
                response.text
            )

            if not content:

                print(
                    "[GEMINI] Empty response."
                )

                return []

            parsed = json.loads(
                content
            )

            classifications = (
                parsed.get(
                    "classifications",
                    []
                )
            )

            if not isinstance(
                classifications,
                list
            ):

                print(
                    "[GEMINI] "
                    "Invalid classifications."
                )

                return []

            return classifications

        except Exception as exc:

            print(
                "[BATCH SIGNAL CLASSIFIER ERROR] "
                f"{type(exc).__name__}: {exc}"
            )

            return []

    # ----------------------------------------
    # Normalize signal
    # ----------------------------------------

    def _normalize_signal(
        self,
        signal,
        post,
        text,
        discovery_result
    ):

        if not isinstance(
            signal,
            dict
        ):
            return None

        signal_type = (
            signal.get(
                "signal_type"
            )
            or discovery_result.get(
                "signal_type"
            )
        )

        company_name = (
            signal.get(
                "company_name"
            )
        )

        location = (
            signal.get(
                "location"
            )
        )

        actor_type = str(signal.get("actor_type") or "UNKNOWN").upper()
        if actor_type in {"PROPERTY_SUPPLY", "MARKET_COMMENTARY"}:
            return None

        confidence = (
            signal.get(
                "confidence"
            )
        )

        try:
            confidence = float(
                confidence
            )
        except (
            ValueError,
            TypeError
        ):
            confidence = 0.0

        confidence = min(
            1.0,
            max(
                0.0,
                confidence
            )
        )

        # ----------------------------------------
        # Evidence
        # ----------------------------------------

        evidence_text = (
            signal.get(
                "evidence"
            )
            or text
        )

        reason = (
            signal.get(
                "reason"
            )
        )

        evidence = {
            "text": evidence_text,
            "reason": reason,
        }

        # ----------------------------------------
        # Source
        # ----------------------------------------

        source = (
            discovery_result.get(
                "source"
            )
        )

        source_url = (
            post.get(
                "url"
            )
            if isinstance(
                post,
                dict
            )
            else None
        )

        if not source_url:

            source_url = (
                discovery_result.get(
                    "source_url"
                )
            )

        # ----------------------------------------
        # Intent
        # ----------------------------------------

        intent = self._normalize_intent(
            signal.get(
                "intent"
            )
        )

        # ----------------------------------------
        # Status
        # ----------------------------------------

        status = (
            self._derive_status(
                intent=intent,
                confidence=confidence,
                company_name=company_name
            )
        )

        # ----------------------------------------
        # Recency
        # ----------------------------------------

        recency = (
            self._extract_recency(
                text
            )
        )

        return {
            "signal_type": signal_type,
            "company_name": company_name,
            "location": location,
            "actor_type": actor_type,
            "intent": intent,
            "recency": recency,
            "confidence": confidence,
            "status": status,
            "evidence": evidence,
            "source": source,
            "source_url": source_url,
            "discovery_query": (
                discovery_result.get(
                    "query"
                )
            ),
        }

    # ----------------------------------------
    # Normalize intent
    # ----------------------------------------

    @staticmethod
    def _normalize_intent(intent):

        if intent is None:
            return "unknown"

        normalized = str(intent).strip().lower()

        aliases = {
            "planned_expansion": "planned",
            "active_expansion": "active",
            "completed_expansion": "completed",
        }

        return aliases.get(
            normalized,
            normalized if normalized in {
                "planned",
                "active",
                "completed",
                "unknown",
            } else "unknown"
        )

    # ----------------------------------------
    # Derive pipeline status
    # ----------------------------------------

    @staticmethod
    def _derive_status(
        intent,
        confidence=0.0,
        company_name=None
    ):

        # Low-confidence candidates are discarded.
        if confidence < 0.50:
            return "rejected"

        # A genuine signal without a reliable company name
        # should be enriched before becoming a usable lead.
        if not company_name:
            return "needs_enrichment"

        # A sufficiently confident signal with a company is
        # actionable regardless of whether the expansion is
        # planned, active, or completed.
        if confidence >= 0.60:
            return "qualified"

        # A lower-confidence signal can still qualify when the
        # model identified a concrete lifecycle intent.
        if intent != "unknown":
            return "qualified"

        return "needs_enrichment"

    # ----------------------------------------
    # Recency extraction
    # ----------------------------------------

    @staticmethod
    def _extract_recency(
        text
    ):

        if not text:
            return None

        normalized = (
            text.lower()
        )

        patterns = [
            r"(\d+)\s*(?:m|min|mins|minutes?)\s*ago",
            r"(\d+)\s*(?:h|hr|hrs|hours?)\s*ago",
            r"(\d+)\s*(?:d|day|days)\s*ago",
            r"(\d+)\s*(?:w|week|weeks)\s*ago",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized
            )

            if not match:
                continue

            value = int(
                match.group(1)
            )

            if "min" in pattern:
                return (
                    f"{value} minutes ago"
                )

            if "hour" in pattern:
                return (
                    f"{value} hours ago"
                )

            if "day" in pattern:
                return (
                    f"{value} days ago"
                )

            if "week" in pattern:
                return (
                    f"{value} weeks ago"
                )

        return None

    # ----------------------------------------
    # Generic phrase helper
    # ----------------------------------------

    @staticmethod
    def _contains_any(
        text,
        phrases
    ):

        if not text:
            return False

        normalized = (
            text.lower()
        )

        return any(
            phrase.lower() in normalized
            for phrase in phrases
        )

    # ----------------------------------------
    # Deduplication
    # ----------------------------------------

    @staticmethod
    def _deduplicate(
        signals
    ):

        seen = set()
        unique = []

        for signal in signals:

            evidence = signal.get(
                "evidence",
                {}
            )

            if isinstance(
                evidence,
                dict
            ):

                evidence_text = (
                    evidence.get(
                        "text"
                    )
                )

            else:

                evidence_text = (
                    evidence
                )

            key = (
                signal.get(
                    "company_name"
                ),
                signal.get(
                    "location"
                ),
                signal.get(
                    "signal_type"
                ),
                signal.get(
                    "source_url"
                ),
                evidence_text
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                signal
            )

        return unique

