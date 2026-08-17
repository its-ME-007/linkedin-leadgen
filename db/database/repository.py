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