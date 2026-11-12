# Chicago Crime Data Streamlit Dashboard - DAEN 328 Team 8 - Texas A&M University
Howdy! This is Team 8's GitHub repository for our term project in Mark Lawley's DAEN 328 - Section 500 class. The goal of this project is to create a well-designed ETL program for the crime data from the city of Chicago, where the final live-updating dashboard will be built on the StreamLit library in Python.

## DISCLAIMER
DO NOT COMMIT TO THE MAIN BRANCH YET. MAKE YOUR OWN BRANCH AND WORK THROUGH THERE. [Information on how to do that can be found here.](https://docs.github.com/en/pull-requests/how-tos/commit-changes/managing-branches-within-your-repository)

## Table of Contents
***I'll do later, I'm lazy***

## Local Setup
### Getting Local Access to the Repository 
To gain access to the most up to date versions of the source files from the main branch on your machine, go to your terminal (on MacOS/Linux) or your VSCode terminal (on Windows). Navigate to the directory you'd like to clone into with
```bash
cd /directory/location/here/...
```
Once you are in the preferred directory, clone the repository into it using the command:
```bash
git clone https://github.com/Panflan/DAEN328-Team8.git
```
If you have an SSH key pair configured between your local machine and your GitHub account, you can also use:
```bash
git clone git@github.com:Panflan/DAEN328-Team8.git
```
At this point you should be able to run the project locally, if any issues are encountered, [consult this page](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

### Environmental Variables
No API keys or secrets are needed for the project at the moment. `.env.example` provides the necessary structure for your local `.env` file. You will need the API endpoint link (in the example file), a directory path for where you would like to store the raw data, and your postgres credentials

### Running the Project w/Docker
In order to test the project, you need to have *Docker Desktop* installed, [you can find the download here](https://www.docker.com/products/docker-desktop/). When trying to run tests on the project, you must have docker desktop open in the background so that the *docker daemon* is awake. Once you have opened docker desktop, you can enter the following command into your terminal to run the project:
```bash
docker compose up --build
```
If you are unfamiliar with the terminal, know that you can always stop the docker process by pressing `ctrl + C`

### Python Setup
When trying to test the project, all files run through the `etl.py` docker container. This means that all other files in the project must have a wrapper (e.g., all data transform functionality from the `transform.py` file must be wrapped in a single function like `transform()`), and then the wrapper function must be inserting into `etl.py` after all dependent code. Additionally, each wrapper function added to `etl.py` must be imported from its respective file, for example:
```python
from helpers import get_connection, create_tables
from extract import extract_data
from transform import transform_data
```
For docker to run the file correctly, you must also insert the names of any third-party (not python native) libraries/modules being used into `requirements.txt`. Otherwise the container will not download the necessary packages.
