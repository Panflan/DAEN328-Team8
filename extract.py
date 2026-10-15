import requests
import json
import os
from dotenv import load_dotenv

# ==================================== #
# HELPER FUNCTIONS                     #
# ==================================== #
def save_state(timestamp, record_id):
    '''
    Saves last successfully extracted record
    '''

    with open(state_path, "w") as file:
        json.dump({
            "last_updated": timestamp,
            "last_id": record_id
        }, file, indent=4)

def load_state():
    '''
    Loads last successfully extracted record

    Returns:
        tuple:
            (last_updated, last_id)

        If no state exists:
            (None, None)
    '''

    if os.path.exists(state_path):
        
        with open(state_path, "r") as file:
            state = json.load(file)

        return (
            state.get("last_updated"),
            state.get("last_id")
        )

    return None, None


# ==================================== #
# ENVIRONMENT VARIABLES & CONSTANTS    #
# ==================================== #

load_dotenv() # Loads all environmental variables from your .env file

url = os.getenv("API_ENDPOINT") # Chicago PD Crime Dataset

data_path = os.getenv("RAW_DATA") # File path for the raw json data

state_path = os.getenv("STATE_FILE") # File path for raw data state file

LIMIT = 10000 # For pagination, batch size per extract

offset = 0 # For pagination, chooses which rows to gather

last_updated, last_id = load_state() # For pagination, loads current data write's state

headers = {"Accept": "application/json"} # Clarifies the data is retrieved as json

batch_num = 0 # For logging number of batches processed during a loop

total_records = 0 # For logging number of records processed during a loop


# ==================================== #
# LOCAL SAVE WIPE (for debugging)      #
# ==================================== #
del_local_data = input("Delete the current local save of the raw data? (y/n)").lower().strip()

while True:

    if del_local_data == "y":
        os.remove(data_path)
        print("Local data removed! Proceeding to extraction")
        break

    elif del_local_data == "n":
        print("Local data conserved! Appending new extractions")
        break

    else:
        del_local_data = input("Invalid character, try again with \"y\" or \"n\"")




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
        last_updated,
        last_id
    )

    # No new records need to be retrieved if batch size is less than the limit
    if len(batch) < LIMIT:
        break


print(f"Extraction complete | {total_records} records fetched")







