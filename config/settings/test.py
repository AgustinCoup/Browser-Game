"""Entorno de tests: SQLite en memoria, sin depender de MySQL ni de variables de entorno."""

import os

# Debe fijarse antes de importar base (que lee SECRET_KEY y DATABASE_URL).
os.environ.setdefault("SECRET_KEY", "test-only-not-a-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .base import *  # noqa: E402, F403

DATABASES["default"]["OPTIONS"] = {}  # noqa: F405  # 'charset' es solo de MySQL
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # tests rápidos
