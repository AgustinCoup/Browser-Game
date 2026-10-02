"""Entorno de tests: SQLite en memoria, sin depender de MySQL ni de variables de entorno."""

import os

# Debe fijarse antes de importar base (que lee SECRET_KEY y DATABASE_URL).
# Se fuerzan (no setdefault) para que un DATABASE_URL real del entorno nunca afecte a los tests.
os.environ["SECRET_KEY"] = "test-only-not-a-secret"
os.environ["DATABASE_URL"] = "sqlite://:memory:"

from .base import *  # noqa: E402, F403

DATABASES["default"]["OPTIONS"] = {}  # noqa: F405  # 'charset' es solo de MySQL
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # tests rápidos
