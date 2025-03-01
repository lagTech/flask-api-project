from dotenv import load_dotenv
from app import app  # Import from app/__init__.py

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    app.run(debug=True)
