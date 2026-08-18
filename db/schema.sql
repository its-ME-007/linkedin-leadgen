PRAGMA foreign_keys = ON;


-- ============================================
-- COMPANIES
-- ============================================

CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    normalized_name TEXT,
    domain TEXT,

    industry TEXT,
    employee_count INTEGER,
    revenue TEXT,
    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- OPPORTUNITY / EXPANSION SIGNALS
-- ============================================

CREATE TABLE IF NOT EXISTS expansion_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,

    company_id INTEGER,

    signal_type TEXT NOT NULL,

    title TEXT,
    description TEXT,

    location TEXT,

    source_url TEXT NOT NULL,
    source_name TEXT,

    author_name TEXT,
    author_linkedin_url TEXT,

    signal_strength REAL,

    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE SET NULL
);


-- ============================================
-- PEOPLE / DECISION MAKERS
-- ============================================

CREATE TABLE IF NOT EXISTS people (
    person_id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name TEXT NOT NULL,
    normalized_name TEXT,

    current_title TEXT,
    location TEXT,

    company_id INTEGER,

    linkedin_url TEXT,
    linkedin_id TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE SET NULL
);


-- ============================================
-- PERSON ↔ COMPANY RELATIONSHIP
-- ============================================

CREATE TABLE IF NOT EXISTS person_company (
    person_id INTEGER,
    company_id INTEGER,

    title TEXT,
    relationship_type TEXT,

    start_date DATE,
    end_date DATE,

    is_current INTEGER DEFAULT 1,

    PRIMARY KEY (person_id, company_id),

    FOREIGN KEY (person_id)
        REFERENCES people(person_id)
        ON DELETE CASCADE,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);


-- ============================================
-- JOB OPENINGS
-- ============================================

CREATE TABLE IF NOT EXISTS job_openings (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,

    company_id INTEGER,

    title TEXT NOT NULL,
    description TEXT,

    location TEXT,
    employment_type TEXT,

    source_url TEXT,
    source_name TEXT,

    posted_at TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);


-- ============================================
-- CONTACT / REACH-OUT POINTS
-- ============================================

CREATE TABLE IF NOT EXISTS contact_points (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,

    person_id INTEGER NOT NULL,

    contact_type TEXT NOT NULL,
    contact_value TEXT NOT NULL,

    confidence REAL,

    is_verified INTEGER DEFAULT 0,

    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,

    FOREIGN KEY (person_id)
        REFERENCES people(person_id)
        ON DELETE CASCADE
);


-- ============================================
-- WEB SOURCES
-- ============================================

CREATE TABLE IF NOT EXISTS web_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,

    url TEXT NOT NULL UNIQUE,

    source_type TEXT,
    domain TEXT,

    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP
);


-- ============================================
-- CONTACT EVIDENCE
-- ============================================

CREATE TABLE IF NOT EXISTS contact_evidence (
    contact_id INTEGER,
    source_id INTEGER,

    evidence_text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (contact_id, source_id),

    FOREIGN KEY (contact_id)
        REFERENCES contact_points(contact_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_id)
        REFERENCES web_sources(source_id)
        ON DELETE CASCADE
);


-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_companies_name
    ON companies(normalized_name);

CREATE INDEX IF NOT EXISTS idx_companies_domain
    ON companies(domain);

CREATE INDEX IF NOT EXISTS idx_signals_company
    ON expansion_signals(company_id);

CREATE INDEX IF NOT EXISTS idx_signals_type
    ON expansion_signals(signal_type);

CREATE INDEX IF NOT EXISTS idx_signals_location
    ON expansion_signals(location);

CREATE INDEX IF NOT EXISTS idx_people_name
    ON people(normalized_name);

CREATE INDEX IF NOT EXISTS idx_people_company
    ON people(company_id);

CREATE INDEX IF NOT EXISTS idx_people_linkedin
    ON people(linkedin_id);

CREATE INDEX IF NOT EXISTS idx_jobs_company
    ON job_openings(company_id);

CREATE INDEX IF NOT EXISTS idx_jobs_location
    ON job_openings(location);

CREATE INDEX IF NOT EXISTS idx_jobs_title
    ON job_openings(title);

CREATE INDEX IF NOT EXISTS idx_contacts_person
    ON contact_points(person_id);

CREATE INDEX IF NOT EXISTS idx_contacts_type
    ON contact_points(contact_type);