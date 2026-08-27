from .connection import get_connection


# =========================
# COMPANIES
# =========================

def create_company(name, normalized_name=None, domain=None, description=None):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO companies
                (name, normalized_name, domain, description)
            VALUES (?, ?, ?, ?)
            """,
            (name, normalized_name, domain, description)
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_company(company_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM companies
            WHERE company_id = ?
            """,
            (company_id,)
        ).fetchone()

    finally:
        conn.close()


def get_company_by_name(name):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM companies
            WHERE normalized_name = ?
            """,
            (name.lower(),)
        ).fetchone()

    finally:
        conn.close()


def update_company(company_id, name=None, domain=None, description=None):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE companies
            SET name = COALESCE(?, name),
                domain = COALESCE(?, domain),
                description = COALESCE(?, description),
                updated_at = CURRENT_TIMESTAMP
            WHERE company_id = ?
            """,
            (name, domain, description, company_id)
        )

        conn.commit()

    finally:
        conn.close()


def delete_company(company_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM companies
            WHERE company_id = ?
            """,
            (company_id,)
        )

        conn.commit()

    finally:
        conn.close()


# =========================
# PEOPLE
# =========================

def create_person(
    full_name,
    normalized_name=None,
    current_title=None,
    location=None,
    company_id=None,
    linkedin_url=None,
    linkedin_id=None
):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO people
                (
                    full_name,
                    normalized_name,
                    current_title,
                    location,
                    company_id,
                    linkedin_url,
                    linkedin_id
                )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name,
                normalized_name,
                current_title,
                location,
                company_id,
                linkedin_url,
                linkedin_id
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_person(person_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM people
            WHERE person_id = ?
            """,
            (person_id,)
        ).fetchone()

    finally:
        conn.close()


def get_person_by_name(name):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM people
            WHERE normalized_name = ?
            """,
            (name.lower(),)
        ).fetchone()

    finally:
        conn.close()


def update_person(
    person_id,
    full_name=None,
    current_title=None,
    location=None,
    company_id=None,
    linkedin_url=None,
    linkedin_id=None
):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE people
            SET full_name = COALESCE(?, full_name),
                current_title = COALESCE(?, current_title),
                location = COALESCE(?, location),
                company_id = COALESCE(?, company_id),
                linkedin_url = COALESCE(?, linkedin_url),
                linkedin_id = COALESCE(?, linkedin_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE person_id = ?
            """,
            (
                full_name,
                current_title,
                location,
                company_id,
                linkedin_url,
                linkedin_id,
                person_id
            )
        )

        conn.commit()

    finally:
        conn.close()


def delete_person(person_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM people
            WHERE person_id = ?
            """,
            (person_id,)
        )

        conn.commit()

    finally:
        conn.close()


# =========================
# JOBS
# =========================

def create_job(
    company_id,
    title,
    description=None,
    location=None,
    employment_type=None,
    source_url=None,
    source_name=None,
    posted_at=None
):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO job_openings
                (
                    company_id,
                    title,
                    description,
                    location,
                    employment_type,
                    source_url,
                    source_name,
                    posted_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                title,
                description,
                location,
                employment_type,
                source_url,
                source_name,
                posted_at
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_job(job_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM job_openings
            WHERE job_id = ?
            """,
            (job_id,)
        ).fetchone()

    finally:
        conn.close()


def get_jobs_by_company(company_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM job_openings
            WHERE company_id = ?
            ORDER BY discovered_at DESC
            """,
            (company_id,)
        ).fetchall()

    finally:
        conn.close()


def delete_job(job_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM job_openings
            WHERE job_id = ?
            """,
            (job_id,)
        )

        conn.commit()

    finally:
        conn.close()


# =========================
# CONTACTS
# =========================

def create_contact(
    person_id,
    contact_type,
    contact_value,
    confidence=None,
    is_verified=False
):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO contact_points
                (
                    person_id,
                    contact_type,
                    contact_value,
                    confidence,
                    is_verified
                )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                person_id,
                contact_type,
                contact_value,
                confidence,
                int(is_verified)
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_contact(contact_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM contact_points
            WHERE contact_id = ?
            """,
            (contact_id,)
        ).fetchone()

    finally:
        conn.close()


def get_contacts_by_person(person_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM contact_points
            WHERE person_id = ?
            ORDER BY confidence DESC
            """,
            (person_id,)
        ).fetchall()

    finally:
        conn.close()


