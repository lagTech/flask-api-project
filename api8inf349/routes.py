from flask import jsonify, request
from api8inf349 import app
import json
import os
import requests
from rq import Queue
from rq.job import Job
from redis.exceptions import RedisError
from api8inf349.models import Product, Order, OrderProduct
from api8inf349.database import database
from api8inf349.redis_client import redis_client
from api8inf349.tasks import process_payment
from flask import send_from_directory


TAX_RATES = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
SHIPPING_COSTS = [(500, 5), (2000, 10), (float("inf"), 25)]

# @app.route("/")
# def get_products():
#     products = Product.select()
#     return jsonify({"products": [p.__data__ for p in products]}), 200


# Get products with pagination
@app.route("/")
def get_products():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    query = Product.select().paginate(page, limit)
    total = Product.select().count()

    return jsonify({
        "products": [p.__data__ for p in query],
        "total": total,
        "page": page
    }), 200

@app.route("/order", methods=["POST"])
def create_order():
    data = request.get_json()

    # Supporte `products` (nouveau format) ou `product` (ancien)
    products_data = []

    if "products" in data and isinstance(data["products"], list):
        products_data = data["products"]
    elif "product" in data and isinstance(data["product"], dict):
        products_data = [data["product"]]
    else:
        return jsonify({"errors": {"products": {
            "code": "missing-fields",
            "name": "Missing or invalid 'product(s)'"
        }}}), 422

    if not products_data:
        return jsonify({"errors": {"products": {
            "code": "empty",
            "name": "No products provided"
        }}}), 422

    # Création de la commande
    order = Order.create(total_price=0)
    total_price = 0

    for item in products_data:
        product_id = item.get("id")
        quantity = item.get("quantity", 1)

        if not product_id or quantity < 1:
            return jsonify({"errors": {"products": {
                "code": "invalid-entry",
                "name": f"Invalid product ID or quantity: {item}"
            }}}), 422

        product = Product.get_or_none(Product.id == product_id)
        if not product or not product.in_stock:
            return jsonify({"errors": {"products": {
                "code": "not-found",
                "name": f"Product ID {product_id} not found or out of stock"
            }}}), 422

        # Ajout à la table de liaison (OrderProduct)
        OrderProduct.create(order=order, product=product, quantity=quantity)
        total_price += product.price * quantity

    order.total_price = total_price
    order.save()

    # return jsonify({"order_id": order.id}), 302, {"Location": f"/order/{order.id}"}
    return jsonify({"order_id": order.id}), 201

@app.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    cached = redis_client.get(f"order:{order_id}")
    if cached:
        return jsonify(json.loads(cached)), 200

    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    product_entries = [
        {
            "id": op.product.id,
            "name": op.product.name,
            "quantity": op.quantity,
            "price": float(op.product.price)
        }
        for op in order.products
    ]

    # Préparer les données de transaction
    transaction_data = {}
    if order.transaction_id:
        transaction_data = {"id": order.transaction_id}
    elif order.transaction_error:
        try:
            transaction_data = json.loads(order.transaction_error)
        except:
            transaction_data = {"error": "payment-failed", "details": order.transaction_error}

    response_data = {
        "order": {
            "id": order.id,
            "total_price": order.total_price,
            "total_price_tax": order.total_price_tax or 0.0,
            "email": order.email,
            "credit_card": {},
            "shipping_information": {
                "country": order.country,
                "address": order.address,
                "postal_code": order.postal_code,
                "city": order.city,
                "province": order.province
            } if any([order.country, order.address, order.postal_code, order.city, order.province]) else {},
            "paid": order.paid,
            "transaction": transaction_data,
            "products": product_entries,
            "shipping_price": order.shipping_price or 0.0
        }
    }

    return jsonify(response_data), 200


@app.route("/order/<int:order_id>", methods=["PUT"])
def update_order_and_pay(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if not order:
        return jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}), 404

    if order.paid:
        return jsonify({"errors": {"order": {"code": "already-paid", "name": "Order is already paid and cannot be modified"}}}), 409

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
        shipping_info = data["order"].get("shipping_information", {})
        email = data["order"].get("email", "").strip()

        if not email or not all(shipping_info.get(field) for field in ["country", "address", "postal_code", "city", "province"]):
            return jsonify({"errors": {"order": {
                "code": "missing-fields",
                "name": "Shipping info & email required"
            }}}), 422

        order.email = email
        order.country = shipping_info["country"]
        order.address = shipping_info["address"]
        order.postal_code = shipping_info["postal_code"]
        order.city = shipping_info["city"]
        order.province = shipping_info["province"]

        tax_rate = TAX_RATES.get(order.province, 0)
        order.total_price_tax = order.total_price * (1 + tax_rate)

        total_weight = sum(op.product.weight * op.quantity for op in order.products)
        order.shipping_price = next(price for max_weight, price in SHIPPING_COSTS if total_weight <= max_weight)

        order.save()

        return get_order(order.id)  # Réutilise le format de GET

    if is_payment:
        if not order.email or not all([order.country, order.address, order.postal_code, order.city, order.province]):
            return jsonify({"errors": {"order": {
                "code": "missing-fields",
                "name": "Order must have email and shipping information before payment"
            }}}), 422

        credit_card = data["credit_card"]
        required_fields = ["number", "expiration_year", "expiration_month", "cvv", "name"]

        if not all(k in credit_card for k in required_fields):
            return jsonify({"errors": {"payment": {
                "code": "invalid-fields",
                "name": "Incomplete credit card details"
            }}}), 422

        payment_data = {
            "credit_card": {
                "number": credit_card["number"],
                "expiration_month": credit_card['expiration_month'],
                "expiration_year": credit_card['expiration_year'],
                "cvv": credit_card["cvv"]
            },
            "amount_charged": order.total_price_tax + order.shipping_price
        }

        q = Queue(connection=redis_client)
        job = q.enqueue(
            process_payment,
            order.id,
            payment_data,
            credit_card,
            "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
        )

        return jsonify({
            "message": "Payment processing started",
            "job_id": job.get_id()
        }), 202

    return jsonify({"errors": {"order": {"code": "invalid-request", "name": "Invalid request format"}}}), 400

@app.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_client)
    except RedisError:
        return jsonify({"error": "Redis unavailable"}), 503
    except Exception:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "id": job.id,
        "status": job.get_status(),
        "result": job.result if job.is_finished else None
    }

    return jsonify(response), 200

# additional method
@app.route("/order", methods=["GET"])
def list_orders():
    orders = Order.select().order_by(Order.id.desc())

    response = {
        "orders": []
    }

    for order in orders:
        response["orders"].append({
            "id": order.id,
            "email": order.email,
            "total_price": order.total_price,
            "paid": order.paid,
            "products_count": order.products.count()
        })

    return jsonify(response), 200

@app.route("/frontend/<path:path>")
def serve_frontend(path):
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    return send_from_directory(frontend_dir, path)

@app.route("/img/<filename>")
def serve_image(filename):
    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "static", "img")
    return send_from_directory(image_dir, filename)
