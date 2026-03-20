# Study Note 

## 1. To begin any project
1. Create an isolated environment within your project folder to prevent conflicts and ensure a clean workspace. 
```bash
python -m venv .venv
source .venv/bin/activate  # to activate the venv
pip install pandas pyarrow # install the necessary packages
```

2. Then, run the line below to pass 12 as an argument and execute the script. The venv activated environment will be showing.
```bash
python ./pipeline/pipeline.py 12
```
---
## 2. Using uv (preferred method)

A Python virtual environment can also be managed using **uv**.  
The main advantage of using uv is that it is very fast at installing packages, because it is written in Rust.

```bash
# Install uv (if not already installed)
pip install uv

# Initialize a project and create a virtual environment
# You can specify the Python version to use
uv init --python 3.13

# Verify Python versions
# Global environment:
python -V
# uv-managed virtual environment:
uv run python -V

# Install packages into the uv virtual environment
uv add pandas pyarrow

# use the select interpreter (ctrl+shift+p) to direct vscode to use the python in the venv which will be in the
../venv/bin/python

# from the project home directory, run the pipeline script using the uv environment
uv run python ./pipeline/pipeline.py 12
```

**Note**
- `uv run` ensures commands are executed inside the uv-managed environment
- Packages added with `uv add` are isolated from the global Python installation

## 3. Building a docker image
A Dockerfile describes how we build a docker container. It contains all the instructions we need to create the image from which the container can be created. Before building a Docker image, always **save the Dockerfile** and verify its contents using:
```bash
cat Dockerfile
```

To build the image, use
```bash
docker build -t <image_name> . # the fullstop signifies current working dir
```

If any changes are made to the Dockerfile, rebuild the image using the code below to ensure Docker does not reuse cached layers (it reuses cache by default unless told otherwise):

```bash
docker build --no-cache -t <image_name> .
```

Run the container using:
```bash
docker run -it --rm --entrypoint bash <image_name>
```

for interactive debugging, or  if an `ENTRYPOINT` is already defined in the Dockerfile:

```bash
docker run --rm <image_name> [args]
```
Importantly, always check the Docker build output to confirm that all expected steps (e.g., `WORKDIR`, `COPY`) are executed.

## Parquet and CSV files
CSV files are plain text, meaning they do not "know" what kind of data they hold. When you load a CSV, the system must perform schema inference—it scans the raw text to guess whether a value like 12 is an integer, a string, or a decimal. This process is computationally expensive and prone to errors; for instance, a column of ID numbers might be incorrectly inferred as integers, leading to the loss of leading zeros or causing crashes if a stray character is encountered later. 
**Parquet’s Binary and Self-Describing Advantage**
Parquet is a binary, self-describing format, which means the metadata (the "schema") is baked directly into the file. When a program reads a Parquet file, it immediately knows the exact data type of every column without having to guess. This eliminates the need for expensive inference and ensures high data integrity, as types like dates and nested lists are preserved exactly as they were written. Since Parquet is optimized for analytical workloads, it offers several technical benefits over CSV such as allowing for column pruning, where the system only reads the specific columns needed for a query, significantly reducing disk I/O and speed (this is possible because unlike CSVs which store data row by row, Parquet stores data column by column).

## Pandas and SQLAlchemy
Pandas integrates with SQLAlchemy to serve as a high-performance bridge between Python data structures and nearly any relational database. While Pandas is designed for data manipulation, SQLAlchemy acts as the specialized "translator" that manages the complexities of different SQL dialects. 

**How the Interaction Works**
- The Engine as a Universal Interface: To connect Pandas to a database (like PostgreSQL, MySQL, or SQL Server), you first create a SQLAlchemy Engine object. This engine contains the connection details and the "dialect" needed to communicate with that specific database type.
- Reading Data (read_sql): When you call pd.read_sql(), you pass it a SQL query and the SQLAlchemy engine. Pandas uses the engine to execute the query and automatically converts the resulting database rows into a structured DataFrame.
- Writing Data (to_sql): Similarly, df.to_sql() allows you to send a DataFrame directly to a database table. SQLAlchemy handles the heavy lifting of generating the correct INSERT or CREATE TABLE statements for your specific database. 

