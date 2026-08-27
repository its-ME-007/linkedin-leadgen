import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import dotenv
from app.services.tavily_contact_provider import TavilyContactProvider

OUTPUT_DIR = Path("tests/output/tavily_contact_provider")
LIVE_INPUT_FILE = Path("tests/output/executive_discovery.json")
LIVE_OUTPUT_FILE = Path("tests/output/tavily_contact_provider/live_contact_results.json")

dotenv.load_dotenv()

class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        self.request = {"url": url, "json": json}
        return FakeResponse(self.payload)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False, default=str)
    return path


async def run_live_contact_probe():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set; cannot run live Tavily contact search.")

    if not LIVE_INPUT_FILE.exists():
        raise FileNotFoundError(f"Live input file not found: {LIVE_INPUT_FILE}")

    with open(LIVE_INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    executives = []
    for result in data.get("results", []):
        signal = result.get("signal", {})
        company = signal.get("company_name")
        for executive in result.get("executives", []):
            executives.append({**executive, "company": company})

    if not executives:
        raise ValueError(f"No executives found in {LIVE_INPUT_FILE} for live Tavily contact search.")

    executive = executives[0]
    provider = TavilyContactProvider(api_key=api_key)
    contact = await provider.search_contact(
        name=executive.get("name"),
        company=executive.get("company") or executive.get("company_name"),
        linkedin_url=executive.get("linkedin_url"),
    )

    payload = {
        "executive": executive,
        "contact": contact,
    }
    write_json(LIVE_OUTPUT_FILE, payload)
    print(f"Live Tavily contact results written to: {LIVE_OUTPUT_FILE}")
    return payload


class TavilyContactProviderTests(unittest.TestCase):
    @staticmethod
    def _write_result(name, payload):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False, default=str)
        return path

    @staticmethod
    def _make_client(payload):
        class PayloadClient(FakeAsyncClient):
            pass

        PayloadClient.payload = payload
        return PayloadClient

    def test_requires_api_key(self):
        original = os.environ.get("TAVILY_API_KEY")
        os.environ.pop("TAVILY_API_KEY", None)
        try:
            with self.assertRaises(ValueError):
                TavilyContactProvider(api_key=None)
        finally:
            if original is not None:
                os.environ["TAVILY_API_KEY"] = original

    def test_extracts_email_and_phone_and_keeps_query_context(self):
        payload = {
            "results": [
                {
                    "title": "Jane Doe Contact",
                    "url": "https://example.com/contact",
                    "content": "Contact Jane Doe at jane.doe@example.com or call +1 (415) 555-0147.",
                    "raw_content": "Contact Jane Doe at jane.doe@example.com or call +1 (415) 555-0147.",
                }
            ]
        }

        PayloadClient = self._make_client(payload)

        with patch(
            "app.services.tavily_contact_provider.httpx.AsyncClient",
            PayloadClient,
        ):
            provider = TavilyContactProvider(api_key="test-key")
            result = asyncio.run(
                provider.search_contact(
                    name="Jane Doe",
                    company="Acme Corp",
                    linkedin_url="https://www.linkedin.com/in/janedoe",
                )
            )

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["company"], "Acme Corp")
        self.assertEqual(result["email"], "jane.doe@example.com")
        self.assertEqual(result["phone"], "+1 (415) 555-0147")
        self.assertEqual(result["source"], "tavily")
        self.assertEqual(result["confidence"], 0.8)
        self.assertEqual(result["result_count"], 1)
        self.assertIn("Jane Doe", result["query"])
        self.assertIn("Acme Corp", result["query"])
        self.assertIn("https://www.linkedin.com/in/janedoe", result["query"])
        self.assertEqual(result["evidence"][0]["emails"], ["jane.doe@example.com"])
        self._write_result("test_extracts_email_and_phone_and_keeps_query_context", result)

    def test_low_confidence_when_results_exist_without_contact_data(self):
        payload = {
            "results": [
                {
                    "title": "Jane Doe profile",
                    "url": "https://example.com/profile",
                    "content": "Jane Doe is a product leader at Acme Corp.",
                    "raw_content": "Jane Doe is a product leader at Acme Corp.",
                }
            ]
        }

        PayloadClient = self._make_client(payload)

        with patch(
            "app.services.tavily_contact_provider.httpx.AsyncClient",
            PayloadClient,
        ):
            provider = TavilyContactProvider(api_key="test-key")
            result = asyncio.run(
                provider.search_contact(
                    name="Jane Doe",
                    company="Acme Corp",
                )
            )

        self.assertIsNone(result["email"])
        self.assertIsNone(result["phone"])
        self.assertEqual(result["confidence"], 0.2)
        self.assertEqual(result["result_count"], 1)
        self.assertEqual(result["evidence"], [])
        self._write_result("test_low_confidence_when_results_exist_without_contact_data", result)

    def test_zero_confidence_when_no_search_results(self):
        payload = {"results": []}

        PayloadClient = self._make_client(payload)

        with patch(
            "app.services.tavily_contact_provider.httpx.AsyncClient",
            PayloadClient,
        ):
            provider = TavilyContactProvider(api_key="test-key")
            result = asyncio.run(
                provider.search_contact(
                    name="Jane Doe",
                    company="Acme Corp",
                )
            )

        self.assertIsNone(result["email"])
        self.assertIsNone(result["phone"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["result_count"], 0)
        self.assertEqual(result["evidence"], [])
        self._write_result("test_zero_confidence_when_no_search_results", result)


if __name__ == "__main__":
    if "--live" in sys.argv:
        sys.argv = [arg for arg in sys.argv if arg != "--live"]
        asyncio.run(run_live_contact_probe())
    else:
        if os.getenv("TAVILY_API_KEY") and LIVE_INPUT_FILE.exists():
            print("TAVILY_API_KEY detected; writing live contact output before tests...")
            asyncio.run(run_live_contact_probe())
    unittest.main(verbosity=2)