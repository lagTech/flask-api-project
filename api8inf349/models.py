from peewee import Model, IntegerField, CharField, BooleanField, FloatField, ForeignKeyField, AutoField, TextField
from api8inf349.database import database

class BaseModel(Model):
    class Meta:
        database = database

class Product(BaseModel):
    id = AutoField()
    name = CharField()
    description = CharField()
    price = FloatField()
    weight = IntegerField()
    in_stock = BooleanField()
    image = CharField()

class Order(BaseModel):
    id = AutoField()
    total_price = FloatField()
    total_price_tax = FloatField(null=True)
    email = CharField(null=True)
    paid = BooleanField(default=False)
    shipping_price = FloatField(null=True)
    transaction_id = CharField(null=True)
    transaction_error = TextField(null=True)  # Nouveau champ pour stocker les erreurs de transaction

    # New Shipping Fields
    country = CharField(null=True)
    address = CharField(null=True)
    postal_code = CharField(null=True)
    city = CharField(null=True)
    province = CharField(null=True)

class OrderProduct(BaseModel):
    order = ForeignKeyField(Order, backref="products")
    product = ForeignKeyField(Product)
    quantity = IntegerField()