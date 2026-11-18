from helpers import (
    get_cdc_connection,
    create_cdc_tables,
    create_psql_tables,
    get_connection,
    load_incremental_state,
    save_incremental_state
)
from extract import Extractor, CDC
import logging
import os
from load import load_records, delete_records

from transform import transform_batch, COLUMNS
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

etl_mode = os.getenv("ETL_MODE", "incremental")

etl_logger = logging.getLogger(__name__)

def main():

    etl_logger.info("ETL container started")

    try:
        etl_logger.info("Connecting to CDC Postgres Database...")
        cdc_conn = get_cdc_connection()
        etl_logger.info("Connected to CDC Postgrest Database")


        etl_logger.info("Creating CDC tables...")
        create_cdc_tables(cdc_conn)
        etl_logger.info("CDC tables created")


        etl_logger.info("Initializing CDC run...")
        cdc_run = CDC(cdc_conn)
        etl_logger.info(f"CDC run initiated with run_id = {cdc_run.run_id}")

        etl_logger.info("Connecting to Main Postgres Database...")
        conn = get_connection()
        etl_logger.info("Connected to Main Postgrest Database")

        etl_logger.info("Creating Main PSQL tables...")
        create_psql_tables(conn)
        etl_logger.info("Main PSQL tables created")

        etl_logger.info("Setting up extractor for new snapshot...")

        if etl_mode == "full":
            last_incremental = None
            etl_logger.info("ETL MODE: full extraction")
        else:
            last_incremental = load_incremental_state(cdc_conn)
            etl_logger.info(f"Last incremental extraction state: {last_incremental}")

        extractor = Extractor(
            headers = {
                "Accept": "application/json"
            },
            batch_size = 25000,
            incremental_since = last_incremental
        )
        etl_logger.info("New extractor set up")


        etl_logger.info("Initializing new snapshot extraction")

        cleaning_stats = Counter() 

        while True:
            batch = extractor.get_batch()

            if not batch:
                break

            extractor.dump_batch(batch)
            cdc_run.process_batch(batch)

            cleaned_batch = transform_batch(batch, cleaning_stats)

            if cleaned_batch:
                load_records(cleaned_batch, conn)

        if etl_mode == "full":
            deleted_ids = cdc_run.process_deletions()
            deleted_count = delete_records(deleted_ids, conn)
        else: 
            deleted_count = 0

        etl_logger.info(f"{deleted_count} records deleted from main database")

        cdc_run.finish_run(cdc_conn, cdc_run.run_id)


        etl_logger.info("Snapshot extraction complete")

    finally:

        if extractor.last_created_date is not None:
            save_incremental_state(cdc_conn, extractor.last_created_date)
            etl_logger.info(f"Incremental extraction state saved: {extractor.last_created_date}")

        etl_logger.info("Closing CDC connection...")
        cdc_conn.close()
        etl_logger.info("CDC Postgres connection closed")

        etl_logger.info("Closing Main Postgres Database connection...")
        conn.close()
        etl_logger.info("Main Postgres Database connection closed")

        etl_logger.info("Main PSQL connection closed")
        etl_logger.info("Tranformation and Cleaning Complete!")
        etl_logger.info(f"Records received: {cleaning_stats['received']}")
        etl_logger.info(f"Records cleaned: {cleaning_stats['cleaned']}")
        etl_logger.info(f"Duplicates removed: {cleaning_stats['duplicates']}")
        etl_logger.info(f"Invalid IDs: {cleaning_stats['invalid_id']}")

        for col in COLUMNS:
            if cleaning_stats[f"missing_{col}"]:
                etl_logger.info(
                    f"Missing {col}: {cleaning_stats[f'missing_{col}']}"
                )

if __name__ == "__main__":
    main()
