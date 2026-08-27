import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.services.provider_factory import create_providers
from app.services.discovery import DiscoveryService

async def main():
    providers = create_providers()
    print("Providers loaded:", list(providers.keys()))
    
    discovery = DiscoveryService(
        linkedin_provider=None,
        web_search_service=providers.get("web_search_list", [None])[0]
    )
    
    print("Web search service is:", discovery.web_search)
    
    criteria = {
        "location": "Austin, TX",
        "signal_types": ["new_facility"]
    }
    
    results = await discovery.discover_opportunities(criteria)
    print("Results:", results)
    
if __name__ == "__main__":
    asyncio.run(main())