With this combination, you can write one script that works for SQLite during development and easily switch it to a production PostgreSQL database by only changing the SQLAlchemy connection string. Also, when writing data, Pandas uses SQLAlchemy to map Python data types (integers, strings, dates) to the correct SQL column types automatically, reducing manual data entry errors. Furthermore, SQLAlchemy provides built-in connection pooling, which keeps a set of database connections open for reuse. This significantly improves performance for applications that frequently read or write data. Finally, by using SQLAlchemy’s execution layer, Pandas can utilize parameterized queries, which protect your database against SQL injection attacks.

## Notes
When you have a large dataset to ingest into a a database, you can read it in chunks with pandas (sqlalchemy) so you can effectively decipher whether anything breaks or performs oddly.

## Command-Line interface parameters
You can use the **click** package to turn your Python function into a command-line tool and map terminal arguments to function parameters. instead of hardcoding the values, you can run your script as shown below:
```bash
uv run python ingest_data.py \
  --pg-user=root \
  --pg-password=root \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips \
  --year=2021 \
  --month=1 \
  --chunksize=100000 
```

To verify that the data was ingested, run:
```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

To run the same script in docker (to dockerize it), first you need to change the COPY and the entrypoint in the dockerfile to ingest_data.py, then build the docker image of the pipeline using 
```bash
docker build -t taxi_ingest:v001 .
```
Then, you run the script in docker, but ensure postgres is running in the background to avoid an error. However, this can be avoided by creating a network:

```bash
docker run -it --rm \
  taxi_ingest:v001 \
  --pg-user=root \
  --pg-password=root \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips \
  --year=2021 \
  --month=1 \
  --chunksize=100000 
```

After containerizing the ingestion script, you would want to provide the network for Docker to find the Postgres container (this is because things within the same network can see each other). It goes before the name of the image. Also, since Postgres is running on a separate container, the host argument will have to point to the container name of Postgres (pgdatabase). 

To do this, first create the network:
```bash
docker network create pg-network
```
Then add the network name to the docker script and specify Postgres's container name. Run the scripts accordingly:

Update the postgres container details with the network name and the name of the shared container it would run the ingest_data with, then run to establish a port connection:
```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  --network=pg-network \
  --name pgdatabase \
postgres:18
```

In another terminal, update the ingest data details with the network name and the host container it should run with and run:
```bash
docker run -it --rm \
  --network=pg-network \
  taxi_ingest:v001 \
  --pg-user=root \
  --pg-password=root \
  --pg-host=pgdatabase \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips \
  --year=2021 \
  --month=1 \
  --chunksize=100000 
```
To see the data in a database GUI, you can use pgadmin. In another terminal, run pgAdmin on the same network (ensure you are in the pipeline folder). then open the link in your browser and interact with the data on pgadmin.
```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
dpage/pgadmin4 
```

After this, you can create a docker-compose.yaml file to launch multiple containers using a single configuration file, so that we don't have to run multiple complex docker run commands separately. By default, everything you run within one  docker file, is executed within one network. You can execute the docker-compose file using `docker-compose up` or `docker-compose up -d` to run in detached mode. Basically, the docker compose is used to run all the dependencies of the pipeline. This creates a new instance of all your containers combined, including the database and servers (if that was done previously, they would be recreated). You can login into pgadmin again to interact with the data. To do that, you need to separately run the script for ingesting the data into the database, but that must be done within the network that was created by docker compose. Do `docker network ls` to see the network's name (since the network was not named, it takes the name of the folder by default appended with "default"; i.e "pipeline_default"). After ingesting the data, the next time `docker-compose up` is done, all the data will be there. 
```bash
docker run -it --rm \
  --network=pipeline_default \
  taxi_ingest:v001 \
  --pg-user=root \
  --pg-password=root \
  --pg-host=pgdatabase \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips \
  --year=2021 \
  --month=1 \
  --chunksize=100000 
```

```bash
`docker-compose down` # to shut down the containers running in foreground mode.
docker ps -aq # to find the current running or finished containers
docker rm (docker ps -aq) # to kill all running containers
```