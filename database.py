import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Set echo=False to disable SQL query logging
# Set echo=True if you want to see all SQL queries for debugging
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
