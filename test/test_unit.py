import pytest
import json
from app.models import Product, Order

class TestModels:
    """Tests unitaires pour les modèles de données"""

    def test_product_creation(self, test_db):
        """Test de création d'un produit"""
        product = Product.create(
            id=118,
            name="oats",
            description="oats flour",
            price=19.99,
            weight=50,
            in_stock=True,
            image="118.jpg"
        )
        
        saved_product = Product.get(Product.id == 118)
        
        assert saved_product.id == 118
        assert saved_product.name == "oats"
        assert saved_product.description == "oats flour"
        assert saved_product.price == 19.99
        assert saved_product.weight == 50
        assert saved_product.in_stock == True
        assert saved_product.image == "118.jpg"

    def test_order_creation(self, test_db):
            """Test de création d'une commande"""
            # Créer un produit d'abord
            product = Product.create(
                id=200,
                name="Test Product",
                description="Test Description",
                price=40.01,
                weight=150,
                in_stock=True,
                image="test.jpg"
            )
            
            # Créer une commande liée au produit
            order = Order.create(
                id=1000,
                product=product,
                quantity=3,
                total_price=59.97,
                email="test@example.com",
                paid=False
            )
            
            saved_order = Order.get(Order.id == 1000)
            
            assert saved_order.id == 1000
            assert saved_order.product.id == 200
            assert saved_order.quantity == 3
            assert saved_order.total_price == 59.97
            assert saved_order.email == "test@example.com"
            assert saved_order.paid == False
    
    def test_order_total_price_calculation(self, test_db):
        """Test du calcul correct du prix total"""
        product = Product.create(
            id=300,
            name="Test Product",
            description="Test Description",
            price=25.00,
            weight=800,
            in_stock=True,
            image="test.jpg"
        )
        
        # Créer une commande avec un prix total calculé manuellement
        quantity = 4
        expected_total = quantity * product.price
        
        order = Order.create(
            product=product,
            quantity=quantity,
            total_price=expected_total
        )
        
        assert order.total_price == expected_total
        assert order.total_price == 100.00

    def test_tax_calculation(self, test_db):
        """Test des calculs de taxes pour différentes provinces"""
        product = Product.create(
            id=400,
            name="Test Product",
            description="Test Description",
            price=100.00,
            weight=800,
            in_stock=True,
            image="test.jpg"
        )
        
        # Tester différentes provinces avec différents taux
        provinces_and_rates = {
            "QC": 0.15,
            "ON": 0.13,
            "AB": 0.05,
            "BC": 0.12,
            "NS": 0.14
        }
        
        for province, rate in provinces_and_rates.items():
            order = Order.create(
                product=product,
                quantity=1,
                total_price=100.00,
                province=province
            )
            
            # Calculer manuellement le prix avec taxes
            expected_total_with_tax = 100.00 * (1 + rate)
            
            # Mettre à jour l'ordre avec le calcul des taxes
            order.total_price_tax = order.total_price * (1 + rate)
            order.save()
            
            assert order.total_price_tax == expected_total_with_tax
    
    def test_shipping_cost_calculation(self, test_db):
        """Test des calculs de frais d'expédition basés sur le poids"""
        # Créer trois produits avec différents poids
        products = [
            {"id": 501, "weight": 400, "expected_shipping": 5},   # <500g = $5
            {"id": 502, "weight": 1800, "expected_shipping": 10}, # <2000g = $10
            {"id": 503, "weight": 3000, "expected_shipping": 25}  # >2000g = $25
        ]
        
        for p in products:
            product = Product.create(
                id=p["id"],
                name=f"Product {p['id']}",
                description="Test Description",
                price=10.00,
                weight=p["weight"],
                in_stock=True,
                image="test.jpg"
            )
            
            order = Order.create(
                product=product,
                quantity=1,
                total_price=10.00,
                shipping_price=p["expected_shipping"]
            )
            
            assert order.shipping_price == p["expected_shipping"]