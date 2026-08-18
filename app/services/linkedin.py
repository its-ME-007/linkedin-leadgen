class LinkedInProvider:
    """
    Interface for LinkedIn-specific operations.

    The implementation will later connect to the selected
    LinkedIn MCP/server.
    """

    def search_posts(self, query, limit=20):
        raise NotImplementedError

    def search_people(self, query, limit=20):
        raise NotImplementedError

    def search_companies(self, query, limit=20):
        raise NotImplementedError

    def get_person(self, linkedin_url):
        raise NotImplementedError

    def get_company(self, company_identifier):
        raise NotImplementedError