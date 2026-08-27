import unittest

from app.services.discovery import DiscoveryService


class LinkedInProviderStub:
    def __init__(self):
        self.queries = []

    async def search_posts(self, query, limit):
        self.queries.append((query, limit))
        return {
            "references": {
                "search_results": [
                    {
                        "text": "We are looking for 30,000 sq ft office space in Bengaluru.",
                        "url": "https://www.linkedin.com/posts/example-1",
                        "author": "Example Corp",
                    }
                ]
            }
        }


class HashtagDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_searches_each_configured_hashtag_individually(self):
        provider = LinkedInProviderStub()
        service = DiscoveryService(linkedin_provider=provider)

        results = await service.discover_opportunities({"location": "Bengaluru"})

        self.assertEqual(
            [query for query, _ in provider.queries],
            [
                "#PropertyRequirement",
                "#PropertyWanted",
                "#CommercialProperty",
            ],
        )
        self.assertEqual(len(results), 1)  # Same post returned for all tags.
        self.assertEqual(results[0]["discovery_query"], "#PropertyRequirement")
        self.assertEqual(results[0]["target_location"], "Bengaluru")


if __name__ == "__main__":
    unittest.main()
