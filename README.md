# Stock Prediction Portal

A full-stack stock analysis app by Harsh Gavand, built with React, Django REST Framework, and a pretrained LSTM model.

**Live application:** https://stock-prediction-portal-kohl.vercel.app/

Create an account, save a watchlist, fetch the latest available Yahoo Finance quotes, and compare model estimates with historical closing prices. The dashboard includes price history, 100-day and 200-day moving averages, historical evaluation metrics, and an experimental next-session closing-price estimate.

## Architecture

```text
Browser → Vercel React frontend
        → /api/v1/* → Vercel Python function → Django REST API
                                           → Neon PostgreSQL
                                           → Yahoo Finance
                                           → NumPy LSTM inference → in-memory PNG charts
```

The frontend and backend share one origin. Production users and watchlists live in PostgreSQL. SQLite is available for local development only; the app refuses to start on Vercel without a database URL. No production chart or account data depends on a function's local filesystem.

## Features

- Registration, JWT login and token refresh, profile editing, and logout.
- Per-user watchlists with at most 10 validated, unique tickers, including empty watchlists.
- Latest available market quotes, currency and timestamp, refreshed every minute.
- Around 10 years of daily price history when available from the provider.
- Four expandable charts and MSE, RMSE, and R-squared metrics.
- Light and dark themes, responsive layouts, and direct navigation to frontend routes.
- Real model inference using weights exported from the original Keras model.

## Local setup

Use Python 3.12 and Node.js 22. Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item backend-drf/.env.example backend-drf/.env
npm --prefix frontend-react ci
```

Replace the placeholder `SECRET_KEY` in `backend-drf/.env` with a long random value. Then:

```powershell
.\.venv\Scripts\python.exe backend-drf/manage.py migrate
.\.venv\Scripts\python.exe backend-drf/manage.py runserver
```

In a second terminal:

```powershell
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` to http://127.0.0.1:8000. The frontend defaults to `/api/v1`; set `VITE_API_BASE_URL` only when using another backend origin.

## Deploy to Vercel

The root `vercel.json` builds `frontend-react`, serves its static assets, and routes API requests to `api/index.py`. Python 3.12 and Node.js 22 are pinned. The runtime dependency file excludes TensorFlow, which is needed only for reference verification.

1. Import this repository into Vercel, using the repository root.
2. Connect a dedicated Neon PostgreSQL database through Vercel Storage. Select the Free plan if that suits your usage.
3. Set production variables:
   - `DATABASE_URL`: the SSL connection URL supplied by the integration.
   - `SECRET_KEY`: a securely generated, stable random secret.
   - `DEBUG=False`.
   - `ALLOWED_HOSTS`: your production hostname. Vercel deployment and project hostnames are also read from Vercel's environment.
   - `CSRF_TRUSTED_ORIGINS`: your production HTTPS origin.
4. Initialize the database before the first production launch:

```powershell
npx vercel link
npx vercel env pull .env.production.local --environment production
.\.venv\Scripts\python.exe scripts/production_manage.py migrate --noinput
npx vercel --prod
```

Use `scripts/production_manage.py migrate --noinput` before deploying future schema changes too. Never run production database migrations against the local SQLite database by mistake. Keep all environment files and tokens private; only placeholder example files are tracked.

`GET /api/v1/health/` checks database connectivity and model loading. Admin pages remain available with a local Django server; the public Vercel configuration exposes the application API and React routes.

## Model provenance and evaluation

The original file is `backend-drf/stock_prediction_model.keras`. Its architecture is:

```text
100 daily closes → LSTM(128, return sequences) → LSTM(64) → Dense(25) → Dense(1)
```

`scripts/export_model.py` extracts its weights into `stock_prediction_weights.npz`. The inference code implements the same LSTM and Dense equations with NumPy. The source model checksum and numerical verification are recorded in `backend-drf/model_manifest.json`.

The exported implementation was compared with TensorFlow on 11 input sequences, including random inputs, zeros, ones, and values outside the training scale. Maximum absolute difference: **2.384185791015625e-7**. Tests also compare against a saved TensorFlow reference. To regenerate that reference, use a separate Python environment with `tensorflow-cpu==2.21.0`, `h5py`, and `threadpoolctl`, then run:

```powershell
python scripts/export_model.py --verify
```

Scaling is fitted to the first 70% of the downloaded history; the remaining 30% is used for historical comparison. This fixes the original code's scaling of evaluation data. The model is already pretrained; its original training period and symbol coverage are not established by this repository, so the displayed comparison is **not a guarantee of unseen-data performance**. R-squared is a fit statistic, not a confidence probability. The next-session value is an experimental estimate, not a guaranteed future price.

## Verification

```powershell
.\.venv\Scripts\python.exe backend-drf/manage.py test accounts.tests api.tests --verbosity 2
.\.venv\Scripts\python.exe backend-drf/manage.py check
.\.venv\Scripts\python.exe backend-drf/manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pip check
npm run lint
npm --prefix frontend-react audit --audit-level=moderate
npm run build
```

GitHub Actions runs these offline checks. The live smoke test creates a synthetic account and uses real provider data:

```powershell
.\.venv\Scripts\python.exe scripts/live_smoke.py https://stock-prediction-portal-kohl.vercel.app
```

Credentials and full chart responses from this script remain under ignored `.tmp/`. See `docs/VERIFICATION.md` for the recorded deployment checks.

## API

All application endpoints use the `/api/v1/` prefix.

| Method | Endpoint | Authentication |
|---|---|---|
| GET | health/ | Public |
| POST | register/ | Public |
| POST | token/ | Public |
| POST | token/refresh/ | Refresh token |
| GET | protected-view/ | Access token |
| GET / PATCH | profile/ | Access token |
| GET / POST | portfolio/ | Access token |
| POST | live-prices/ | Access token |
| POST | predict/ | Access token |

Prediction request: `{"ticker":"AAPL"}`. Quote request: `{"tickers":["AAPL","RELIANCE.NS"]}`. Chart response fields keep the original names (`plot_img`, `plot_100_dma`, `plot_200_dma`, `plot_prediction`) and now contain self-contained PNG data URIs.

## Operational limits

Yahoo Finance is an external, unofficial data source and may delay, rate-limit, or temporarily reject requests. Provider failures produce clear errors; the app does not substitute fabricated prices. Historical responses and completed predictions are cached for 15 minutes per function process; quotes are cached for one minute. Caches and DRF request throttles are process-local, so they do not enforce a shared global limit across scaled function instances.

Vercel cold starts can add latency. Hosting and database free-plan quotas still apply. Secrets, persistent database contents, and generated verification accounts are excluded from Git.

The `Resources/` folder preserves the original notebooks, sample datasets, and other training artifacts; it is excluded from Vercel uploads.
