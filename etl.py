from helpers import get_cdc_connection, create_cdc_tables, create_psql_tables, get_connection
from extract import Extractor, CDC
import logging
from load import load_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

etl_logger = logging.getLogger(__name__)

def main():

    etl_logger.info("ETL container started")


    etl_logger.info("Connecting to CDC Postgres Database...")
    cdc_conn = get_cdc_connection()
    etl_logger.info("Connected to CDC Postgrest Database")


    etl_logger.info("Creating CDC tables...")
    create_cdc_tables(cdc_conn)
    etl_logger.info("CDC tables created")


    etl_logger.info("Initializing CDC run...")
    cdc_run = CDC(cdc_conn)
    etl_logger.info(f"CDC run initiated with run_id = {cdc_run.run_id}")


    etl_logger.info("Setting up extractor for new snapshot...")
    extractor = Extractor(
        headers = {
            "Accept": "application/json"
        },
        batch_size = 100000
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
    cdc_conn.close()
    etl_logger.info("CDC Postgres connection closed")

    etl_logger.info("Connecting to Main Postgres Database...")
    conn = get_connection()
    etl_logger.info("Connected to Main Postgrest Database")

    etl_logger.info("Creating Main PSQL tables...")
    create_psql_tables(conn)
    etl_logger.info("Main PSQL tables created")

    # -- ADD TRANSFORMATION STUFF HERE, THEN CONNECT TO MASONS LOAD -- #

if __name__ == "__main__":
    main()
