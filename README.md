# Extract-Transform-Load Pipeline Project

A production-ready ETL pipeline that automatically extracts energy mix data from ECO2mix, transforms it with quality checks, and loads it into PostgreSQL for analysis and visualization.

## Overview

This project is an end-to-end workflow which aims to query ECO2mix data on a regular basis, process it by applying multiple transformations, store it in a PostgreSQL database, and load the data to a visualization dashboard.

ECO2mix is a dataset refreshed hourly, presenting regional data from the eCO2mix application. The data comes from telemetry of the structures, supplemented by packages and estimates. The data is collected every 15 minutes and stored as a history that accumulates from the first successful DAG run.

**Data available every 15 minutes:**
- Production according to different sectors composing the energy mix
- Consumption of pumps in Energy Transfer Pumping Stations (STEP)
- Balance of physical exchanges with neighboring regions

For more information, visit the [ECO2mix Open Data Portal](https://odre.opendatasoft.com/explore/dataset/eco2mix-regional-tr/information/?disjunctive.libelle_region&disjunctive.nature)

## Features

- ✅ **Automated scheduling** using Apache Airflow
- ✅ **Data validation** and transformation pipelines
- ✅ **Refreshed hourly dashboard** with time-window filtering
- ✅ **Containerized deployment** with Docker
- ✅ **PostgreSQL** data storage with idempotent upserts
- ✅ **Scalable architecture** for production use

## Data model

The target table is created once and then updated with an upsert on the natural key `(date_heure, region, filiere)`.

```sql
CREATE TABLE IF NOT EXISTS energy.eco_to_mix (
    date_heure TIMESTAMPTZ NOT NULL,
    region TEXT NOT NULL,
    filiere TEXT NOT NULL,
    consommation DOUBLE PRECISION,
    PRIMARY KEY (date_heure, region, filiere)
);

CREATE INDEX IF NOT EXISTS idx_eco_to_mix_region_date_heure
    ON energy.eco_to_mix (region, date_heure);
```

History accumulates from the first DAG run. Rows are upserted on `(date_heure, region, filiere)` so the dataset can be refreshed hourly without creating duplicates. The data source covers only a recent window, so older values are not backfilled by this pipeline.

If a legacy table created by the earlier replace-based workflow still exists without the primary key, recreate it once with the SQL above. Because the pipeline reloads the current source window on each run, a drop-and-recreate migration is acceptable.

## Project Stack and Architecture

![Data Pipeline Architecture](assets/data_pipeline_example.svg)

**Technology Stack:**
- **Orchestration:** Apache Airflow
- **Data Processing:** Python
- **Database:** PostgreSQL
- **Containerization:** Docker & Docker Compose
- **Visualization:** Dashboard UI

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Running Airflow and Managing DAGs](#running-airflow-and-managing-dags)
- [Visualizing the Data](#visualizing-the-data)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Docker Desktop** 4.x or higher
- **Docker Compose** 2.x or higher
- **Git**
- At least 4GB available RAM
- Docker daemon must be running

## Installation

### Setup

To install the project environment, ensure Docker Desktop is running, then execute:

```bash
docker-compose up
```

This command will:
1. Build all required Docker images
2. Start Airflow, PostgreSQL, and the visualization service
3. Initialize the database

### On Code Changes

If you modify code, you may need to rebuild the containers:

```bash
docker-compose down
docker-compose up -d --build
```

### Reset Everything

If `docker-compose up` keeps failing, reset the environment:

```bash
docker-compose down --volumes --rmi all
docker-compose up
```

### Force Recreate Without Cache

To force Docker to recreate images without using local cache:

```bash
docker-compose up --force-recreate
```

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/sambafall/etl-pipeline-energy-data.git
   cd etl-pipeline-energy-data
   ```

2. **Start the services**
   ```bash
   docker-compose up
   ```

3. **Access Airflow UI**
   - Open http://localhost:8080 in your browser
   - Login with credentials:
     - **Username:** airflow
     - **Password:** airflow

4. **Activate and run the DAG**
   - Click on the **DAGs** tab
   - Locate the "process-energy" DAG
   - Click the toggle to activate it
   - Click the play icon to trigger the pipeline manually

5. **View the results**
   - Once the DAG completes successfully, open http://localhost:8000
   - Browse the energy data visualization dashboard

## Running Airflow and Managing DAGs

### Access Airflow Web UI

Open your browser and navigate to:
```
http://localhost:8080/login
```

### Login Credentials

- **Username:** airflow
- **Password:** airflow

### Manage DAGs

1. Click on the **DAGs** button in the sidebar
2. Find the "process-energy" DAG in the list
3. Use the toggle switch to enable/disable the DAG
4. Click the play icon to manually trigger a run
5. Monitor execution in the DAG details view

## Visualizing the Data

Once the DAG has run successfully, view the processed data:

```
http://localhost:8000
```

The dashboard now:
- queries PostgreSQL with a region filter and a selected date range in the SQL `WHERE` clause
- defaults to the last 7 days
- supports the `Last 24h`, `Last 7 days`, and `Last 30 days` selectors
- refreshes automatically every hour without reloading the page
- aggregates hourly in SQL when the selected period exceeds 30 days to keep the chart readable

The region dropdown and area chart remain available for interactive use.

## Project Structure

```
etl-pipeline-energy-data/
├── dags/                    # Airflow DAG definitions
├── src/                     # Python application code
│   ├── app.py              # Dashboard app logic
│   ├── data_utils.py      # Timestamp and upsert preparation helpers
│   └── dashboard_data.py   # SQL query builders for filtered chart data
├── config/                 # Configuration files
├── assets/                 # Documentation and diagrams
├── docker-compose.yaml     # Service orchestration
├── Dockerfile              # Image build configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

### Issue: `docker-compose up` fails immediately

**Solution:** Reset the environment:
```bash
docker-compose down --volumes --rmi all
docker-compose up
```

### Issue: Airflow UI shows no DAGs

**Solution:** Wait 30-60 seconds for Airflow to scan the DAGs folder, then refresh your browser.

### Issue: Database connection errors

**Solution:** Ensure PostgreSQL is running by checking logs:
```bash
docker-compose logs postgres
```

### Issue: Port already in use (8080, 8000)

**Solution:** Stop conflicting services or modify the `docker-compose.yaml` port mappings.

### Issue: Out of memory errors

**Solution:** Allocate more RAM to Docker Desktop (Settings → Resources → Memory).

## Contributing

We welcome contributions to this project! 

If you encounter a bug or find something unclear:
1. Check existing issues to avoid duplicates
2. Submit a detailed bug report with steps to reproduce
3. Include relevant logs and error messages
4. Propose improvements via pull requests

## License

Released under the [MIT License](LICENSE.txt)

---

**Last Updated:** 2026-10-01
