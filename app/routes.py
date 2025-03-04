from dataclasses import field

from flask import jsonify, request
from jinja2.utils import missing

from app import app
import json
import requests
from app.models import Product, Order
from app.database import database

TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
SHIPPING_COSTS = [(500, 5), (2000, 10), (float("inf"), 25)]

@app.route("/")
def get_products():
    products = Product.select()
    return jsonify({"products": [p.__data__ for p in products]}), 200


@app.route("/order", methods=["POST"])
def create_order():
    data = request.get_json()

    # Check if "product" exists
    if "product" not in data:
        return jsonify({"errors": {"product": {"code": "missing-fields", "name": "Product details required"}}}), 422

    # Check if "product" is a **list** (invalid case)
    if isinstance(data["product"], list):
        return jsonify({"errors": {"product": {"code": "invalid-format", "name": "Only one product is allowed per order"}}}), 422

    # Ensure "product" is a dictionary
    if not isinstance(data["product"], dict):
        return jsonify({"errors": {"product": {"code": "invalid-format", "name": "Product must be an object"}}}), 422

    # Ensure "product" has required fields
    if "id" not in data["product"] or "quantity" not in data["product"]:
        return jsonify({"errors": {"product": {"code": "missing-fields", "name": "Product ID and quantity are required"}}}), 422

    product_id = data["product"]["id"]
    quantity = data["product"]["quantity"]

    # Ensure quantity is valid
    if quantity < 1:
        return jsonify({"errors": {"product": {"code": "invalid-quantity", "name": "Quantity must be at least 1"}}}), 422

    #  Check if product exists
    product = Product.get_or_none(Product.id == product_id)
    if not product:
        return jsonify({"errors": {"product": {"code": "not-found", "name": "Product not found"}}}), 404

    # Check stock availability
    if not product.in_stock:
        return jsonify({"errors": {"product": {"code": "out-of-inventory", "name": "Product is out of stock"}}}), 422

    # Create order
    total_price = product.price * quantity
    order = Order.create(product=product, quantity=quantity, total_price=total_price)

    return jsonify({"order_id": order.id}), 302, {"Location": f"/order/{order.id}"}

@app.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    response_data = {
        "order": {
            "id": order.id,
            "total_price": order.total_price,
            "total_price_tax": order.total_price_tax if order.total_price_tax else 0.0,
            "email": order.email,
            "credit_card": {},
            "shipping_information": (
    {
        "country": order.country,
        "address": order.address,
        "postal_code": order.postal_code,
        "city": order.city,
        "province": order.province
    }
    if any([order.country, order.address, order.postal_code, order.city, order.province])
    else {}
)
,
            "paid": order.paid,
            "transaction": {},
            "product": {
                "id": order.product.id,
                "quantity": order.quantity
            },
            "shipping_price": order.shipping_price if order.shipping_price else 0.0
        }
    }

    return jsonify(response_data), 200


