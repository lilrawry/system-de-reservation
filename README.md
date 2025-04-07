# Système de Réservation

Un système de réservation de salles développé avec Django.

## Fonctionnalités

- Gestion des salles (ajout, modification, suppression)
- Réservation de salles par les utilisateurs
- Interface d'administration pour les gestionnaires
- Authentification des utilisateurs
- Filtrage des salles par capacité, prix et disponibilité

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé sur votre système
2. Clonez ce dépôt sur votre machine locale

## Exécution du serveur

### Option 1: Utiliser les scripts fournis (recommandé)

#### Windows (CMD)
```
run_server.bat
```

#### Windows (PowerShell)
```
.\run_server.ps1
```

Ces scripts vont:
- Créer un environnement virtuel s'il n'existe pas
- Activer l'environnement virtuel
- Installer les dépendances nécessaires
- Démarrer le serveur de développement Django

### Option 2: Configuration manuelle

1. Créez un environnement virtuel:
```
python -m venv .venv
```

2. Activez l'environnement virtuel:
```
# Windows (CMD)
.venv\Scripts\activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

3. Installez les dépendances:
```
pip install django pillow django-debug-toolbar
```

4. Accédez au répertoire du projet:
```
cd DjangoProject1
```

5. Exécutez les migrations:
```
python manage.py migrate
```

6. Créez un superutilisateur (optionnel):
```
python manage.py createsuperuser
```

7. Démarrez le serveur de développement:
```
python manage.py runserver
```

## Accès à l'application

- Interface utilisateur: http://127.0.0.1:8000/
- Interface d'administration: http://127.0.0.1:8000/admin/

## Structure du projet

- `DjangoProject1/`: Répertoire principal du projet Django
  - `rooms/`: Application de gestion des salles et réservations
  - `templates/`: Templates HTML pour l'interface utilisateur
  - `static/`: Fichiers statiques (CSS, JavaScript, images)
  - `media/`: Fichiers média uploadés par les utilisateurs 