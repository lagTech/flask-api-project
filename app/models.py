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

# Création des tables
database.connect()
database.create_tables([Product, Order])
database.close()
