import os
import psycopg2
from dotenv import load_dotenv

def get_connection():
    load_dotenv()
    return psycopg2.connect(
        host = os.getenv("PSQL_HOST"),
        port = os.getenv("PSQL_PORT"),
        dbname = os.getenv("PSQL_DB"),
        user = os.getenv("PSQL_USER"),
        password = os.getenv("PSQL_PASSWORD")
    )

def get_cdc_connection():
    load_dotenv()
    return psycopg2.connect(
        host = os.getenv("CDC_HOST"),
        port = os.getenv("CDC_PORT"),
        dbname = os.getenv("CDC_DB"),
        user = os.getenv("CDC_USER"),
        password = os.getenv("CDC_PASSWORD")
    )

def create_cdc_tables(cdc_conn):

    # Reads the schema file with all of the postgres tables
    with open("sql/cdc_schema.sql", "r") as file:
        schema = file.read()

    # Executes the table creation in postgres
    with cdc_conn.cursor() as cursor:
        cursor.execute(schema)

    cdc_conn.commit()

def create_psql_tables(psql_conn):

    # Reads the schema file with all of the postgres tables
    with open("sql/psql_schema.sql", "r") as file:
        schema = file.read()

    # Executes the table creation in postgres
    with psql_conn.cursor() as cursor:
        cursor.execute(schema)

    psql_conn.commit()


def load_incremental_state(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT state_value
            FROM extraction_state
            WHERE state_key = 'last_incremental_created_date';
            """
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return row[0]


def save_incremental_state(conn, created_date):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO extraction_state (
                state_key,
                state_value
            )
            VALUES (
                'last_incremental_created_date',
                %s
            )
            ON CONFLICT (state_key)
            DO UPDATE SET
                state_value = EXCLUDED.state_value;
            """,
            (created_date,)
        )

    conn.commit()
