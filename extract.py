import requests
import json

# Chicago PD Crime Dataset
url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

headers = {"Accept": "application/json"} # Get the data in JSON format
response = requests.get(url, headers = headers) 

if response.status_code == 200:
    data = response.json()

    with open("data/imported_data.json", "w", encoding = "utf-8") as file:
        json.dump(data, file, indent = 4)
    print("Data fetch successful!")

else:
    print("Failed to fetch data.")
    print(f"Status Code: {response.status_code}") # Tells us what went wrong