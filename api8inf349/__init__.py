from flask import Flask
from api8inf349.commands import init_db_command



app = Flask(__name__)  # Define the global api8inf349 instance

from api8inf349 import routes
app.cli.add_command(init_db_command)

print(" Flask api8inf349 loaded from __init__.py")