def delete_contact(contact_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM contact_points
            WHERE contact_id = ?
            """,
            (contact_id,)
        )

        conn.commit()

    finally:
        conn.close()

# ============================================
# EXPANSION SIGNALS
# ============================================

def create_expansion_signal(
    signal_type,
    source_url,
    company_id=None,
    title=None,
    description=None,
    location=None,
    source_name=None,
    author_name=None,
    author_linkedin_url=None,
    signal_strength=None
):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO expansion_signals (
                company_id,
                signal_type,
                title,
                description,
                location,
                source_url,
                source_name,
                author_name,
                author_linkedin_url,
                signal_strength
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                signal_type,
                title,
                description,
                location,
                source_url,
                source_name,
                author_name,
                author_linkedin_url,
                signal_strength
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_expansion_signal(signal_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM expansion_signals
            WHERE signal_id = ?
            """,
            (signal_id,)
        ).fetchone()

    finally:
        conn.close()


def get_signals_by_company(company_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM expansion_signals
            WHERE company_id = ?
            ORDER BY signal_strength DESC,
                     discovered_at DESC
            """,
            (company_id,)
        ).fetchall()

    finally:
        conn.close()


def get_signals_by_location(location):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM expansion_signals
            WHERE location LIKE ?
            ORDER BY signal_strength DESC,
                     discovered_at DESC
            """,
            (f"%{location}%",)
        ).fetchall()

    finally:
        conn.close()


def update_signal_company(signal_id, company_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE expansion_signals
            SET company_id = ?
            WHERE signal_id = ?
            """,
            (company_id, signal_id)
        )

        conn.commit()

    finally:
        conn.close()


def delete_expansion_signal(signal_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM expansion_signals
            WHERE signal_id = ?
            """,
            (signal_id,)
        )

        conn.commit()

    finally:
        conn.close()

# ============================================
# WEB SOURCES
# ============================================

def create_web_source(url, source_type=None):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO web_sources (
                url,
                source_type
            )
            VALUES (?, ?)
            """,
            (
                url,
                source_type
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


# ============================================
# CONTACT EVIDENCE
# ============================================

def create_contact_evidence(
    contact_id,
    source_id,
    evidence_text=None
):
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO contact_evidence (
                contact_id,
                source_id,
                evidence_text
            )
            VALUES (?, ?, ?)
            """,
            (
                contact_id,
                source_id,
                evidence_text
            )
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


# ============================================
# UPSERT METHODS
# ============================================

def upsert_company(
    name,
    normalized_name=None,
    domain=None,
    industry=None,
    employee_count=None,
    revenue=None,
    description=None
):
    """
    Insert or update a company by normalized_name.

    Returns the company_id (existing or new).
    """
    conn = get_connection()

    if not normalized_name:
        normalized_name = name.strip().lower()

    try:
        cursor = conn.execute(
            """
            INSERT INTO companies
                (name, normalized_name, domain,
                 industry, employee_count, revenue,
                 description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_name) DO UPDATE SET
                domain = COALESCE(excluded.domain, companies.domain),
                industry = COALESCE(excluded.industry, companies.industry),
                employee_count = COALESCE(
                    excluded.employee_count,
                    companies.employee_count
                ),
                revenue = COALESCE(excluded.revenue, companies.revenue),
                description = COALESCE(
                    excluded.description,
                    companies.description
                ),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                name,
                normalized_name,
                domain,
                industry,
                employee_count,
                revenue,
                description,
            )
        )

        conn.commit()

        # Retrieve the actual company_id
        row = conn.execute(
            """
            SELECT company_id
            FROM companies
            WHERE normalized_name = ?
            """,
            (normalized_name,)
        ).fetchone()

        return row["company_id"] if row else cursor.lastrowid

    finally:
        conn.close()


def upsert_person(
    full_name,
    company_id=None,
    normalized_name=None,
    current_title=None,
    location=None,
    linkedin_url=None,
    linkedin_id=None
):
    """
    Insert or update a person by (normalized_name, company_id).

    Returns the person_id (existing or new).
    """
    conn = get_connection()

    if not normalized_name:
        normalized_name = full_name.strip().lower()

    try:
        cursor = conn.execute(
            """
            INSERT INTO people
                (full_name, normalized_name, current_title,
                 location, company_id, linkedin_url, linkedin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_name, company_id) DO UPDATE SET
                current_title = COALESCE(
                    excluded.current_title,
                    people.current_title
                ),
                location = COALESCE(
                    excluded.location,
                    people.location
                ),
                linkedin_url = COALESCE(
                    excluded.linkedin_url,
                    people.linkedin_url
                ),
                linkedin_id = COALESCE(
                    excluded.linkedin_id,
                    people.linkedin_id
                ),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                full_name,
                normalized_name,
                current_title,
                location,
                company_id,
                linkedin_url,
                linkedin_id,
            )
        )

        conn.commit()

        # Retrieve actual person_id
        row = conn.execute(
            """
            SELECT person_id
            FROM people
            WHERE normalized_name = ?
              AND company_id IS ?
            """,
            (normalized_name, company_id)
        ).fetchone()

        return row["person_id"] if row else cursor.lastrowid

    finally:
        conn.close()


