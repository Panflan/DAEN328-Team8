import os
import psycopg2


def get_connection():
    return psycopg2.connect(
        host = os.getenv("POSTGRES_HOST"),
        port = os.getenv("POSTGRES_PORT"),
        dbname = os.getenv("POSTGRES_DB"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD")
    )

def create_tables(connection):

    # Reads the schema file with all of the postgres tables
    with open("schema.sql", "r") as file:
        schema = file.read()

    # Executes the table creation in postgres
    with connection.cursor() as cursor:
        cursor.execute(schema)

    connection.commit()

def load_state(pipeline_name):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT last_updated, last_id
                FROM etl_state
                WHERE pipeline_name = %s;
                """, (
                    pipeline_name,
                )
            )

            row = cursor.fetchone()

        if row is None:
            return None, None

        return row[0], row[1]

    finally:
        connection.close()


def load_state(pipeline_name):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT last_updated, last_id
                FROM etl_state
                WHERE pipeline_name = %s;
                """, (
                    pipeline_name,
                )
            )

            row = cursor.fetchone()

        if row is None:
            return None, None

        return row[0], row[1]

    finally:
        connection.close()


def save_state(pipeline_name, last_updated, last_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO etl_state (
                    pipeline_name,
                    last_updated,
                    last_id
                )
                VALUES (%s, %s, %s)

                ON CONFLICT (pipeline_name)
                DO UPDATE SET
                    last_updated = EXCLUDED.last_updated,
                    last_id = EXCLUDED.last_id;
                """, (
                    pipeline_name,
                    last_updated,
                    last_id
                )
            )

        connection.commit()

    finally:
        connection.close()