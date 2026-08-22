import httpx


class SearxngSearchService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json"},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0 Safari/537.36"
                    )
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        for result in data.get("results", []):
            if isinstance(result, dict) and "snippet" not in result and "content" in result:
                result["snippet"] = result["content"]

        return data