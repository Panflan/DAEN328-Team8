# NYC 311 Service Requests ETL Data Pipeline

Howdy! This is *Team 8's* GitHub repository for our term project in Dr. Mark Lawley's DAEN 328 - Section 500 class. The goal of this project is to create a well-designed ETL data pipeline that extracts data from the "NYC 311 Service Requests from 2020 to Present" dataset API, cleans/normalizes/transforms the data, loads the data into PostgreSQL, & serves data-driven analytics to the end user via a Streamlit dashboard.

## DISCLAIMER
DO NOT COMMIT TO THE MAIN BRANCH YET. MAKE YOUR OWN BRANCH AND WORK THROUGH THERE. [Information on how to do that can be found here.](https://docs.github.com/en/pull-requests/how-tos/commit-changes/managing-branches-within-your-repository)

## Table of Contents
* [Local Setup](#LocalSetup)
  * [Local Repository Access](#GettingLocalAccesstotheRepository)
  * [Environmental Variables](#EnvironmentalVariables)
  * [Docker Compose](#RunningtheProjectw/Docker)
* [Extraction](#Extraction)
* [Transformation](#Transformation)
* [Loading](#Loading)
* [Visualization](#Visualization)
* [ETL Orchestration](#ETLOrchestration)
* [Dockerization](#Dockerization)

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


## Extraction

## Transformation

## Loading

## Visualization

## ETL Orchestration

## Dockerization

