from flask import Flask

app = Flask(__name__)  # Define the global app instance

from app import routes  # Import routes AFTER defining app
