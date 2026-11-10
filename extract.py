import requests
import json
import os
import logging
import hashlib

from helpers import get_cdc_connection

from urllib.parse import urlparse
from dotenv import load_dotenv

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

class Extractor:

    def __init__(self, headers: dict[str, str] , batch_size: int):
        """ 
        Instantiates an `Extractor()` object, which has attributes:
            `endpoint` - API endpoint URL
            `dump_path` - File path for where the extracted data will be stored
            `rq_headers` - HTTP headers for the extraction request
            `batch_size` - Size of each paginated batch
            `records_pulled` - The number of records pulled from the API by this specific extractor
            `records_processed` - The number of records written to JSON for cleaning
            `last_created_date` - The 'created_date' field of the last record pulled
            `last_unique_key` - The 'unique_key' field of the last record pulled
            `logger` - Extractor specific logger

        Args:
            headers: HTTP headers for the extraction request
            batch_size: Size of each paginated batch
        
        """

        load_dotenv()

        self.endpoint = os.getenv("API_ENDPOINT")
        self.dump_path = os.getenv("RAW_DATA")
        self.rq_headers = headers
        self.batch_size = batch_size

        self.records_pulled = 0
        self.records_processed = 0

        self.last_created_date = None
        self.last_unique_key = None

        self.logger = logging.getLogger(__name__)




    def get_batch(self):
        """
        Calls the NYC API

        Returns a response object from the `requests` module
        """
        self.logger.info(f"Sending GET request for up to {self.batch_size} records")

        # Sorts data from lowest to highest unique key & by most recent date
        params = {
            '$limit': self.batch_size,
            '$order': 'created_date ASC, unique_key ASC' 
        }

        # If the Extractor has a pagination state stored, check against it
        if self.last_created_date is not None:
            params["$where"] = (
                f"created_date > '{self.last_created_date}' "
                f"OR "
                f"(created_date = '{self.last_created_date}' "
                f"AND unique_key > '{self.last_unique_key}')"
            )

        try:
            response = requests.get(
                self.endpoint,
                params=params,
                headers=self.rq_headers,
                timeout=30
            )

            response.raise_for_status()

        except requests.exceptions.Timeout:
            self.logger.error("API request timed out")
            raise

        except requests.exceptions.ConnectionError:
            self.logger.error("Could not connect to API")
            raise

        except requests.exceptions.HTTPError as e:
            self.logger.error(
                "API returned HTTP error %s: %s",
                response.status_code,
                e
            )
            raise

        except requests.exceptions.RequestException as e:
            self.logger.error("Unexpected request error: %s", e)
            raise

        request = response.request
        parsed = urlparse(request.url)

        # If the extractor is new, print the HTTP request and response for the first pull only
        if self.records_pulled == 0:
            log_string = (
                "\n"
                "\n--- REQUEST ---\n"
                f"--- {request.method} {request.path_url} HTTP/1.1\n"
                f"--- Host: {parsed.netloc}\n"
                "-----------------\n"
                "\n"
                "--- RESPONSE ---\n"
                f"--- HTTP/1.1 {response.status_code} {response.reason}\n"
            )

            k = 0
            for key, value in response.headers.items():
                k += 1
                if k > 6:
                    break
                log_string += f"--- {key}: {value}\n"

            log_string += f"---------------"
            log_string += f"\n"

            self.logger.info(log_string)

        batch = response.json()

        self.records_pulled += len(batch)

        if batch:
            last_record = batch[-1]

            self.last_created_date = last_record["created_date"]
            self.last_unique_key = last_record["unique_key"]

            self.logger.info(f"Pagination state updated - last_created_date: {self.last_created_date}")

        else:
            self.logger.info("No additional records returned; extraction complete")


        return batch

    def dump_batch(self, batch):
        """
        Writes batch from response to JSON

        Args:
            batch: batch from `get_batch` method
        """

        self.logger.info(f"Writing {len(batch)} records to JSON @ {self.dump_path}")

        with open(self.dump_path, "w", encoding="utf-8") as file:
            for record in batch:
                    file.write(json.dumps(record) + "\n") # Appends new record to file

        self.records_processed += len(batch)

        self.logger.info(f"Batch written to {self.dump_path}, {self.records_processed} records processed total")


