import pandas as pd
from sqlalchemy import create_engine

table = "taxi_zone"

def ingest_zone():
    df = pd.read_csv("taxi_zone_lookup.csv")
    engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')
    df.to_sql(name=table,
              con=engine,
              if_exists="replace")
    print(f'{table} table created.')


    if __name__ == "__main__":
        ingest_zone()