@app.route("/order/<int:order_id>", methods=["PUT"])
def update_order_and_pay(order_id):
    order = Order.get_or_none(Order.id == order_id)

    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    data = request.get_json()

    is_update = False
    is_payment = False

    if "order" in data and "credit_card" in data:
        return jsonify({"errors": {"order": {
            "code": "invalid-operation",
            "name": "Cannot update shipping info and pay at the same time"
        }}}), 422

    elif "order" in data:
        is_update = True

    elif "credit_card" in data:
        is_payment = True

    if is_update:
        if "order" not in data or "shipping_information" not in data["order"] or "email" not in data["order"]:
            return jsonify({"errors": {"order": {
                "code": "missing-fields",
                "name": "Shipping info & email required"
            }}}), 422

        # Validate email is not empty or just spaces
        email = data["order"]["email"].strip() if data["order"]["email"] else ""
        if not email:
            return jsonify({"errors": {"email": {"code": "invalid-email", "name": "Email cannot be empty"}}}), 422

        shipping_info = data["order"]["shipping_information"]

        required_fields = ["country", "address", "postal_code", "city", "province"]

        missing_fields = [field for field in required_fields if not shipping_info.get(field)]
        if missing_fields:
            return jsonify({"errors": {"shipping_information": {
                "code": "invalid-fields",
                "name": f"Missing or empty fields: {', '.join(missing_fields)}"
            }}}), 422

        order.email = data["order"]["email"]
        order.country = shipping_info["country"]
        order.address = shipping_info["address"]
        order.postal_code = shipping_info["postal_code"]
        order.city = shipping_info["city"]
        order.province = shipping_info["province"]

        # Calculate tax
        tax_rate = TAX_RATES.get(order.province, 0)
        order.total_price_tax = order.total_price * (1 + tax_rate)

        # Calculate shipping price
        weight = order.product.weight * order.quantity
        order.shipping_price = next(price for max_weight, price in SHIPPING_COSTS if weight <= max_weight)

        order.save()

        response_data = {
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "total_price_tax": order.total_price_tax if order.total_price_tax else 0.0,
                "email": order.email,
                "credit_card": {},
                "shipping_information": (
                    {
                        "country": order.country,
                        "address": order.address,
                        "postal_code": order.postal_code,
                        "city": order.city,
                        "province": order.province
                    }
                    if any([order.country, order.address, order.postal_code, order.city, order.province])
                    else {}
                )
                ,
                "paid": order.paid,
                "transaction": {},
                "product": {
                    "id": order.product.id,
                    "quantity": order.quantity
                },
                "shipping_price": order.shipping_price if order.shipping_price else 0.0
            }
        }

        return jsonify(response_data), 200
    if is_payment:
        # Cannot pay twice
        if order.paid:
            return jsonify({"errors": {"order": {"code": "already-paid", "name": "Order already paid"}}}), 422

        # Check if order has required information
        if not order.email or not all([order.country, order.address, order.postal_code, order.city, order.province]):
            return jsonify({"errors": {"order": {
                "code": "missing-fields",
                "name": "Order must have email and shipping information before payment"
            }}}), 422

        # Extract and validate credit card details
        credit_card = data["credit_card"]
        required_card_fields = ["number", "expiration_year", "expiration_month", "cvv", "name"]

        if not all(k in credit_card for k in required_card_fields):
            return jsonify({"errors": {"payment": {
                "code": "invalid-fields",
                "name": "Incomplete credit card details"
            }}}), 422

        # Format payment data
        payment_data = {
            "credit_card": {
                "number": credit_card["number"],
                "expiration_month": credit_card['expiration_month'],
                "expiration_year": credit_card['expiration_year'],
                "cvv": credit_card["cvv"]
            },
            "amount_charged": order.total_price_tax + order.shipping_price
        }
        print("DEBUG - Payment Data Sent to API:", json.dumps(payment_data, indent=4))

        # Send payment request to remote payment API
        PAYMENT_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
        headers = {"Host": "dimensweb.uqac.ca", "Content-Type": "application/json"}

        try:
            response = requests.post(PAYMENT_URL, json=payment_data, headers=headers)
            print("DEBUG - Payment API Response Code:", response.status_code)
            print("DEBUG - Payment API Response Text:", response.text)

            if response.status_code != 200:
                return jsonify(response.json()), 422

            payment_response = response.json()

        except requests.exceptions.RequestException as e:
            print("ERROR - Payment API Request Failed:", str(e))
            return jsonify({"errors": {"payment": {
                "code": "server-error",
                "name": "Payment service unavailable"
            }}}), 500

        # Mark order as paid and save transaction details
        order.paid = True
        order.transaction_id = payment_response["transaction"]["id"]
        order.save()

        # Extract first and last digits of card number
        first_digits = credit_card["number"][:4]
        last_digits = credit_card["number"][-4:]

        return jsonify({
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
                "product": {
                    "id": order.product.id,
                    "quantity": order.quantity
                },
                "shipping_price": order.shipping_price
            }
        }), 200


    return jsonify({"errors": {"order": {"code": "invalid-request", "name": "Invalid request format"}}}), 400










