import requests
from api8inf349.models import Product
from api8inf349.database import database

PRODUCTS_URL = "http://dimensweb.uqac.ca/~jgnault/shops/products/"

def sanitize(text):
    if text:
        return text.replace('\x00', '')
    return text

def fetch_products():
    response = requests.get(PRODUCTS_URL)
    if response.status_code == 200:
        data = response.json()["products"]

        with database.atomic():
            for item in data:
                Product.get_or_create(
                    id=item["id"],
                    defaults={
                        "name": sanitize(item["name"]),
                        "description": sanitize(item["description"]),
                        "price": item["price"],
                        "weight": item["weight"],
                        "in_stock": item["in_stock"],
                        "image": sanitize(item["image"])
                    }
                )