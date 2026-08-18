class ApolloProvider:
    """
    Interface for Apollo-based company and person enrichment.
    """

    def search_companies(self, query, limit=20):
        raise NotImplementedError

    def search_people(self, query, limit=20):
        raise NotImplementedError

    def get_company(self, company_identifier):
        raise NotImplementedError

    def get_person(self, person_identifier):
        raise NotImplementedError