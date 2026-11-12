"""Get NYC 311 records from the public API."""

import json
import os
import time

import requests
from dotenv import load_dotenv

from helpers import load_state


def extract_data():
    """Get the first sample or only records with a new unique key."""
    load_dotenv()

    url = os.getenv("API_ENDPOINT")
    raw_data_path = os.getenv("RAW_DATA", "data/nyc_311_raw.jsonl")
    batch_size = int(os.getenv("BATCH_SIZE", "10000"))
    initial_limit = int(os.getenv("INITIAL_LOAD_LIMIT", "50000"))

    if not url:
        raise ValueError("API_ENDPOINT is missing from .env")

    last_updated, last_id = load_state("nyc_311_extract")
    first_run = last_id is None
    page_cursor = None
    records = []

    while True:
        if first_run:
            limit = min(batch_size, initial_limit - len(records))
            order = "unique_key DESC"
        else:
            limit = batch_size
            order = "unique_key ASC"

        params = {
            "$select": "*,:updated_at",
            "$limit": limit,
            "$order": order,
        }

        if first_run and page_cursor is not None:
            params["$where"] = f"unique_key < '{page_cursor}'"
        elif not first_run:
            params["$where"] = f"unique_key > '{last_id}'"

        # Try up to three times because a public API can be temporarily unavailable.
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                break
            except requests.RequestException as error:
                if attempt == 2:
                    raise RuntimeError(f"NYC 311 API request failed: {error}") from error
                print("API request failed. Trying again...")
                time.sleep(2)

        batch = response.json()
        if not batch:
            break

        records.extend(batch)

        if first_run:
            # The first row has the largest key because the API is sorted descending.
            if last_id is None:
                last_id = int(batch[0]["unique_key"])
                last_updated = batch[0][":updated_at"]
            page_cursor = batch[-1]["unique_key"]
        else:
            # The last row has the largest key because the API is sorted ascending.
            last_id = int(batch[-1]["unique_key"])
            last_updated = batch[-1][":updated_at"]

        if len(batch) < limit:
            break
        if first_run and len(records) >= initial_limit:
            break

    if records:
        os.makedirs(os.path.dirname(raw_data_path) or ".", exist_ok=True)
        with open(raw_data_path, "w", encoding="utf-8") as raw_file:
            for record in records:
                raw_file.write(json.dumps(record) + "\n")

    return records, last_updated, last_id
