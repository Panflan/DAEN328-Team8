#cleaning data
import json
import logging
import re
from datetime import datetime #the data has timestamp
from collections import Counter


RAW_PATH = "data/raw_data.json"
CLEAN_PATH = "data/cleaned_data.json"

#Fields for the dashboard/database
COLUMNS = [
    "unique_key","created_date","closed_date","agency",
    "agency_name","complaint_type","descriptor","location_type",
    "incident_zip","incident_address","street_name","city","status", 
    "resolution_description","resolution_action_updated_date",
    "community_board","council_district","police_precinct","borough",
    "open_data_channel_type","latitude","longitude"
]

TEXT_COLUMNS = [
    "agency","agency_name","complaint_type","descriptor",
    "location_type","incident_address","street_name","city",
    "status","community_board","police_precinct",
    "borough","open_data_channel_type"

]

"""
not in list:
cross_street_1, cross_street_2, intersection_street_1, 
intersection_street_2, address_type, bbl, x_coordinate_state_plane,
y_coordinate_state_plane, park_facility_name, park_borough, location
"""

def date_time_format(record): #make sure to change this based on new dtataset
    date_col = [
        "created_date",
        "closed_date",
        "resolution_action_updated_date"
    ]
    
    for col in date_col:
            value = record.get(col)
            if value is None or value == "":
                continue
            try:
                dt = datetime.fromisoformat(record[col])
                record[col] = dt.isoformat(timespec="seconds")
            except (ValueError, TypeError):
                record[col] = None
    return record

def missing_values(record):
    #set as either null/none or 
    #try to find from other columns
    for col, value in record.items():
        if isinstance(value, str) and not value.strip():
            record[col] = None
    return record

def duplicates(record, seen_ids):
    record_id = record.get("unique_key")

    if record_id in seen_ids:
        return True
    
    seen_ids.add(record_id)
    return False

def standardization(record):
    for col in TEXT_COLUMNS:
        value = record.get(col)
        if isinstance(value, str):
            value = " ".join(value.split())

            if col in ["agency", "city", "borough", "community_board", 
                   "open_data_channel_type", "incident_address",
                   "street_name"]:
                value = value.upper()
            record[col] = value
    return record

def convert_types(record):
    record["unique_key"] = int(record["unique_key"])

    for col in ("latitude", "longitude"):
        value = record.get(col)

        if value is not None:
            try:
                record[col] = float(value)
            except (ValueError, TypeError):
                record[col] = None
    #keep ZIP codes, district codes, etc. as strings
    #they potentially may contain leading zeros

    return record


def column_drop(record):
    return {
        col: record.get(col)
        for col in COLUMNS
    }

def transform_batch(batch, stats=None):
    if stats is None:
        stats = Counter()

    cleaned_batch = []
    seen_ids = set()

    for record in batch:
        stats["received"] += 1

        record = record.copy()

        record_id = record.get("unique_key")

        if not str(record_id or "").isdigit():
            stats["invalid_id"] += 1
            continue

        #removes duplicates
        if duplicates(record, seen_ids):
            stats["duplicates"] += 1
            continue

        #this section applies separate cleaning functions
        record = column_drop(record)
        record = missing_values(record)
        record = standardization(record)
        record = convert_types(record)
        record = date_time_format(record)

        for col, value in record.items():
            if value is None:
                stats[f"missing_{col}"] += 1
        cleaned_batch.append(record)
        stats["cleaned"] += 1
    return cleaned_batch

def transform_data(max_records=None):
    stats = Counter()

    with open(RAW_PATH, "r", encoding="utf-8") as raw_file:
        with open(CLEAN_PATH, "w", encoding="utf-8") as clean_file:
            batch = []
            
            for line in raw_file:
                if max_records is not None and stats["received"] >= max_records:
                    break
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    stats["invalid_json"] += 1
                    continue

                batch.append(record)

                if len(batch) >= 1000:
                    cleaned = transform_batch(batch, stats)

                    for record in cleaned:
                        clean_file.write(json.dumps(record) + "\n")
                    batch = []

            if batch:
                cleaned = transform_batch(batch, stats)

                for record in cleaned:
                    clean_file.write(json.dumps(record) + "\n")

            logging.info(f"Transformation complete.")
            logging.info("Rows received: %s", stats["received"])
            logging.info("Rows cleaned: %s", stats["cleaned"])
            logging.info("Duplicates removed: %s", stats["duplicates"])
            logging.info("Invalid IDs: %s", stats["invalid_id"])
            logging.info("Invalid JSON: %s", stats["invalid_json"])

            for col in COLUMNS:
                if stats[f"missing_{col}"]:
                    logging.info("Missing %s: %s", 
                                 col, 
                                 stats[f"missing_{col}"])
            return stats
        
#temp testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s"
    )

    transform_data(max_records=10000)
