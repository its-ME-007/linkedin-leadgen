import asyncio

from app.services.linkedin import LinkedInProvider


async def main():
    provider = LinkedInProvider(
        ["uvx", "mcp-server-linkedin@latest"]
    )

    try:
        await provider.connect()

        print("Connected to LinkedIn MCP server.")

        result = await provider.session.call_tool(
            'search_posts', 
            {
                "keywords" : "company expanding Bangalore office", 
                "max_pages" : 1
            }
        )
        
        if result.is_error:
            raise RuntimeError(str(result.content))

        return result.structured_content
    
    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())