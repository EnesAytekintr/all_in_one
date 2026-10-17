import pandas as pd
from sqlalchemy import create_engine 
from dotenv import load_dotenv
import os

load_dotenv()

df = pd.read_csv(f"{os.getenv('CSV_PATH', 'all_in_one_data_extracting/model_data/models.csv')}")

engine = create_engine(url="postgresql+psycopg2://postgres:postgres@localhost:5432/hf_models_db")

df.to_sql(
    name="models_raw",
    con=engine,
    if_exists="replace",
    schema= "raw",
    index=False,
    chunksize=50000
)