
# Extract-Transform-Load pipeline Project
This project is an end-to-end workflow which aims to query Eco2mix data on a regular basis, process it by applying multiple transformations, store it in a PostgreSQL database then load the data to a dashboard to visualize it interactively.

ECO2mix is a once an hour refreshed dataset, and presents “real-time” regional data from the eCO2mix application. They come from the telemetry of the structures, supplemented by packages and estimates.

You will find every quarter of an hour:

- The production according to the different sectors composing the energy mix.
- The consumption of pumps in Energy Transfer Pumping Stations (STEP).
- The balance of physical exchanges with neighboring regions.

For more information, follow this link: https://odre.opendatasoft.com/explore/dataset/eco2mix-regional-tr/information/?disjunctive.libelle_region&disjunctive.nature


# Project stack and architecture
![image](assets/data_pipeline_example.svg)

## Table of contents

- [Installation](#installation)
- [Run airflow and manage the dags](#Manage-tasks)
- [Visualize the data](#Visualize-data)
- [Contributing](#contributing)
- [Copyright and license](#copyright-and-license)




## Installation

### Prerequisites
This project requires Docker desktop and Docker Compose to be installed

### setup
Docker desktop should be running fo the following to work.
To install the project environment just run the following command:
```
docker-compose up
```

On code change you might need to run these commands:
```
docker-compose down
docker-compose up -d --build
```

## Running airflow and managing dags
Once the installation completed, open AirFlow's web UI:
```
http://localhost:8080/login
```

Use these credentials to login: 
- login: airflow
- pwd: airflow

Click on the DAGS button then activate the "process-energy" dag and click on the play icon to trigger manually the dag. 

## Visualize the data
Once the dag has ran successfully, open the dashboard to visualize the data:
```
http://localhost:8000
```
## Contributing

We welcome contributions to the project If you find a bug or
something is unclear please submit a bug report.

## Copyright and license

Released under the [MIT license](LICENSE.txt)

