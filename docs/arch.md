LinkedInProvider
        │
        │ raw MCP response
        ▼
LinkedInSearchResult
        │
        ▼
DiscoveryService
        │
        ├── classify expansion signal
        │
        ├── extract company
        │
        ├── extract location
        │
        └── extract evidence
        │
        ▼
Company Research
        │
        ▼
People Discovery
        │
        ▼
Web Evidence
        │
        ▼
Database


### PIPELINE 

                    ┌─────────────────────┐
                    │ User Search Criteria│
                    │ Bangalore           │
                    │ Office Expansion    │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ DiscoveryService   │
                    │                    │
                    │ Query Grammar      │
                    │ Phrase Queries     │
                    │ Hashtag Queries    │
                    └─────────┬──────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
        ┌───────────────┐           ┌──────────────┐
        │ LinkedIn MCP  │           │ Web Search   │
        │ search_posts  │           │ / Crawler    │
        └───────┬───────┘           └──────┬───────┘
                │                          │
                └────────────┬─────────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Expansion Signals   │
                  │                     │
                  │ Company?            │
                  │ Location?           │
                  │ Event?              │
                  │ Evidence?           │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ CompanyService      │
                  │                     │
                  │ LinkedIn            │
                  │ Web                 │
                  │ Apollo              │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ PeopleService       │
                  │                     │
                  │ Expansion roles     │
                  │ Leadership          │
                  │ Decision makers     │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ ContactService      │
                  │                     │
                  │ Email               │
                  │ Phone               │
                  │ Web evidence        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ PostgreSQL/SQLite   │
                  │ Repository          │
                  └─────────────────────┘

#### BREAKDOWN

                    USER CRITERIA
                         │
                         ▼
                ┌─────────────────┐
                │ DiscoveryService │
                └────────┬────────┘
                         │
                 Query Grammar
                  /           \
                 ▼             ▼
          LinkedIn MCP       Web Search
          search_posts
                 \             /
                  ▼           ▼
                DISCOVERY RESULTS
                       │
                       ▼
                 SIGNAL EXTRACTION
                       │
                       ▼
                  COMPANY SERVICE
                       │
                ┌──────┴──────┐
                ▼             ▼
            LinkedIn        Apollo
                │             │
                └──────┬──────┘
                       ▼
                 PEOPLE SERVICE
                       │
                       ▼
                CONTACT SERVICE