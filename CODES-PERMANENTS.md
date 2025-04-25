## Code Permanents
- LACU01010000
- SANJ10048604
- CAMM06609200
- NGUC13569800

## Lien github
-https://github.com/lagTech/flask-api-project

## Lien de la video(presentation)
https://uqac.ca.panopto.com/Panopto/Pages/Viewer.aspx?id=4bb0064e-f631-4ccc-a5dd-b2ca010fbe22


## Guide d'exécution locale de l'application

Voici les étapes à suivre pour exécuter correctement ce projet Flask avec PostgreSQL et Redis via Docker.

## Prérequis

1. **Installer Docker Desktop** : Assurez-vous que Docker est installé et fonctionne sur votre machine.
2. **Cloner le dépôt Git** contenant le projet sur votre machine locale.
3. **Lancer Docker Desktop** pour démarrer l’environnement de conteneurisation.

>

## Démarrage des services via Docker Compose

Ouvrez un terminal à la racine du projet, puis :

```bash
# Lancer PostgreSQL, Redis, l'API Flask et le worker
$ docker-compose up -d
```

Cela lance les services suivants :

- PostgreSQL (port 5432)
- Redis (port 6379)
- L'application Flask (port 5000)
- Le worker pour exécuter les paiements

## Construction de l'image de l'application (optionnel)

Cela est déjà inclus dans `docker-compose.yml`. Vous n'avez donc **pas besoin** de construire manuellement l'image ni d'exécuter la commande `docker run` avec tous les paramètres nécessaires comme indiqué dans le PDF de consignes.

Cependant, si vous souhaitez tester manuellement en dehors de Docker Compose, voici la commande :

```bash
$ docker build -t api8inf349 .
```

Et pour exécuter manuellement l'application avec tous les paramètres requis (non nécessaire si vous utilisez `docker-compose.yml`) :

```bash
docker run -p 5000:5000   -e FLASK_APP=api8inf349   -e FLASK_DEBUG=True   -e REDIS_URL=redis://host.docker.internal   -e DB_HOST=host.docker.internal   -e DB_USER=postgres   -e DB_PASSWORD=secret123   -e DB_PORT=5432   -e DB_NAME=api8inf349   api8inf349
```

## Initialisation de la base de données

Une fois les conteneurs démarrés, initialisez la base de données PostgreSQL et chargez les produits : (dans un autre terminal, sans arrêter l'app en cours, utilisez la commande suivante)

```bash
$ docker exec -it <nom_du_conteneur_ou_ID> flask init-db
```

Exemple :

```bash
$ docker exec -it flask-api-project-api-1 flask init-db
```

> 📝 `flask-api-project-api-1` est le nom du conteneur Flask API généré par Docker Compose (vérifiez avec `docker ps` si besoin).

## Tester l'API

L'API est disponible sur :

```
http://localhost:5000
```

Vous pouvez tester les routes avec **Postman** ou un autre client HTTP.

Exemples utiles :

- `GET /` : liste des produits
- `POST /order` : création d'une commande
- `PUT /order/<id>` : mettre à jour ou payer une commande
- `GET /job/<job_id>` : vérifier le statut d'un paiement asynchrone

---

### Remarques

- **Pas besoin d'installer PostgreSQL localement** : tout est géré via Docker avec un utilisateur `postgres` et mot de passe `secret123`.
- Les données de PostgreSQL sont persistées dans le volume nommé `pgdata`.
- En cas d'erreur liée aux tables manquantes, revérifiez que la commande `flask init-db` a bien été exécutée dans le bon conteneur.


