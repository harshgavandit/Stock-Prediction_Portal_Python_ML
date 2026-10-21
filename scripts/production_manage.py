"""Run Django management against the project's ignored Vercel environment file.

Usage: python scripts/production_manage.py migrate --noinput
Never prints connection strings or tokens.
"""
import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv

root = Path(__file__).resolve().parent.parent
settings = Config(RepositoryEnv(str(root / ".env.production.local")))
os.environ["DATABASE_URL"] = settings("DATABASE_URL")
sys.path.insert(0, str(root / "backend-drf"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_prediction_main.settings")
from django.core.management import execute_from_command_line
execute_from_command_line(["manage.py", *sys.argv[1:]])
