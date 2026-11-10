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


