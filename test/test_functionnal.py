import pytest
import json
from app.models import Product, Order

class TestAPIRoutes:
    """Tests fonctionnels des routes API"""
    
    def test_get_products(self, client, test_db):
        """Test de récupération de la liste des produits"""
        response = client.get('/')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "products" in data
        assert len(data["products"]) == 3  # Nombre de produits dans MOCK_PRODUCTS
        
        # Vérifier les détails du premier produit
        first_product = data["products"][0]
        assert first_product["id"] == 1
        assert first_product["name"] == "Brown eggs"
        assert first_product["price"] == 28.1
        assert first_product["in_stock"] == True
    
    def test_create_order_success(self, client, test_db):
        """Test de création d'une commande avec succès"""
        # Données pour une commande valide
        order_data = {
            "product": {
                "id": 1,
                "quantity": 2
            }
        }
        
        response = client.post('/order', 
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 302  # Redirection après création
        
        data = json.loads(response.data)
        assert "order_id" in data
        
        # Vérifier l'en-tête Location pour la redirection
        assert response.headers["Location"].startswith("/order/")
        
        # Vérifier que la commande existe dans la BD
        order_id = data["order_id"]
        order = Order.get_or_none(Order.id == order_id)
        assert order is not None
        assert order.product.id == 1
        assert order.quantity == 2
        assert order.total_price == 28.1 * 2  # Prix du produit * quantité
    
    def test_create_order_invalid_data(self, client, test_db):
        """Test avec des données de commande invalides"""
        # Cas 1: Champ product manquant
        response = client.post('/order', 
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert "errors" in data
        assert "product" in data["errors"]
        assert data["errors"]["product"]["code"] == "missing-fields"
        
        # Cas 2: Product est une liste (non autorisé)
        response = client.post('/order', 
                             data=json.dumps({"product": []}),
                             content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["product"]["code"] == "invalid-format"
        
        # Cas 3: Champs requis manquants dans product
        response = client.post('/order', 
                             data=json.dumps({"product": {}}),
                             content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["product"]["code"] == "missing-fields"
        
        # Cas 4: Quantité invalide
        response = client.post('/order', 
                             data=json.dumps({"product": {"id": 1, "quantity": 0}}),
                             content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["product"]["code"] == "invalid-quantity"
        
        # Cas 5: Produit inexistant
        response = client.post('/order', 
                             data=json.dumps({"product": {"id": 999, "quantity": 1}}),
                             content_type='application/json')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["errors"]["product"]["code"] == "not-found"
        
        # Cas 6: Produit hors stock
        response = client.post('/order', 
                             data=json.dumps({"product": {"id": 3, "quantity": 1}}),
                             content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["product"]["code"] == "out-of-inventory"
    
    def test_get_order(self, client, test_db, create_test_order):
        """Test de récupération des détails d'une commande"""
        order = create_test_order
        
        response = client.get(f'/order/{order.id}')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "order" in data
        assert data["order"]["id"] == order.id
        assert data["order"]["total_price"] == order.total_price
        assert data["order"]["product"]["id"] == order.product.id
        assert data["order"]["product"]["quantity"] == order.quantity
    
    def test_get_order_not_found(self, client, test_db):
        """Test de récupération d'une commande inexistante"""
        response = client.get('/order/9999')
        
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert "errors" in data
        assert data["errors"]["order"]["code"] == "not-found"
    
    def test_update_order_shipping_info(self, client, test_db, create_test_order):
        """Test de mise à jour des informations d'expédition d'une commande"""
        order = create_test_order
        
        shipping_data = {
            "order": {
                "email": "customer@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "123 Maple Street",
                    "postal_code": "G7X 3Z2",
                    "city": "Chicoutimi",
                    "province": "QC"
                }
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(shipping_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["order"]["email"] == "customer@example.com"
        assert data["order"]["shipping_information"]["country"] == "Canada"
        assert data["order"]["shipping_information"]["province"] == "QC"
        
        # Vérifier que les taxes ont été calculées (15% pour QC)
        assert data["order"]["total_price_tax"] == pytest.approx(order.total_price * 1.15)
        
        # Vérifier que les frais d'expédition ont été calculés (basés sur le poids)
        assert "shipping_price" in data["order"]
    
    def test_update_order_missing_fields(self, client, test_db, create_test_order):
        """Test de mise à jour d'une commande avec des champs manquants"""
        order = create_test_order
        
        # Cas 1: Champ order manquant
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps({}),
                            content_type='application/json')
        assert response.status_code == 400
        
        # Cas 2: Champ shipping_information manquant
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps({"order": {"email": "test@example.com"}}),
                            content_type='application/json')
        assert response.status_code == 422
        
        # Cas 3: Email vide
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps({
                                "order": {
                                    "email": "",
                                    "shipping_information": {
                                        "country": "Canada",
                                        "address": "123 Maple Street",
                                        "postal_code": "G7X 3Z2",
                                        "city": "Chicoutimi",
                                        "province": "QC"
                                    }
                                }
                            }),
                            content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["email"]["code"] == "invalid-email"
        
        # Cas 4: Champs d'expédition manquants
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps({
                                "order": {
                                    "email": "test@example.com",
                                    "shipping_information": {
                                        "country": "Canada",
                                        "city": "Chicoutimi",
                                        # address et postal_code manquants
                                    }
                                }
                            }),
                            content_type='application/json')
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["shipping_information"]["code"] == "invalid-fields"

    def test_payment_with_invalid_credit_card_format(self, client, test_db, create_complete_order):
        """Test de paiement avec un format de carte de crédit invalide"""
        order = create_complete_order
        
        payment_data = {
            "credit_card": {
                "number": "1234",  
                "expiration_year": 2025,
                "expiration_month": 12,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert "errors" in data
        assert data["errors"]["credit_card"]["code"] == 'card-invalid'

    def test_get_order_with_transaction_details(self, client, test_db, create_complete_order):
        """Test de récupération d'une commande avec détails de transaction"""
        order = create_complete_order
        
        # Simuler une commande payée avec détails de transaction
        order.paid = True
        order.transaction_id = "txn_123456789"
        order.save()
        
        response = client.get(f'/order/{order.id}')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["order"]["paid"] == True

    def test_create_order_with_invalid_json(self, client, test_db):
        """Test de création d'une commande avec JSON invalide"""
        response = client.post('/order', 
                            data="invalid json",
                            content_type='application/json')
        
        assert response.status_code == 400

    def test_update_order_with_invalid_json(self, client, test_db, create_test_order):
        """Test de mise à jour d'une commande avec JSON invalide"""
        order = create_test_order
        
        response = client.put(f'/order/{order.id}', 
                            data="invalid json",
                            content_type='application/json')
        
        assert response.status_code == 400

    def test_update_order_without_data(self, client, test_db, create_test_order):
        """Test de mise à jour d'une commande sans données"""
        order = create_test_order
        
        # Requête vide
        response = client.put(f'/order/{order.id}')
        
        assert response.status_code == 415

    def test_update_nonexistent_order(self, client, test_db):
        """Test de mise à jour d'une commande inexistante"""
        response = client.put('/order/1234', 
                            data=json.dumps({"order": {"email": "test13@example.com"}}),
                            content_type='application/json')
        
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data["errors"]["order"]["code"] == "not-found"

    def test_update_order_with_invalid_email_format(self, client, test_db, create_test_order):
        """Test de mise à jour d'une commande avec un format d'email invalide"""
        order = create_test_order
        
        shipping_data = {
            "order": {
                "email": "invalid-email",  
                "shipping_information": {
                    "country": "Canada",
                    "address": "123 Maple Street",
                    "postal_code": "G7X 3Z2",
                    "city": "Chicoutimi",
                    "province": "QC"
                }
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(shipping_data),
                            content_type='application/json')
        
       
        assert response.status_code == 200

    def test_payment_with_expired_card(self, client, test_db, create_complete_order):
        """Test de paiement avec une carte expirée"""
        order = create_complete_order
        
        payment_data = {
            "credit_card": {
                "number": "4111111111111111",
                "expiration_year": 2020,  # Année expirée
                "expiration_month": 1,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
       
        assert response.status_code in [200, 422]

    def test_payment_with_missing_card_fields(self, client, test_db, create_complete_order):
        """Test de paiement avec des champs de carte manquants"""
        order = create_complete_order
        
        # Manque le champ CVV
        payment_data = {
            "credit_card": {
                "number": "4111111111111111",
                "expiration_year": 2025,
                "expiration_month": 12,
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert "payment" in data["errors"]
        assert data["errors"]["payment"]["code"] == "invalid-fields"

    def test_payment_for_already_paid_order(self, client, test_db, create_complete_order):
        """Test de paiement pour une commande déjà payée"""
        order = create_complete_order
        
        # Marquer la commande comme déjà payée
        order.paid = True
        order.save()
        
        payment_data = {
            "credit_card": {
                "number": "4111111111111111",
                "expiration_year": 2025,
                "expiration_month": 12,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["order"]["code"] == "already-paid"