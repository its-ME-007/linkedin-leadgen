import os
import shlex
from app.services.brave import BraveSearchService
from app.services.searxng import SearxngSearchService
from app.services.tavily_contact_provider import TavilyContactProvider
from app.services.signal_extractor import SignalExtractor
from app.services.linkedin import LinkedInProvider

def create_providers():
    """
    Check environment variables and instantiate only available providers.
    Allows the pipeline to degrade gracefully if API keys are missing.
    """
    providers = {}
    
    # -------------------------
    # Web Search Providers
    # -------------------------
    web_search_providers = []

    brave_api_key = os.getenv("BRAVE_API_KEY")
    if brave_api_key:
        brave = BraveSearchService(api_key=brave_api_key)
        providers["brave"] = brave
        web_search_providers.append(brave)

    searxng_url = os.getenv("SEARXNG_URL")
    if searxng_url:
        searxng = SearxngSearchService(base_url=searxng_url)
        providers["searxng"] = searxng
        web_search_providers.append(searxng)
        
    providers["web_search_list"] = web_search_providers

    # -------------------------
    # Contact Providers (Tavily)
    # -------------------------
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key:
        tavily = TavilyContactProvider(api_key=tavily_api_key)
        providers["tavily"] = tavily

    # -------------------------
    # AI (Gemini)
    # -------------------------
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        providers["signal_extractor"] = SignalExtractor()
        
    # -------------------------
    # LinkedIn MCP
    # -------------------------
    # The MCP is opt-in because it starts an external process and requires an
    # async connection lifecycle. The API connects/closes it per run.
    if os.getenv("LINKEDIN_MCP_ENABLED", "true").lower() in {
        "1", "true", "yes", "on"
    }:
        command = os.getenv(
            "LINKEDIN_MCP_COMMAND",
            "uvx mcp-server-linkedin@latest",
        )
        providers["linkedin"] = LinkedInProvider(shlex.split(command))

    return providers
