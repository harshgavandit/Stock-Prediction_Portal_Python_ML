# Stock Prediction Portal

A stock analysis app for checking market prices, saving a personal watchlist, and viewing price estimates from a trained LSTM model.

- Search for stocks using ticker symbols such as AAPL, TSLA, or RELIANCE.NS.
- View the latest available market quotes and historical closing prices.
- See 100-day and 200-day moving average charts.
- Compare the model's estimates with historical prices and review MSE, RMSE, and R-squared.
- View an experimental estimate for the next session's closing price.
- Create an account, save up to 10 stocks in a watchlist, and update profile details.

[Open the app](https://stock-prediction-portal-kohl.vercel.app/) · [Deployment verification](docs/VERIFICATION.md)

## Architecture

```text
React/Vite → JWT-authenticated Django REST API
  ├─ account/profile/watchlist → SQLite locally or PostgreSQL on Vercel
  └─ ticker → Yahoo Finance history → 100-close sequences
       → exported LSTM weights + NumPy inference
       → historical comparison, next-close estimate, and four PNG charts
```

| Code | Responsibility |
| --- | --- |
| [`frontend-react/src/`](frontend-react/src/) | Registration/login, token refresh, dashboard, chart display, watchlist, and profile editing. |
| [`backend-drf/accounts/`](backend-drf/accounts/) | Password validation, JWT endpoints, per-user profiles, and watchlist persistence/validation. |
| [`backend-drf/api/market.py`](backend-drf/api/market.py) | Bounded Yahoo Finance requests, alternate provider host/yfinance fallback, and process-local market-data caching. |
| [`backend-drf/api/inference.py`](backend-drf/api/inference.py) | Two LSTM layers and two Dense layers evaluated with committed NumPy weights. |
| [`backend-drf/api/views.py`](backend-drf/api/views.py) | Input validation, historical comparison, metrics, next-close inference, and Matplotlib charts returned as PNG data URIs. |
| [`api/index.py`](api/index.py), [`vercel.json`](vercel.json) | Same-origin React deployment and Django WSGI routing on Vercel. |

The runtime uses weights exported from the existing Keras model; it does not train a model for each ticker and does not require TensorFlow to serve predictions. [`scripts/export_model.py`](scripts/export_model.py) and [`backend-drf/model_manifest.json`](backend-drf/model_manifest.json) document the export. A committed TensorFlow reference fixture checks the NumPy implementation.

For historical comparison, the API scales prices using the first 70% of returned history and compares the pretrained model's estimates against the remaining 30%. Each input contains 100 closing prices. This split avoids fitting the scaler on the comparison prices; it does not establish that those prices were absent from the original model's training data.

## Run locally

Use Python 3.12 and Node.js 22. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item backend-drf/.env.example backend-drf/.env
Copy-Item frontend-react/.env.example frontend-react/.env
npm --prefix frontend-react ci
```

On macOS/Linux, activate with `source .venv/bin/activate` and use `cp` for the two template copies. Set a long random `SECRET_KEY` in `backend-drf/.env` before starting Django.

| Variable | Location and purpose |
| --- | --- |
| `SECRET_KEY` | Backend signing secret; required. |
| `DEBUG` | Backend debug mode; the local template uses `True`. Use `False` on deployment. |
| `ALLOWED_HOSTS` | Comma-separated backend hostnames; the local template allows `localhost,127.0.0.1`. |
| `DATABASE_URL` | Optional backend PostgreSQL connection URL locally; required on Vercel. Without it, local development uses `backend-drf/db.sqlite3`. |
| `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | Optional backend origin lists; both default to `http://localhost:5173`. |
| `VITE_API_BASE_URL` | Frontend API path; the template uses `/api/v1`. Vite proxies `/api` to `http://127.0.0.1:8000` locally. |

Run migrations and start the backend:

```powershell
python backend-drf/manage.py migrate
python backend-drf/manage.py runserver 127.0.0.1:8000
```

In a second terminal, from the repository root:

```powershell
npm --prefix frontend-react run dev -- --host localhost
```

Open <http://localhost:5173>, register an account, and use the dashboard. Market requests need network access to Yahoo Finance; no market API key is configured by this app. `/api/v1/health/` checks the database connection and model-weight loading without requesting quotes.

## Tests and verification

With the Python environment active and the backend secret configured:

```powershell
python -m pip check
python backend-drf/manage.py check
python backend-drf/manage.py makemigrations --check --dry-run
python backend-drf/manage.py test accounts.tests api.tests --verbosity 2
npm --prefix frontend-react run lint
npm --prefix frontend-react run build
```

The Django tests cover authentication/refresh, private endpoints, weak passwords, profile changes, watchlist validation/isolation, empty-watchlist persistence, bad tickers, provider errors, short history, model parity, finite metrics, and PNG generation. Market responses are mocked for inference tests; the committed weights run against synthetic prices. [GitHub Actions](.github/workflows/ci.yml) runs these checks with Python 3.12 and Node.js 22, plus a frontend dependency audit.

[`scripts/live_smoke.py`](scripts/live_smoke.py) separately exercises a deployed app with real market requests and a newly created synthetic account. It changes account/watchlist state and stores local artifacts under ignored `.tmp/`. The [21 October verification record](docs/VERIFICATION.md) distinguishes those public API/browser observations from offline tests and records the original-model parity comparison. Its prices, fit metrics, and request timings are dated observations.

## Deployment and limits

Vercel builds `frontend-react/dist` and routes `/api/v1/*` to Django. Configure `SECRET_KEY`, `DEBUG=False`, appropriate host/origin lists, and a dedicated persistent PostgreSQL `DATABASE_URL`, then apply the Django migrations to that database. A local SQLite file is not persistent deployment storage. The committed exported weights are included in the Python application; rebuilding the frontend does not retrain them.

Historical MSE, RMSE, and R-squared describe the displayed comparison, not a trading strategy or a probability of future accuracy. The repository does not establish the original model's training dates or symbol coverage. The next-session estimate is experimental; quotes may be delayed and depend on Yahoo Finance availability. Caches and throttles are process-local rather than shared admission controls across instances. There is no brokerage integration or order execution.
