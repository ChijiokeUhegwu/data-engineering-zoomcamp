#!/usr/bin/env python
# coding: utf-8

# import packages
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

# Specify the data types to handle the error where pandas is not able to accurately infer the datatypes in the dataset 
dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


# create variables for parameterization
def run():
    year = 2021
    month = 1
    pg_user = 'root'
    pg_password = 'root'
    pg_host = 'localhost'
    pg_port = 5432
    pg_db = 'ny_taxi'
    target_table = 'yellow_taxi_data'
    chunksize = 10000
    
    # Read a sample of the data
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
    url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'
    # f"{month:02d}" - the month are zero-padded with a width of 2 

    # create database connection for pandas and sqlalchemy
    engine =  create_engine(f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}')

    df_iter = pd.read_csv(
    url,
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=chunksize,
    )

    first = True
    # iterate over the chunks and insert 
    for df_chunk in tqdm(df_iter):
        if first:
            df_chunk.head(0).to_sql(
                name=target_table, 
                con=engine, 
                if_exists='replace',
                index=False # to avoid creating an unnecessary index column
            )
            first = False
         
            df_chunk.to_sql(
                name=target_table, 
                con=engine, 
                if_exists='append',
                index=False
            )

if __name__ == '__main__':
    run()

