from peewee import PostgresqlDatabase
from api8inf349.config import Config
import os
import requests


# Initialisation de la base de données
database = PostgresqlDatabase(
    os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT'))
)




# # Fetch products on startup
# fetch_products()