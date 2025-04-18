import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    DATABASE = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
