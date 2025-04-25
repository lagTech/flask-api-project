import json
import requests
from api8inf349.models import Order
from api8inf349.redis_client import redis_client


def process_payment(order_id, payment_data, credit_card, transaction_url):
    order = Order.get_by_id(order_id)

    try:
        response = requests.post(transaction_url, json=payment_data, headers={"Content-Type": "application/json"})

        # Traitement de la réponse
        payment_response = {}
        error_info = None

        # Analyse de la réponse
        if response.status_code != 200:
            # Erreur du service de paiement distant
            try:
                error_info = response.json()
            except:
                error_info = {"error": "payment-failed", "details": response.text}

            # Persister l'erreur dans la base de données
            order.transaction_error = json.dumps(error_info)
            order.save()
        else:
            # Paiement réussi
            payment_response = response.json()
            order.paid = True
            order.transaction_id = payment_response["transaction"]["id"]
            order.transaction_error = None
            order.save()

        # Préparer les données de réponse
        first_digits = credit_card["number"][:4]
        last_digits = credit_card["number"][-4:]

        product_entries = [
            {
                "id": op.product.id,
                "name": op.product.name,
                "quantity": op.quantity,
                "price": float(op.product.price),
                "weight": op.product.weight,
                "height": op.product.height
            }
            for op in order.products
        ]

        # Structure de la transaction en fonction du succès ou de l'échec
        transaction_data = {}
        if order.paid:
            transaction_data = payment_response["transaction"]
        elif order.transaction_error:
            try:
                transaction_data = json.loads(order.transaction_error)
            except:
                transaction_data = {"error": "payment-failed", "details": order.transaction_error}

        response_data = {
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "total_price_tax": order.total_price_tax,
                "email": order.email,
                "credit_card": {
                    "name": credit_card["name"],
                    "first_digits": first_digits,
                    "last_digits": last_digits,
                    "expiration_year": credit_card["expiration_year"],
                    "expiration_month": credit_card["expiration_month"]
                },
                "shipping_information": {
                    "country": order.country,
                    "address": order.address,
                    "postal_code": order.postal_code,
                    "city": order.city,
                    "province": order.province
                },
                "paid": order.paid,
                "transaction": transaction_data,
                "products": product_entries,
                "shipping_price": order.shipping_price
            }
        }

        # Mettre en cache les données de la commande
        redis_client.set(f"order:{order.id}", json.dumps(response_data))

        if order.paid:
            return {"success": True}
        else:
            return {"error": "payment-failed", "details": transaction_data}

    except Exception as e:
        error_info = {"error": "worker.py-exception", "message": str(e)}

        # Persister l'erreur dans la base de données
        order.transaction_error = json.dumps(error_info)
        order.save()

        return error_info
