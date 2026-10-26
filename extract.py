import requests
import json
import os

from dotenv import load_dotenv
from helpers import load_state, save_state


def extract_data():
    # ==================================== #
    # ENVIRONMENT VARIABLES & CONSTANTS    #
    # ==================================== #

    load_dotenv() # Loads all environmental variables from your .env file

    url = os.getenv("API_ENDPOINT") # Chicago PD Crime Dataset

    data_path = os.getenv("RAW_DATA") # File path for the raw json data

    LIMIT = 100 # For pagination, batch size per extract

    offset = 0 # For pagination, chooses which rows to gather

    last_updated, last_id = load_state("crime_extract") # For pagination, loads current data write's state

    # To convert from default (python datetime) to str
    if last_updated is not None:
        last_updated = last_updated.isoformat()

    headers = {"Accept": "application/json"} # Clarifies the data is retrieved as json

    batch_num = 0 # For logging number of batches processed during a loop

    total_records = 0 # For logging number of records processed during a loop



    # ==================================== #
    # PAGINATED EXTRACTION LOOP            #
    # ==================================== #
    while True:

        # Sets the parameters for pagination
        params = {
            '$limit': LIMIT,
            '$order': 'updated_on ASC, id ASC'
            # ^ Sorts from most the lowest id on the oldest update to the highest id on the newest update
        }

        # Sets params after checkpoint is achieved
        if last_updated is not None:

            params["$where"] = (
                f"updated_on > '{last_updated}' "
                f"OR "
                f"(updated_on = '{last_updated}' AND id > {last_id})"
            )

        # Extracts the data
        response = requests.get(
            url, 
            params = params,
            headers = headers
        )

        if batch_num == 0:
            request = response.request

            print(f"--- REQUEST ---")
            print(f"-- {request.method}:/resource/ijzp-q8t2.json?...")
            print(f"-- Host: data.cityofchicago.org")
            print(f"---------------")

            print('\n')

            print("--- RESPONSE ---")
            print(f"-- HTTP/1.1 {response.status_code} {response.reason}")
            k = 0
            for key, value in response.headers.items():
                k += 1
                if k > 6:
                    break
                print(f"-- {key}: {value}")
            print(f"---------------\n")

        # If extraction fails, prints trace and breaks pagination loop
        if response.status_code != 200:
            print("Failed to fetch data.")
            print(f"Status Code: {response.status_code}")
            print(response.text)
            break

        batch_num += 1

        batch = response.json() # Converts the data to json

        # Breaks loop when there are no more records left to extract
        if len(batch) == 0:
            break



    # ==================================== #
    # WRITING BATCH DATA TO STORAGE        #
    # ==================================== #

        # Writes the extracted data to raw data json file
        with open(data_path, "a", encoding="utf-8") as file:

            for record in batch:
                file.write(json.dumps(record) + "\n") # Appends new record to file


        total_records += len(batch) # Updates the total number of records

        print(
            f"Fetched {len(batch)} records {f"({batch_num})":>2} )"
            f"| Total: {total_records}"
        )

    # ==================================== #
    # UPDATE CHECKPOINT                    #
    # ==================================== #

        last_record = batch[-1] # Gets the last record in the batch

        # Gets the update time & id on the last record
        last_updated = last_record["updated_on"]
        last_id = last_record["id"]

        # Saves current state of the data for pagination
        save_state(
            "crime_extract",
            last_updated,
            last_id
        )

        # No new records need to be retrieved if batch size is less than the limit
        if len(batch) < LIMIT:
            break


    print(f"Extraction complete | {total_records} records fetched")

if __name__ == "__main__":
    extract_data()







