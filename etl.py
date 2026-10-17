import os
import psycopg2

def create_tables(connection):

    # Reads the schema file with all of the postgres tables
    with open("schema.sql", "r") as file:
        schema = file.read()

    # Executes the table creation in postgres
    with connection.cursor() as cursor:
        cursor.execute(schema)

    connection.commit()

def main():
    print("ETL container started.")

    print("Connecting to PostgreSQL...")

    connection = psycopg2.connect(
        host = os.getenv("POSTGRES_HOST"),
        port = os.getenv("POSTGRES_PORT"),
        dbname = os.getenv("POSTGRES_DB"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD")
    )

    print("Succesfully connected to PostgreSQL")

    create_tables(connection)

    connection.close()

if __name__ == "__main__":
    main()