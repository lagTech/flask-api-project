# Projet API Flask – 8INF349

Ce projet est une API Web écrite en Flask qui permet de gérer des commandes de produits. Il utilise PostgreSQL comme base de données relationnelle et Redis pour la mise en cache et la gestion de tâches asynchrones (RQ).

---

## 🧱 Structure

- `api8inf349/` : Dossier principal de l’application (anciennement `app/`)
- `Dockerfile` : Image Docker de l'application Flask
- `docker-compose.yml` : Démarrage de PostgreSQL (v12) et Redis (v5)
- `.env` : Configuration de la base de données et de Redis
- `requirements.txt` : Dépendances Python

---

## 🚀 Initialisation (exigée par la remise)

Dans un terminal :

```bash
SET FLASK_DEBUG=True
SET FLASK_APP=api8inf349
SET REDIS_URL=redis://localhost
SET DB_HOST=localhost
SET DB_USER=user
SET DB_PASSWORD=pass
SET DB_PORT=5432
SET DB_NAME=api8inf349

flask init-db
