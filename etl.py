import os
import psycopg2
from helpers import get_connection, create_tables
from extract import extract_data


def main():
    print("ETL container started.")

    print("Connecting to PostgreSQL...")
    connection = get_connection()
    print("Succesfully connected to PostgreSQL")

    create_tables(connection)

    connection.close()

    extract_data()

if __name__ == "__main__":
    main()
