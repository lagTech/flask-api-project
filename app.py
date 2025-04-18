from dotenv import load_dotenv
from api8inf349 import app  # Import from api8inf349/__init__.py

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    app.run(debug=True)
