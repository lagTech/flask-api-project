import os
import sys
import pytest
from peewee import SqliteDatabase
import tempfile
import json
from app import app as flask_app
from app.models import Product, Order, BaseModel
import requests

# Ajout du répertoire parent au chemin d'importation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

# Données de test pour les produits
MOCK_PRODUCTS = {
    "products": [
        {
        "id": 1,
		"name": "Brown eggs",
		"description": "Raw organic brown eggs in a basket",
		"image": "0.jpg",
		"weight": 400,
		"price": 28.1,
		"in_stock": True
        },
        {
        "id": 2,
		"name": "Sweet fresh stawberry",
		"description": "Sweet fresh stawberry on the wooden table",
		"image": "1.jpg",
		"weight": 299,
		"price": 29.45,
		"in_stock": True
        },
        {
        "id": 3,
		"name": "Green smoothie",
		"description": "Glass of green smoothie with quail egg's yolk, served with cocktail tube, green apple and baby spinach leaves over tin surface.",
		"image": "3.jpg",
		"weight": 399,
		"price": 17.68,
		"in_stock": False
        }
    ]
}

# Données de test pour la transaction de paiement
MOCK_PAYMENT_SUCCESS = {
    "transaction": {
        "id": "txn_123456789",
        "status": "success",
        "amount": 34.49
    }
}

MOCK_PAYMENT_FAILURE = {
    "errors": {
        "payment": {
            "code": "invalid-card",
            "name": "Invalid credit card information"
        }
    }
}

@pytest.fixture
def app():
    """Fixture pour créer une instance de l'application Flask avec une base de données en mémoire"""
    # Configuration pour les tests
    flask_app.config.update({
        'TESTING': True,
        'DEBUG': False,
    })

    yield flask_app

@pytest.fixture
def client(app):
    """Fixture pour créer un client de test"""
    return app.test_client()

@pytest.fixture
def test_db():
    """Fixture pour créer une base de données temporaire en mémoire pour les tests"""
    # Créer un fichier temporaire pour la BD
    db_fd, db_path = tempfile.mkstemp()
    test_database = SqliteDatabase(db_path)
    
    # Remplacer la BD originale par notre BD de test
    original_db = BaseModel._meta.database
    BaseModel._meta.database = test_database
    
    # Créer les tables dans la BD de test
    test_database.connect()
    test_database.create_tables([Product, Order])

    Product.delete().execute()
    Order.delete().execute()

    # Peupler la BD avec des données de test
    for product_data in MOCK_PRODUCTS["products"]:
        Product.get_or_create(**product_data)
    
    yield test_database
    
    # Nettoyer après les tests
    test_database.close()
    os.close(db_fd)
    os.unlink(db_path)
    # Restaurer la BD originale
    BaseModel._meta.database = original_db

@pytest.fixture
def mock_requests_get(monkeypatch):
    """Fixture pour simuler requests.get"""
    def mock_get(*args, **kwargs):
        if args[0] == "http://dimensweb.uqac.ca/~jgnault/shops/products/":
            return MockResponse(MOCK_PRODUCTS, 200)
        return MockResponse({"error": "URL not found"}, 404)
    
    monkeypatch.setattr(requests, "get", mock_get)

@pytest.fixture
def mock_requests_post(monkeypatch):
    """Fixture pour simuler requests.post"""
    def mock_post(*args, **kwargs):
        if args[0] == "https://dimensweb.uqac.ca/~jgnault/shops/pay/":
            data = kwargs.get('json', {})
            card_number = data.get('credit_card', {}).get('number', '')
            
            # Cas de test: Carte commençant par 4 -> succès, tous les autres -> échec
            if card_number.startswith('4'):
                return MockResponse(MOCK_PAYMENT_SUCCESS, 200)
            else:
                return MockResponse(MOCK_PAYMENT_FAILURE, 422)
        
        return MockResponse({"error": "URL not found"}, 404)
    
    monkeypatch.setattr(requests, "post", mock_post)

@pytest.fixture
def create_test_order(test_db):
    """Fixture pour créer une commande de test"""
    product = Product.get(Product.id == 1)
    order = Order.create(
        product=product,
        quantity=2,
        total_price=product.price * 2
    )
    return order

@pytest.fixture
def create_complete_order(test_db):
    """Fixture pour créer une commande complète avec informations d'expédition"""
    product = Product.get(Product.id == 1)
    
    order = Order.create(
        product=product,
        quantity=2,
        total_price=product.price * 2,
        total_price_tax=product.price * 2 * 1.15,
        email="test@example.com",
        country="Canada",
        address="123 Test Street",
        postal_code="G7X 1A1",
        city="Chicoutimi",
        province="QC",
        shipping_price=5.0
    )
    return order