class CDC:

    def __init__(self, conn):
        """
        Instantiates an `CDC()` object, a wrapper around the CDC logger & state classes. Has attributes:
            `logger` - The `Logger()` object for CDC logging
            `state` - The `State()` object for CDC state-keeping
            `run_id` - The run id for this specific CDC object
        """
        self.logger = CDCLogger()
        self.state = CDCState()
        self.conn = conn


        # Starts new run associated with this CDC object
        with self.conn as conn:
            self.run_id = self.state.start_run(conn)


    def process_batch(self, batch):
        """
        Intakes a batch, creates new state hashes for new records, checks and updates existing state hashes if necessary

        Args:
            batch: a json response from the API
        """

        # If a batch is not passed in, return nothing
        if not batch:
            return

        # Gets all unique keys in the batch
        src_ids = [
            record["unique_key"]
            for record in batch
        ]
        
        with self.conn as conn:

            # Gets the existing state for the entire batch
            existing = self.state.get_existing(conn, src_ids) 

            state_updates = []
            changes = []

            for record in batch:

                # Gets the source id & calculates new state hash
                src_id = record["unique_key"]
                new_hash = self.state.calculate_hash(record)
                
                # Gets the prexisting active status
                previous = existing.get(src_id)

                # If there is no active status associated with the record, then it is a new record, log (id, INSERT)
                if previous is None:
                    operation = "INSERT"
                    changes.append((src_id, operation))

                else:
                    # Splits the individual fields of the `previous` tuple
                    old_hash, is_active = previous

                    # If pre-existing activity state is false, then the record was restored, log (id, RESTORE)
                    if not is_active:
                        operation = "RESTORE"
                        changes.append((src_id, operation))

                    # If old hash doesn't equal new hash, then the record has been altered, log (id, UPDATE)
                    elif old_hash != new_hash:
                        operation = "UPDATE"
                        changes.append((src_id, operation))

                # Regardless of what operation is performed, the last-known state is updated
                state_updates.append((src_id, new_hash))

            # Update the state table
            self.state.update_state(conn, state_updates, self.run_id)

            # Write only the actual changes to the log
            self.logger.log_changes(conn, changes)

            # Commit the current set of changes
            conn.commit()


    def process_deletions(self):
        """
        Processess the deletions that have occured after the conclusion of all batch processing for the current run
        """

        with self.conn as conn:
            
            # Gets the source ids of the pre-existing records that were deleted in this run
            deleted_ids = self.state.get_deleted(conn, self.run_id)

            # Returns 0 if there are no deleted ids (for logging purposes)
            if not deleted_ids:
                return 0
            
            # Creates a list of (id, "DELETE") tuples
            deletions = [
                (src_id, "DELETE")
                for src_id in deleted_ids
            ]

            # Logs the deletions to the CDC change log
            self.logger.log_changes(conn, deletions)

            # Changes the active state of the deleted records from TRUE to FALSE
            self.state.mark_deleted(conn, deleted_ids)

            conn.commit()

        # Returns the number of deleted ids (for logging purposes)
        return len(deleted_ids)

    def finish_run(self, conn, run_id: int):
        """
        Changes the run state in the CDC PSQL database to completed

        Args:
            conn: CDC PSQL database connection
            run_id: the run id for this CDC run
        """
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE cdc_runs
                SET completed_at = CURRENT_TIMESTAMP
                WHERE run_id = %s;
                """,
                (run_id,)
            )





class CDCLogger:

    def log_changes(self, conn, changes: list[tuple[str,str]]):
        """
        Logs CDC events to the CDC change log table in the PSQL database

        Args:
            conn: CDC PSQL database connection
            changes: an array of tuples containing the source id and the operation performed
        """

        with conn.cursor() as cursor:
            for source_id, operation in changes:
                cursor.execute(
                    """
                    INSERT INTO cdc_change_log (source_id, operation)
                    VALUES (%s, %s);
                    """, 
                    (source_id, operation)
                ) 

class CDCState:

    def calculate_hash(self, record: dict) -> str:
        """
        Normalizes an entire JSON record and then creates a unique SHA256 hash with it

        Args:
            record: the record for the batch to be hashed
        """
        # Normalizes contents for hash
        normalized = json.dumps(
            record,
            sort_keys = True,
            separators = (",", ":")
        )

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

    def start_run(self, conn) -> int:
        """
        Starts a unique CDC run in PSQL and returns the run id

        Args:
            conn: CDC PSQL database connection
        """

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cdc_runs DEFAULT VALUES
                RETURNING run_id;
                """
            )

            run_id = cursor.fetchone()[0]

        conn.commit()

        return run_id

    def get_existing(self, conn, src_ids: list[str]):
        """
        Returns the current known hashes for the requested source IDs

        Args:
            conn: CDC PSQL database connection
            src_ids: source IDs that we want the current hashes for
        """

        # If no source ids are passed, return nothing
        if not src_ids:
            return {}

        # Fetches the source ids and corresponding row hashes (if they exist)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id, row_hash, is_active
                FROM cdc_state
                WHERE source_id = ANY(%s);
                """,
                (src_ids,)
            )

            rows = cursor.fetchall()

        # Returns source ids and a tuple of row hashes/active statuses as a key-value pairs 
        return {
            src_id: (row_hash, is_active)
            for src_id, row_hash, is_active in rows
        }

    def update_state(self, conn, records: list[tuple[str,str]], run_id: int):
        """
        Inserts new CDC state records or updates existing ones 

        Args:
            conn: CDC PSQL database connection
            records: An array of tuples containing the source id and the new hash
            run_id: The run id of the parent `CDC()` object
        """

        with conn.cursor() as cursor:
            for src_id, row_hash in records:

                cursor.execute(
                    """
                    INSERT INTO cdc_state (source_id, row_hash, run_id, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    ON CONFLICT (source_id)
                    DO UPDATE SET
                        row_hash = EXCLUDED.row_hash, 
                        last_seen_at = CURRENT_TIMESTAMP, 
                        run_id = EXCLUDED.run_id,
                        is_active = TRUE;
                    """,
                    (src_id, row_hash, run_id)
                )

    def get_deleted(self, conn, run_id: int) -> list[str]:
        """
        Returns a list of pre-existing source ids that no longer existed in the current run

        Args:
            conn: CDC PSQL database connection
            run_id: The run id of the parent `CDC()` object
        """

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_id
                FROM cdc_state
                WHERE run_id <> %s AND is_active = TRUE;
                """,
                (run_id,)
            )

            rows = cursor.fetchall()

        return [
            src_id
            for (src_id,) in rows
        ]

    def mark_deleted(self, conn, src_ids: list[str]):
        """
        Sets the active status of all deleted records to FALSE 

        Args:
            conn: CDC PSQL database connection
            src_ids: list of source ids for deleted records
        """

        # Does nothing if no source ids are passed in
        if not src_ids:
            return

        # Updates active status to "FALSE"
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE cdc_state
                SET is_active = FALSE
                WHERE source_id = ANY(%s);
                """,
                (src_ids,)
            )

    

        







