#  Modifications apportées au projet – *changes-made.md*

## 1. Passage à PostgreSQL
- Remplacement de SQLite par `PostgresqlDatabase(...)` dans `api8inf349/database.py`.
- Connexion configurée via variables d’environnement :  
  `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

---

## 2. Docker & Docker Compose
Le fichier `docker-compose.yml` contient maintenant :
-  un service `postgres` (PostgreSQL v12)
-  un service `redis` (Redis v5)
-  un service `api` (Flask app)
  - J’ai ajouté ce service pour éviter de devoir reconstruire l’image manuellement à chaque fois.
-  un service `worker` (RQ worker)

 Chaque service expose les bons ports :
- `5432` pour PostgreSQL
- `6379` pour Redis
- `5000` pour l’API

 Utilisation du volume `pgdata` pour persister les données PostgreSQL.

---

## 3. Dockerfile
- Création d’un `Dockerfile` à la racine du projet.
- Utilisation de la commande `docker build -t api8inf349 .` pour builder l’image.
-  Optimisation : Ce build est maintenant intégré directement dans `docker-compose.yml`.
- Le conteneur API utilise `flask run --host=0.0.0.0`.

---

## 4. Initialisation de la base de données
- Ajout de la commande personnalisée `flask init-db` :
  - définie dans `commands.py`
  - ajoutée via `app.cli.add_command(...)` dans `__init__.py`

---

## 5. Commande avec plusieurs produits
- La route `POST /order` accepte maintenant un tableau `products: [{id, quantity}]`.
- Rétrocompatibilité assurée avec un seul objet `product`.

---

## 6. Paiement asynchrone (RQ)
- Extraction de la logique de paiement dans `tasks.py` (`process_payment`).
- Utilisation de RQ pour exécuter le paiement de manière asynchrone.
- Nouvelle route `PUT /order/<id>` pour initier le paiement avec les données `"credit_card": {...}`.
- Réponse HTTP `202` avec un `job_id`.
- Nouvelle route `GET /job/<job_id>` pour obtenir l’état du paiement.

---

## 7. Mise en cache avec Redis
- Après un paiement réussi, la commande est mise en cache dans Redis.
- Lors d’un `GET /order/<id>`, la réponse vient de Redis si elle est en cache.

---

## 8. Protection des commandes payées
- Si une commande est déjà payée, une requête `PUT` renvoie une erreur `409 Conflict`.
- Le champ `paid` est bien pris en compte et géré.

---

## 9. Autres éléments respectés
- `requirements.txt` mis à jour (Flask, Peewee, RQ, Redis, etc.).
- API testable avec Postman.
- Structure respectée : `models.py`, `routes.py`, `tasks.py`, `commands.py`, etc.
- Architecture backend + worker bien séparée.