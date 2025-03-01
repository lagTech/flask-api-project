from flask import jsonify, request
from app import app  # Import the global app instance from __init__.py
from app.models import Product, Order
from app.database import database  # Even if it's grey, leave it here in case we use it later

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Flask API!"})

@app.route("/products", methods=["GET"])
def get_products():
    products = Product.select()
    return jsonify({"products": [p.__data__ for p in products]}), 200

@app.route("/order", methods=["POST"])
def create_order():
    data = request.get_json()

    if "product" not in data or "id" not in data["product"] or "quantity" not in data["product"]:
        return jsonify({"errors": {
            "product": {"code": "missing-fields", "name": "La création d'une commande nécessite un produit"}}}), 422

    product_id = data["product"]["id"]
    quantity = data["product"]["quantity"]

    product = Product.get_or_none(Product.id == product_id)
    if not product:
        return jsonify({"errors": {"product": {"code": "not-found", "name": "Produit introuvable"}}}), 404

    if not product.in_stock:
        return jsonify({"errors": {
            "product": {"code": "out-of-inventory", "name": "Le produit demandé n'est pas en inventaire"}}}), 422

    order = Order.create(product=product, quantity=quantity, total_price=product.price * quantity)
    return jsonify({"order_id": order.id}), 302
