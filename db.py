import psycopg2

# Database connection configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "umbrella_jobs",
    "user": "postgres",
    "password": "postgres"
}


def insert_job(
    post_name,
    department,
    organization,
    government_level,
    sector,
    district,
    state,
    advertisement_no,
    total_vacancies,
    apply_start_date,
    apply_last_date,
    source_url
):
    """Insert a job record into the jobs table.

    Uses parameterized SQL to prevent SQL injection and
    handles duplicate records by skipping inserts for existing source_url values.

    Returns:
        True if a new record was inserted.
        False if the record already exists.
    """

    connection = None
    cursor = None

    insert_query = """
        INSERT INTO jobs (
            post_name,
            department,
            organization,
            government_level,
            sector,
            district,
            state,
            advertisement_no,
            total_vacancies,
            apply_start_date,
            apply_last_date,
            source_url
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_url) DO NOTHING
        RETURNING source_url
    """

    insert_values = (
        post_name,
        department,
        organization,
        government_level,
        sector,
        district,
        state,
        advertisement_no,
        total_vacancies,
        apply_start_date,
        apply_last_date,
        source_url,
    )

    try:
        # Establish connection to PostgreSQL
        connection = psycopg2.connect(
            host=DB_CONFIG["host"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = connection.cursor()

        # Execute the parameterized insert statement
        cursor.execute(insert_query, insert_values)

        # Commit transaction regardless of insert or conflict
        connection.commit()

        # If RETURNING produced a row, a new record was inserted
        inserted_row = cursor.fetchone()
        return inserted_row is not None

    except Exception as e:
        # Re-raise the exception after cleanup so callers can handle it
        raise

    finally:
        # Ensure resources are always released
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    # Example usage of insert_job for local development.
    inserted = insert_job(
        post_name="Test Clerk",
        department="Revenue Department",
        organization="Test Organization",
        government_level="State",
        sector="Administration",
        district="Kanpur Nagar",
        state="Uttar Pradesh",
        advertisement_no="TEST-001",
        total_vacancies=10,
        apply_start_date="2026-06-20",
        apply_last_date="2026-07-20",
        source_url="https://example.com/test-job"
    )

    if inserted:
        print("Record inserted successfully!")
    else:
        print("Record already exists; no insert performed.")
