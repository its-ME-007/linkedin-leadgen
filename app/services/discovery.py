"""LinkedIn hashtag-first opportunity retrieval."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import re


@dataclass(frozen=True)
class LinkedInDiscoveryConfig:
    hashtags: tuple[str, ...] = (
    "#PropertyRequirement",
    "#PropertyWanted",
    "#CommercialProperty",
    "#CommercialPropertyRequirement",
    "#PropertyRequired",
    "#SpaceRequirement",
    "#OfficeSpaceRequirement",
    "#OfficeRequirement",
    "#CommercialSpaceRequirement",
    "#RetailSpaceRequirement",
    "#OfficeSpaceWanted",
    "#CommercialSpaceWanted",
    )
    max_pages_per_hashtag: int = 4
    raw_output_dir: Path | None = None


class DiscoveryService:
    """Retrieve raw property-requirement candidates from LinkedIn hashtags."""

    SIGNAL_TYPE = "commercial_property_requirement"

    def __init__(
        self,
        linkedin_provider,
        web_search_service=None,
        config: LinkedInDiscoveryConfig | None = None,
    ):
        self.linkedin = linkedin_provider
        # Kept only for compatibility. Phase 1 never runs web search.
        self.web_search = None
        self.config = config or LinkedInDiscoveryConfig()

    async def discover_opportunities(self, criteria: dict) -> list[dict[str, Any]]:
        """Run one LinkedIn retrieval operation per configured hashtag."""
        if not self.linkedin:
            raise RuntimeError("LinkedInProvider is required for opportunity discovery.")

        results = []
        raw_candidates = 0
        location = criteria.get("location")

        for hashtag in self._build_queries():
            print(f"[DISCOVERY][linkedin] hashtag={hashtag}")
            raw_result = await self.linkedin.search_posts(
                hashtag,
                limit=self.config.max_pages_per_hashtag * 10,
            )
            posts = self._extract_posts(raw_result)
            raw_candidates += len(posts)
            print(
                f"[DISCOVERY][linkedin] hashtag={hashtag} "
                f"candidates={len(posts)}"
            )
            self._save_raw_response(hashtag, raw_result, posts)
            results.extend(
                self._normalize_linkedin_results(posts, hashtag, location)
            )

        unique = self._deduplicate(results)
        print(
            f"[QUALIFICATION] raw candidates: {raw_candidates} "
            f"deduplicated: {len(unique)}"
        )
        return unique

    def _build_queries(self) -> list[str]:
        """Return individual hashtags; never a Boolean LinkedIn query."""
        return list(self.config.hashtags)

    @staticmethod
    def _extract_posts(raw_result) -> list[dict[str, Any]]:
        """Unwrap common MCP result envelopes into post-like dictionaries.

        The LinkedIn MCP server returns two structures in the same payload:

          * ``sections.search_results`` – a single text blob that contains the
            full rendered content of every post, separated by the string
            "Feed post".  This is the authoritative source of post text.

          * ``references.search_results`` – a sparse list of linked entities
            (people, companies, jobs).  Each entry has only a name/title and a
            profile URL; it does *not* carry post body text.

        Previous versions consumed ``references`` first, which caused the
        parser to return author names only (e.g. "Suzi Carter") instead of the
        actual post content.  The fix parses the ``sections`` blob into
        individual posts and uses ``references`` solely to resolve per-author
        profile URLs.
        """
        payload = DiscoveryService._unwrap_payload(raw_result)
        if not isinstance(payload, dict):
            return []

        # ------------------------------------------------------------------
        # Primary path: parse the full-text blob in sections.search_results
        # ------------------------------------------------------------------
        sections = payload.get("sections")
        search_text = (
            sections.get("search_results")
            if isinstance(sections, dict)
            else None
        )
        if isinstance(search_text, str) and not DiscoveryService._is_no_results(search_text):
            # Build an author-name -> URL lookup from the references sidebar.
            ref_url_map: dict[str, str] = {}
            references = payload.get("references")
            if isinstance(references, dict):
                for ref in references.get("search_results") or []:
                    if isinstance(ref, dict) and ref.get("text") and ref.get("url"):
                        ref_url_map[ref["text"].strip().lower()] = ref["url"]

            posts = DiscoveryService._parse_post_blob(search_text, ref_url_map)
            if posts:
                return posts

        # ------------------------------------------------------------------
        # Fallback: generic structured keys (non-LinkedIn MCP sources)
        # ------------------------------------------------------------------
        for key in ("results", "posts", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break
        else:
            candidates = []

        posts = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            text = (
                candidate.get("text")
                or candidate.get("content")
                or candidate.get("snippet")
                or candidate.get("description")
                or ""
            )
            if not isinstance(text, str) or not text.strip():
                continue
            posts.append(
                {
                    "text": text.strip(),
                    "url": candidate.get("url") or candidate.get("link") or candidate.get("href"),
                    "author": candidate.get("author") or candidate.get("author_name"),
                    "timestamp": candidate.get("timestamp") or candidate.get("posted_at"),
                    "raw": candidate,
                }
            )
        return posts

    @staticmethod
    def _parse_post_blob(
        blob: str, ref_url_map: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Split the LinkedIn sections.search_results text blob into posts.

        The blob is structured as:

            Feed post

            <Author Name>

             • 3rd+

            <Headline / job title>

            <timestamp> •

            Follow   ← or "Connect" for non-connections

            <actual post body text>

            <reactions / comments / CTA lines>

            Feed post

            ...

        We split on "Feed post" boundaries, extract the author from the first
        line of each block, strip the LinkedIn header (everything up to and
        including the "Follow" / "Connect" action button), and map the author
        name to a profile URL via the references sidebar.
        """
        # Split on "Feed post" section boundaries.
        raw_blocks = re.split(r"(?m)^Feed post\s*$", blob)
        posts: list[dict[str, Any]] = []

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            lines = block.splitlines()
            author = lines[0].strip() if lines else ""

            # Extract author company/title from the header
            author_company = None
            for i in range(1, min(5, len(lines))):
                line = lines[i].strip()
                if line and not line.startswith('•') and '@' not in line and line != "":
                    # Look for "at CompanyName" or "CompanyName |" patterns
                    if ' at ' in line:
                        author_company = line.split(' at ', 1)[1].split('\n')[0].strip()
                        break
                    elif '|' in line:
                        author_company = line.split('|')[0].strip()
                        break

            # Strip the LinkedIn card header: everything up to and including
            # the "Follow" or "Connect" call-to-action line that precedes the
            # post body.
            body_match = re.split(r"\b(?:Follow|Connect)\b[ \t]*\n+", block, maxsplit=1)
            if len(body_match) == 2:
                body = body_match[1].strip()
            else:
                # No Follow/Connect found – use the full block as the body.
                # This covers edge cases like promoted posts.
                body = block.strip()

            if not body:
                continue

            # Resolve a URL from the author-name lookup built from references.
            url = ref_url_map.get(author.lower()) if author else None

            posts.append(
                {
                    "text": body,
                    "url": url,
                    "author": author or None,
                    "author_company": author_company,
                    "timestamp": None,
                    "raw": {"author": author, "author_company": author_company, "text": body},
                }
            )

        return posts

    @staticmethod
    def _unwrap_payload(raw_result):
        if isinstance(raw_result, dict):
            return raw_result
        if isinstance(raw_result, str):
            try:
                return json.loads(raw_result)
            except json.JSONDecodeError:
                return {"sections": {"search_results": raw_result}}

        structured = getattr(raw_result, "structured_content", None)
        if structured is None:
            structured = getattr(raw_result, "structuredContent", None)
        if isinstance(structured, dict):
            return structured

        text_parts = []
        for item in getattr(raw_result, "content", None) or []:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                text_parts.append(text)
        if text_parts:
            joined = "\n".join(text_parts)
            try:
                return json.loads(joined)
            except json.JSONDecodeError:
                return {"sections": {"search_results": joined}}
        return None

    @staticmethod
    def _is_no_results(text: str) -> bool:
        return "no results found" in text.lower()

    def _normalize_linkedin_results(self, posts, query, target_location):
        normalized = []
        for post in posts:
            normalized.append(
                {
                    "source": "linkedin",
                    "signal_type": self.SIGNAL_TYPE,
                    "query": query,
                    "discovery_query": query,
                    "target_location": target_location,
                    "source_url": post.get("url"),
                    # Keep the envelope compatible with SignalExtractor.
                    "raw_result": {"references": {"search_results": [post]}},
                }
            )
        return normalized

    @staticmethod
    def _deduplicate(results):
        seen = set()
        unique = []
        for result in results:
            post = (
                result.get("raw_result", {})
                .get("references", {})
                .get("search_results", [{}])[0]
            )
            url = post.get("url")
            if url:
                key = ("url", str(url).strip().lower())
            else:
                text = re.sub(r"\s+", " ", str(post.get("text") or "").lower()).strip()
                key = (
                    "content",
                    str(post.get("author") or "").strip().lower(),
                    text,
                    str(post.get("timestamp") or "").strip().lower(),
                )
            if key in seen:
                continue
            seen.add(key)
            unique.append(result)
        return unique

    def _save_raw_response(self, hashtag: str, raw_result, posts) -> None:
        if not self.config.raw_output_dir:
            return
        folder = Path(self.config.raw_output_dir) / hashtag.lstrip("#")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "raw.json").write_text(
            json.dumps(self._make_json_safe(raw_result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (folder / "normalized.json").write_text(
            json.dumps(posts, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @classmethod
    def _make_json_safe(cls, value):
        if isinstance(value, dict):
            return {key: cls._make_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._make_json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        structured = getattr(value, "structured_content", None)
        if isinstance(structured, dict):
            return cls._make_json_safe(structured)
        content = getattr(value, "content", None)
        if content is not None:
            return {"content": [getattr(item, "text", str(item)) for item in content]}
        return str(value)
