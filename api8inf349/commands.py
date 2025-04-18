import click
from flask import current_app
from flask.cli import with_appcontext
from api8inf349.models import Product, Order, OrderProduct
from api8inf349.database import database
from api8inf349.bootstrap import fetch_products


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Reinitialise la base de données PostgreSQL avec les tables nécessaires."""
    with database:
        database.drop_tables([OrderProduct, Order, Product])
        database.create_tables([Product, Order, OrderProduct])
    click.echo("Base de données initialisée.")

    fetch_products()
    click.echo("Products loaded")
