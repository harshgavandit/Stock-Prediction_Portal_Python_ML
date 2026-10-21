"""Vercel WSGI entrypoint; keep React and Django on the same origin."""
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib" if os.getenv("VERCEL") else ".tmp/matplotlib")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend-drf"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_prediction_main.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
