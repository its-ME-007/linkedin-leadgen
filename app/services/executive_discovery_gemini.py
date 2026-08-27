"""Executive discovery using Gemini AI with Google Search grounding."""

import os
import json
import asyncio
from google import genai
from google.genai import types


class ExecutiveDiscoveryServiceGemini:
    """Executive discovery using Gemini AI grounded with Google Search."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        self.client = genai.Client(api_key=self.api_key)

    async def discover_executives(self, signal, **kwargs):
        """Discover executives using Gemini AI with Google Search grounding."""
        company = signal.get("company_name")

        if not company:
            return []

        prompt = f"""Company: {company}

Task: Find the top-level executive leadership of this company (CEO, Founder, Managing Director, Partners).
Focus on executives based in or operating in India.
Use Google Search to find current and verified information about the company's leadership.
Return their name, title, LinkedIn profile URL if available, and a brief description of their role.

Provide the response in JSON format with executives array containing name, title, linkedin_url, relevance, and confidence (0.0-1.0).
If you cannot find specific executives, return empty executives array.
Only include verifiable information for top-level leadership."""

        try:
            print(f"[EXECUTIVE DISCOVERY] Querying Gemini for {company} with Google Search...")
            
            # Use interactions API with google_search tool for grounding
            interaction = self.client.interactions.create(
                model="gemini-3.5-flash-lite",
                input=prompt,
                tools=[
                    {
                        "type": "google_search",
                    }
                ],
            )
            
            # Rate limit: 10s delay after each request
            await asyncio.sleep(10)
            
            # Parse the response
            output_text = interaction.output_text
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                json_start = output_text.find('{')
                json_end = output_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = output_text[json_start:json_end]
                    parsed = json.loads(json_str)
                else:
                    parsed = json.loads(output_text)
            except (json.JSONDecodeError, ValueError):
                print(f"[EXECUTIVE DISCOVERY] Could not parse JSON response for {company}")
                print(f"Raw response: {output_text[:200]}")
                return []
            
            executives_data = parsed.get("executives", [])
            
            print(f"[EXECUTIVE DISCOVERY] Gemini returned {len(executives_data)} executives")
            
            results = []
            for exec_data in executives_data:
                results.append({
                    "name": exec_data.get("name"),
                    "role": exec_data.get("title"),
                    "headline": exec_data.get("relevance"),
                    "linkedin_url": exec_data.get("linkedin_url"),
                    "company_name": company,
                    "tier": 1,
                    "matched_role": exec_data.get("title"),
                    "matched_title": "gemini_discovery",
                    "reason": exec_data.get("relevance"),
                    "confidence": exec_data.get("confidence", 0.7),
                    "source": "gemini_ai_with_google_search",
                })
            
            return results
            
        except Exception as exc:
            print(f"[EXECUTIVE DISCOVERY] Gemini query failed: {exc}")
            return []
