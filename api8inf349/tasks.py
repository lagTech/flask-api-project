import json
import requests
from api8inf349.models import Order
from api8inf349.redis_client import redis_client

def process_payment(order_id, payment_data, credit_card, transaction_url):
    order = Order.get_by_id(order_id)

    try:
        response = requests.post(transaction_url, json=payment_data, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            return {"error": "payment-failed", "details": response.text}

        payment_response = response.json()

        order.paid = True
        order.transaction_id = payment_response["transaction"]["id"]
        order.save()

        first_digits = credit_card["number"][:4]
        last_digits = credit_card["number"][-4:]

        product_entries = [
            {"id": op.product.id, "quantity": op.quantity}
            for op in order.products
        ]

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
                "transaction": payment_response["transaction"],
                "products": product_entries,
                "shipping_price": order.shipping_price
            }
        }

        redis_client.set(f"order:{order.id}", json.dumps(response_data))
        return {"success": True}

    except Exception as e:
        return {"error": "worker.py-exception", "message": str(e)}
