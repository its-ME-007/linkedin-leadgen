from contextlib import AsyncExitStack
import os 
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class LinkedInProvider:

    def __init__(self, server_command):
        self.server_command = server_command
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:],
            env = {
                **os.environ,
                "TRANSPORT": "stdio",
            }
        )

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await self.session.initialize()

    async def search_posts(self, query, limit=20):
        self._ensure_connected()

        result = await self.session.call_tool(
            "search_posts",
            {
                "keywords": query,
                "max_pages": max(1, (limit + 9) // 10),
            },
        )

        return result

    async def search_people(self, query, limit=20):
        self._ensure_connected()

        result = await self.session.call_tool(
            "search_people",
            {
                "keywords": query,
                "max_pages": max(1, (limit + 9) // 10),
            },
        )

        return result

    async def search_companies(self, query, limit=20):
        self._ensure_connected()

        result = await self.session.call_tool(
            "search_companies",
            {
                "keywords": query,
            },
        )

        return result

    async def get_person(self, linkedin_url):
        self._ensure_connected()

        username = linkedin_url.rstrip("/").split("/")[-1]

        result = await self.session.call_tool(
            "get_person_profile",
            {
                "linkedin_username": username,
            },
        )

        return result

    async def get_company(self, company_identifier):
        self._ensure_connected()

        result = await self.session.call_tool(
            "get_company_profile",
            {
                "company_slug": company_identifier,
            },
        )

        return result

    async def search_jobs(self, query, location=None, limit=20):
        self._ensure_connected()

        arguments = {
            "keywords": query,
        }

        if location:
            arguments["location"] = location

        result = await self.session.call_tool(
            "search_jobs",
            arguments,
        )

        return result

    async def get_job_details(self, job_id):
        self._ensure_connected()

        result = await self.session.call_tool(
            "get_job_details",
            {
                "job_id": job_id,
            },
        )

        return result

    async def get_company_employees(
        self,
        company_identifier,
        keywords=None
    ):
        self._ensure_connected()

        arguments = {
            "company_slug": company_identifier,
        }

        if keywords:
            arguments["keywords"] = keywords

        result = await self.session.call_tool(
            "get_company_employees",
            arguments,
        )

        return result

    def _ensure_connected(self):
        if self.session is None:
            raise RuntimeError(
                "LinkedInProvider is not connected. "
                "Call await connect() first."
            )
            
    async def close(self):
        await self.exit_stack.aclose()
        self.session = None
