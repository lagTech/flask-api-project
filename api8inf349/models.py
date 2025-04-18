from peewee import Model, IntegerField, CharField, BooleanField, FloatField, ForeignKeyField
from app.database import database

class BaseModel(Model):
    class Meta:
        database = database

class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = CharField()
    price = FloatField()
    weight = IntegerField()
    in_stock = BooleanField()
    image = CharField()

class Order(BaseModel):
    id = IntegerField(primary_key=True)
    product = ForeignKeyField(Product, backref="orders")
    quantity = IntegerField()
    total_price = FloatField()
    total_price_tax = FloatField(null=True)
    email = CharField(null=True)
    paid = BooleanField(default=False)
    shipping_price = FloatField(null=True)
    transaction_id = CharField(null=True)

    # New Shipping Fields
    country = CharField(null=True)
    address = CharField(null=True)
    postal_code = CharField(null=True)
    city = CharField(null=True)
    province = CharField(null=True)
