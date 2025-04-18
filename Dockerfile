FROM ubuntu:latest
LABEL authors="lacma"

ENTRYPOINT ["top", "-b"]
# Utilise une image de base officielle avec Python
FROM python:3.11-slim

# Crée un répertoire pour l'application
WORKDIR /app

# Copie les fichiers dans l’image Docker
COPY . .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Spécifie la variable d'environnement pour Flask
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0

# Port exposé
EXPOSE 5000

# Commande pour démarrer l’application
CMD ["flask", "run"]
