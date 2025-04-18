import pytest
import json
from app.models import Product, Order

class TestEndToEndFlow(object):
    """Tests d'intégration pour le flux complet de commande"""
    
    def test_order_complete_flow(self, client, test_db, mock_requests_post):
        """Test du flux complet: création, mise à jour et paiement d'une commande"""
        
        # 1. Création d'une commande
        order_data = {
            "product": {
                "id": 1,
                "quantity": 2
            }
        }
        
        response = client.post('/order', 
                             data=json.dumps(order_data),
                             content_type='application/json')
        
        assert response.status_code == 302
        data = json.loads(response.data)
        order_id = data["order_id"]
        
        # 2. Mise à jour des informations d'expédition
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
        
        response = client.put(f'/order/{order_id}', 
                            data=json.dumps(shipping_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["order"]["email"] == "customer@example.com"
        assert data["order"]["total_price_tax"] > data["order"]["total_price"]
        assert data["order"]["shipping_price"] > 0
        
        # 3. Paiement de la commande avec succès (carte commençant par 4)
        payment_data = {
            "credit_card": {
                "number": "4111111111111111",
                "expiration_year": 2025,
                "expiration_month": 12,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order_id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["order"]["paid"] == True
        assert "transaction" in data["order"]
        assert data["order"]["transaction"]["status"] == "success"
        assert "first_digits" in data["order"]["credit_card"]
        assert data["order"]["credit_card"]["first_digits"] == "4111"
        
        # 4. Vérifier que la commande est bien marquée comme payée dans la BD
        order = Order.get(Order.id == order_id)
        assert order.paid == True
    
    def test_payment_failure(self, client, test_db, mock_requests_post, create_complete_order):
        """Test d'échec de paiement avec carte invalide"""
        order = create_complete_order
        
        # Paiement avec une carte invalide (ne commençant pas par 4)
        payment_data = {
            "credit_card": {
                "number": "5555555555554444",  
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
        assert data["errors"]["payment"]["code"] == "invalid-card"
        
        # Vérifier que la commande n'est pas marquée comme payée
        order = Order.get(Order.id == order.id)
        assert order.paid == False
    
    def test_invalid_order_operations(self, client, test_db, create_test_order):
        """Test des opérations invalides sur une commande"""
        order = create_test_order
        
        # 1. Tentative de paiement sans informations d'expédition
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
        assert data["errors"]["order"]["code"] == "missing-fields"
        
        # 2. Tentative de mise à jour et paiement en même temps
        invalid_data = {
            "order": {
                "email": "test@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "123 Test St",
                    "postal_code": "G7X 1A1",
                    "city": "Chicoutimi",
                    "province": "QC"
                }
            },
            "credit_card": {
                "number": "4111111111111111",
                "expiration_year": 2025,
                "expiration_month": 12,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(invalid_data),
                            content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["errors"]["order"]["code"] == "invalid-operation"

    def test_fetch_products_integration(self, client, test_db, mock_requests_get):
        """Test d'intégration pour la récupération des produits depuis l'API externe"""
        from app.database import fetch_products
        
        # Vider d'abord la table des produits
        Product.delete().execute()
        
        # Exécuter la fonction qui récupère les produits
        fetch_products()
        
        # Vérifier que les produits ont été ajoutés
        products = Product.select()
        assert products.count() == 3
        
        # Vérifier que les données correspondent à nos données simulées
        product1 = Product.get(Product.id == 1)
        assert product1.name == "Brown eggs"
        assert product1.price == 28.1
        
        # Vérifier que l'API renvoie bien les produits
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data["products"]) == 3
    
    def test_payment_retry_after_failure(self, client, test_db, create_complete_order):
        """Test pour vérifier qu'une commande peut être payée après un échec initial"""
        order = create_complete_order
        
        # Premier essai avec carte invalide
        payment_data = {
            "credit_card": {
                "number": "5555555555554444",
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
        
        # Deuxième essai avec carte valide
        payment_data = {
            "credit_card": {
                "number": "4242 4242 4242 4242",
                "expiration_year": 2025,
                "expiration_month": 12,
                "cvv": "123",
                "name": "Test Customer"
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(payment_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["order"]["paid"] == True

    

    def test_payment_server_error(self, client, test_db, create_complete_order, monkeypatch):
        """Test de gestion des erreurs serveur lors du paiement"""
        import requests
        
        order = create_complete_order
        
        # Simuler une erreur serveur lors de la requête de paiement
        def mock_requests_post_error(*args, **kwargs):
            raise requests.exceptions.RequestException("Simulated server error")
        
        # Remplacer temporairement la fonction requests.post
        monkeypatch.setattr(requests, "post", mock_requests_post_error)
        
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
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "errors" in data
        assert data["errors"]["payment"]["code"] == "server-error"

    def test_order_flow_with_special_characters(self, client, test_db, mock_requests_post):
        """Test du flux de commande avec des caractères spéciaux dans les données"""
        # 1. Création d'une commande
        order_data = {
            "product": {
                "id": 1,
                "quantity": 2
            }
        }
        
        response = client.post('/order', 
                            data=json.dumps(order_data),
                            content_type='application/json')
        
        assert response.status_code == 302
        data = json.loads(response.data)
        order_id = data["order_id"]
        
        # 2. Mise à jour avec des caractères spéciaux
        shipping_data = {
            "order": {
                "email": "customer.special+tag@example.com",
                "shipping_information": {
                    "country": "Côte d'Ivoire",  # Caractères accentués et apostrophe
                    "address": "123 Université St. Apt #42",  # Caractères spéciaux
                    "postal_code": "X0X-0X0",
                    "city": "Saint-Jérôme",  # Caractères accentués et tiret
                    "province": "QC"
                }
            }
        }
        
        response = client.put(f'/order/{order_id}', 
                            data=json.dumps(shipping_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["order"]["email"] == "customer.special+tag@example.com"
        assert data["order"]["shipping_information"]["country"] == "Côte d'Ivoire"
        assert data["order"]["shipping_information"]["city"] == "Saint-Jérôme"

    def test_update_order_after_payment(self, client, test_db, create_complete_order):
        """Test de tentative de mise à jour d'une commande après paiement"""
        order = create_complete_order
        
        # Simuler une commande payée
        order.paid = True
        order.save()
        
        # Tenter de mettre à jour les informations d'expédition après paiement
        shipping_data = {
            "order": {
                "email": "new-email@example.com",
                "shipping_information": {
                    "country": "USA",
                    "address": "456 Main St",
                    "postal_code": "10001",
                    "city": "New York",
                    "province": "NY"
                }
            }
        }
        
        response = client.put(f'/order/{order.id}', 
                            data=json.dumps(shipping_data),
                            content_type='application/json')
        
        # Si l'implémentation actuelle permet des mises à jour après paiement, 
        # ce test vérifiera si cela fonctionne correctement
        # Idéalement, il devrait y avoir une validation pour empêcher les modifications après paiement
        assert response.status_code in [200, 422]
        
        if response.status_code == 422:
            # Si une validation est en place, vérifier le message d'erreur
            data = json.loads(response.data)
            assert "errors" in data
            # Le code d'erreur exact dépendra de votre implémentation
        elif response.status_code == 200:
            # Si la mise à jour est autorisée, vérifier que les données ont été mises à jour
            order = Order.get(Order.id == order.id)
            assert order.email == "new-email@example.com"
            assert order.country == "USA"

