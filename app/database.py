from peewee import SqliteDatabase
from app.config import Config
import os
import requests
from app.models import Product

# Ensure the database file exists
db_path = Config.DATABASE
os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Create folder if missing

# Initialize the database connection

# Initialisation de la base de données
database = SqliteDatabase(db_path)

PRODUCTS_URL = "http://dimensweb.uqac.ca/~jgnault/shops/products/"

def fetch_products():
    response = requests.get(PRODUCTS_URL)
    if response.status_code == 200:
        data = response.json()["products"]

        with database.atomic():
            for item in data:
                Product.get_or_create(
                    id=item["id"],
                    defaults={
                        "name": item["name"],
                        "description": item["description"],
                        "price": item["price"],
                        "weight": item["weight"],
                        "in_stock": item["in_stock"],
                        "image": item["image"]
                    }
                )

# Fetch products on startup
fetch_products()