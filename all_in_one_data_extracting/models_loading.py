import pandas as pd
from sqlalchemy import create_engine 
from dotenv import load_dotenv
import os

load_dotenv()

df = pd.read_csv(f"{os.getenv('CSV_PATH', 'all_in_one_data_extracting/model_data/models.csv')}")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hf_models_db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "50000"))

engine = create_engine(url=DATABASE_URL)

df.to_sql(
    name="models_raw",
    con=engine,
    if_exists="replace",
    schema= "raw",
    index=False,
    chunksize=CHUNK_SIZE
)