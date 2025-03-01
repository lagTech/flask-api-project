import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Correctly define the SQLite database path
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

class Config:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    DATABASE = DATABASE_PATH  # Now the path is correctly set
