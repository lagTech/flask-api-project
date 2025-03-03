from flask import jsonify, request
from app import app
from app.models import Product, Order
from app.database import database
import requests

TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
SHIPPING_COSTS = [(500, 5), (2000, 10), (float("inf"), 25)]
PAYMENT_URL = "http://dimensweb.uqac.ca/~jgnault/shops/pay/"


@app.route("/")
def get_products():
    products = Product.select()
    return jsonify({"products": [p.__data__ for p in products]}), 200


@app.route("/order", methods=["POST"])
def create_order():
    data = request.get_json()

    if "product" not in data or "id" not in data["product"] or "quantity" not in data["product"]:
        return jsonify({"errors": {"product": {"code": "missing-fields", "name": "Product details required"}}}), 422

    product_id = data["product"]["id"]
    quantity = data["product"]["quantity"]

    if quantity < 1:
        return jsonify({"errors": {"product": {"code": "missing-fields", "name": "Quantity must be at least 1"}}}), 422

    product = Product.get_or_none(Product.id == product_id)

    if not product:
        return jsonify({"errors": {"product": {"code": "not-found", "name": "Product not found"}}}), 404

    if not product.in_stock:
        return jsonify({"errors": {"product": {"code": "out-of-inventory", "name": "Product is out of stock"}}}), 422

    total_price = product.price * quantity
    order = Order.create(product=product, quantity=quantity, total_price=total_price)

    return jsonify({"order_id": order.id}), 302, {"Location": f"/order/{order.id}"}


@app.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    return jsonify({"order": order.__data__}), 200


@app.route("/order/<int:order_id>/update", methods=["PUT"])
def update_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    data = request.get_json()
    if "order" not in data or "shipping_information" not in data["order"] or "email" not in data["order"]:
        return jsonify({"errors": {"order": {"code": "missing-fields", "name": "Shipping info & email required"}}}), 422

    shipping_info = data["order"]["shipping_information"]
    order.email = data["order"]["email"]
    order.country = shipping_info.get("country")
    order.address = shipping_info.get("address")
    order.postal_code = shipping_info.get("postal_code")
    order.city = shipping_info.get("city")
    order.province = shipping_info.get("province")

    # Calculate tax
    TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
    tax_rate = TAX_RATES.get(order.province, 0)
    order.total_price_tax = order.total_price * (1 + tax_rate)

    # Calculate shipping price
    SHIPPING_COSTS = [(500, 5), (2000, 10), (float("inf"), 25)]
    weight = order.product.weight * order.quantity
    order.shipping_price = next(price for max_weight, price in SHIPPING_COSTS if weight <= max_weight)

    order.save()

    return jsonify({
        "order": {
            "id": order.id,
            "email": order.email,
            "paid": order.paid,
            "product": {
                "id": order.product.id,
                "quantity": order.quantity
            },
            "shipping_information": {
                "country": order.country,
                "address": order.address,
                "postal_code": order.postal_code,
                "city": order.city,
                "province": order.province
            },
            "total_price": order.total_price,
            "total_price_tax": order.total_price_tax,
            "shipping_price": order.shipping_price
        }
    }), 200


import requests
from flask import jsonify

import json
import requests

@app.route("/order/<int:order_id>/pay", methods=["PUT"])
def pay_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    data = request.get_json()
    print("DEBUG - Received JSON from Postman:", json.dumps(data, indent=4))  # ✅ Verify what Flask receives

    if "credit_card" not in data or "amount_charged" not in data:
        return jsonify({"errors": {"payment": {"code": "missing-fields", "name": "Credit card details & amount required"}}}), 422

    payment_data = {
        "credit_card": {
            "number": data["credit_card"]["number"],
            "expiration": f"{data['credit_card']['expiration_month']}/{data['credit_card']['expiration_year']}",
            "cvv": data["credit_card"]["cvv"]
        },
        "amount_charged": data["amount_charged"]
    }
    print("DEBUG - Payment Data Sent to API:", json.dumps(payment_data, indent=4))  # ✅ Verify forwarded request

    PAYMENT_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
    headers = {"Host": "dimensweb.uqac.ca", "Content-Type": "application/json"}

    try:
        response = requests.post(PAYMENT_URL, json=payment_data, headers=headers)
        print("DEBUG - Payment API Response Code:", response.status_code)
        print("DEBUG - Payment API Response Text:", response.text)  # ✅ Check payment API response

        if response.status_code != 200:
            return jsonify({"errors": {"payment": {"code": "failed", "name": "Payment processing failed"}}}), 422

        payment_response = response.json()
    except requests.exceptions.RequestException as e:
        print("ERROR - Payment API Request Failed:", str(e))
        return jsonify({"errors": {"payment": {"code": "server-error", "name": "Payment service unavailable"}}}), 500

    order.paid = True
    order.save()

    return jsonify({"order": {"id": order.id, "paid": order.paid, "transaction": payment_response}}), 200






