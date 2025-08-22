from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, JSON

DATABASE_URL = "postgresql://invex_db_user:uR4BGxN3VLcanhCdVSO6laFUgtzzCiwG@dpg-d2kacbv5r7bs73ekh5bg-a.oregon-postgres.render.com:5432/invex_db"

# Conexión asíncrona para FastAPI
database = Database(DATABASE_URL)

# Metadata de SQLAlchemy
metadata = MetaData()

# Engine sincrónico para crear tablas
engine = create_engine(DATABASE_URL)
