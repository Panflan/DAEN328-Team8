"""Run the NYC 311 ETL pipeline."""

from extract import extract_data
from helpers import create_tables, get_connection, save_state
from load import load_records


def main():
    print("ETL run started: NYC 311 service requests")
    connection = get_connection()

    try:
        create_tables(connection)

        records, last_updated, last_id = extract_data()

        # This uses Anthony's transform function after transform.py is merged.
        try:
            from transform import transform_data
            records = transform_data(records)
        except ModuleNotFoundError:
            print("transform.py is not in the project yet; loading the extracted records")

        stats = load_records(records, connection)

        # Save the checkpoint only after the database load succeeds.
        if last_updated and last_id:
            save_state("nyc_311_extract", last_updated, last_id)

        print(f"received from API: {stats['received']}")
        print(f"duplicate input rows removed: {stats['duplicate_input_rows']}")
        print(f"rows skipped because data was missing: {stats['skipped']}")
        print(f"service_requests inserted: {stats['inserted']}")
        print(f"service_requests updated: {stats['updated']}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
