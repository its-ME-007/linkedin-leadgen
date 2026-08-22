import httpx

class BraveSearchService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 20},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        # Brave nests results under data["web"]["results"], but
        # _flatten_web_results in executive_discovery.py only unwraps
        # top-level LIST values under known keys ("results", "web", etc.).
        # Brave's "web" value is a dict, not a list, so it wouldn't be
        # picked up automatically — flatten it here to match the shape
        # the service expects.
        results = data.get("web", {}).get("results", [])

        return {"results": results}