def upsert_contact_point(
    person_id,
    contact_type,
    contact_value,
    confidence=None,
    is_verified=False
):
    """
    Insert or update a contact point by
    (person_id, contact_type, contact_value).

    Returns the contact_id.
    """
    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO contact_points
                (person_id, contact_type, contact_value,
                 confidence, is_verified)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(person_id, contact_type, contact_value)
            DO UPDATE SET
                confidence = COALESCE(
                    excluded.confidence,
                    contact_points.confidence
                ),
                is_verified = MAX(
                    excluded.is_verified,
                    contact_points.is_verified
                ),
                last_verified_at = CASE
                    WHEN excluded.is_verified = 1
                    THEN CURRENT_TIMESTAMP
                    ELSE contact_points.last_verified_at
                END
            """,
            (
                person_id,
                contact_type,
                contact_value,
                confidence,
                int(is_verified),
            )
        )

        conn.commit()

        # Retrieve actual contact_id
        row = conn.execute(
            """
            SELECT contact_id
            FROM contact_points
            WHERE person_id = ?
              AND contact_type = ?
              AND contact_value = ?
            """,
            (person_id, contact_type, contact_value)
        ).fetchone()

        return row["contact_id"] if row else cursor.lastrowid

    finally:
        conn.close()


def upsert_web_source(url, source_type=None):
    """
    Insert a web source, ignoring duplicates by URL.

    Returns the source_id.
    """
    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO web_sources
                (url, source_type)
            VALUES (?, ?)
            """,
            (url, source_type)
        )

        conn.commit()

        row = conn.execute(
            """
            SELECT source_id
            FROM web_sources
            WHERE url = ?
            """,
            (url,)
        ).fetchone()

        return row["source_id"] if row else None

    finally:
        conn.close()


def link_person_company(
    person_id,
    company_id,
    title=None,
    relationship_type=None,
    is_current=True
):
    """
    Insert or update a person ↔ company relationship.
    """
    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO person_company
                (person_id, company_id, title,
                 relationship_type, is_current)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(person_id, company_id) DO UPDATE SET
                title = COALESCE(
                    excluded.title,
                    person_company.title
                ),
                relationship_type = COALESCE(
                    excluded.relationship_type,
                    person_company.relationship_type
                ),
                is_current = excluded.is_current
            """,
            (
                person_id,
                company_id,
                title,
                relationship_type,
                int(is_current),
            )
        )

        conn.commit()

    finally:
        conn.close()


# ============================================
# ADDITIONAL QUERY METHODS
# ============================================

def get_people_by_company(company_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT p.*
            FROM people p
            WHERE p.company_id = ?
            ORDER BY p.created_at DESC
            """,
            (company_id,)
        ).fetchall()

    finally:
        conn.close()


def search_people(query=None, company_id=None, location=None, title=None, limit=50):
    """Search persisted people using optional, composable filters."""
    conn = get_connection()

    try:
        clauses = []
        params = []

        if query:
            clauses.append("(p.full_name LIKE ? OR p.normalized_name LIKE ?)")
            params.extend((f"%{query}%", f"%{query.lower()}%"))
        if company_id is not None:
            clauses.append("p.company_id = ?")
            params.append(company_id)
        if location:
            clauses.append("p.location LIKE ?")
            params.append(f"%{location}%")
        if title:
            clauses.append("p.current_title LIKE ?")
            params.append(f"%{title}%")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        return conn.execute(
            f"""
            SELECT p.*, c.name AS company_name
            FROM people p
            LEFT JOIN companies c ON c.company_id = p.company_id
            {where}
            ORDER BY p.updated_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    finally:
        conn.close()


def get_all_signals(limit=100):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT es.*, c.name AS company_name
            FROM expansion_signals es
            LEFT JOIN companies c
                ON es.company_id = c.company_id
            ORDER BY es.signal_strength DESC,
                     es.discovered_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    finally:
        conn.close()


def get_all_companies(limit=100):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM companies
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    finally:
        conn.close()


def get_company_by_domain(domain):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM companies
            WHERE domain = ?
            """,
            (domain,)
        ).fetchone()

    finally:
        conn.close()


def search_companies_by_name(query, limit=20):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM companies
            WHERE name LIKE ?
               OR normalized_name LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (
                f"%{query}%",
                f"%{query.lower()}%",
                limit,
            )
        ).fetchall()

    finally:
        conn.close()


def get_person_by_linkedin(linkedin_url):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT *
            FROM people
            WHERE linkedin_url = ?
            """,
            (linkedin_url,)
        ).fetchone()

    finally:
        conn.close()
