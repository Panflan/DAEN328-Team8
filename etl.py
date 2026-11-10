from helpers import get_cdc_connection, create_cdc_tables
from extract import Extractor, CDC
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

etl_logger = logging.getLogger(__name__)

def main():
    etl_logger.info("ETL container started")

    etl_logger.info("Connecting to CDC Postgres Database...")
    conn = get_cdc_connection()
    etl_logger.info("Connected to CDC Postgrest Database")

    etl_logger.info("Creating CDC tables...")
    create_cdc_tables(conn)
    etl_logger.info("CDC tables created")

    etl_logger.info("Initializing CDC run...")
    cdc_run = CDC(conn)
    etl_logger.info(f"CDC run initiated with run_id = {cdc_run.run_id}")

    etl_logger.info("Setting up extractor for new snapshot...")
    extractor = Extractor(
        headers = {
            "Accept": "application/json"
        },
        batch_size = 10000
    )
    etl_logger.info("New extractor set up")

    etl_logger.info("Initializing new snapshot extraction")

    while True:
        batch = extractor.get_batch()

        if not batch:
            break

        extractor.dump_batch(batch)
        cdc_run.process_batch(batch)

    deleted_count = cdc_run.process_deletions()
    cdc_run.finish_run() 
    extractor.logger.info(f"{deleted_count} records deleted between previous snapshot and current snapshot")

    etl_logger.info("Snapshot extraction complete")

    etl_logger.info("Closing CDC connection...")
    conn.close()
    etl_logger.info("CDC Postgres connection closed")

if __name__ == "__main__":
    main()
