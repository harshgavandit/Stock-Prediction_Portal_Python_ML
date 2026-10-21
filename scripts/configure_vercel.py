"""Create this project's production settings using the existing Vercel CLI login."""
import json
import os
import secrets
from pathlib import Path

import requests

root = Path(__file__).resolve().parent.parent
auth = json.loads((Path(os.environ["APPDATA"]) / "com.vercel.cli/Data/auth.json").read_text())
project = json.loads((root / ".vercel/project.json").read_text())
base = f"https://api.vercel.com/v10/projects/{project['projectId']}/env"
values = {
    "SECRET_KEY": secrets.token_urlsafe(64), "DEBUG": "False",
    "ALLOWED_HOSTS": "stock-prediction-portal-kohl.vercel.app,localhost,127.0.0.1",
    "CSRF_TRUSTED_ORIGINS": "https://stock-prediction-portal-kohl.vercel.app",
}
# Preserve the project's existing secret if this setup script is rerun.
current = requests.get(base, headers={"Authorization": f"Bearer {auth['token']}"},
                       params={"teamId": project["orgId"]}, timeout=30)
current.raise_for_status()
existing = {item["key"] for item in current.json()["envs"]}
payload = [{"key": key, "value": value, "type": "encrypted", "target": ["production"]}
           for key, value in values.items() if key != "SECRET_KEY" or key not in existing]
response = requests.post(base, params={"teamId": project["orgId"], "upsert": "true"},
                         headers={"Authorization": f"Bearer {auth['token']}"},
                         json=payload, timeout=30)
response.raise_for_status()
print("Production settings configured; secret values were not displayed.")
