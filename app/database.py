from peewee import SqliteDatabase
from app.config import Config
import os

# Ensure the database file exists
db_path = Config.DATABASE
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Create folder if missing

# Initialize the database connection

# Initialisation de la base de données
database = SqliteDatabase(db_path)
