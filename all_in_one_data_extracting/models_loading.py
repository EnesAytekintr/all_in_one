import pandas as pd
from sqlalchemy import create_engine 

df = pd.read_csv("all_in_one_data_extracting/model_data/models.csv")

engine = create_engine(url="postgresql+psycopg2://postgres:postgres@localhost:5432/hf_models_db")

df.to_sql(
    name="models_raw",
    con=engine,
    if_exists="append",
    schema= "raw",
    index=False,
    chunksize=50000
)