from flask import Flask
from app.commands import init_db_command
from app.bootstrap import fetch_products


app = Flask(__name__)  # Define the global app instance

from app import routes  # Import routes AFTER defining app


app.cli.add_command(init_db_command)

print("✅ Flask app loaded from __init__.py")
