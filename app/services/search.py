class SearchService:

    def __init__(self, web_search_provider):
        pass

    def search(self, query: str, limit: int = 10):
        pass

    def search_person(
        self,
        person_name: str,
        company: str | None = None,
        query: str | None = None
    ):
        pass

    def search_company(
        self,
        company_name: str,
        query: str | None = None
    ):
        pass