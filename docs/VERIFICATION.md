# Deployment verification

Verified on 21 October 2026 (Asia/Kolkata).

Application: https://stock-prediction-portal-kohl.vercel.app/

## Local checks

- 14 Django tests passed: authentication, token refresh, weak-password rejection, private endpoints, profile changes, watchlist validation, per-user isolation, empty-watchlist persistence, input validation, provider errors, real model inference, PNG generation, and model parity.
- Django system checks and migration-drift checks passed.
- Python dependency consistency check passed.
- Frontend lint and production build passed.
- npm audit reported zero known vulnerabilities for the installed frontend dependency tree.

## Original-model comparison

The deployment uses NumPy inference with weights exported from the existing Keras model. TensorFlow/Keras verification ran in a separate local environment.

- Original model SHA-256: `51a404360133f38e6fecbe8e99557a62f9e7e1ef0a4f73ed9669bcbb23bb76b3`.
- Architecture: LSTM(128) -> LSTM(64) -> Dense(25) -> Dense(1).
- 11 input sequences compared, including random, zero, one, and out-of-scale values.
- Maximum absolute difference: `2.384185791015625e-7`.
- Committed TensorFlow reference fixture is exercised by the offline tests.

## Public API verification

The live smoke test passed 46 checks with synthetic account details. It called the public production URL without a Vercel authentication cookie or bypass token.

Verified readiness, direct frontend routes, unauthorized access rejection, registration, login, profile editing, watchlist saving, empty watchlist persistence, input rejection, token refresh, and state persistence across a new HTTP session and login.

Real Yahoo Finance quotes were returned for AAPL, RELIANCE.NS, TCS.NS, and INFY.NS. No canned market values were substituted.

| Symbol | Historical rows | Comparison rows | Historical RMSE | Historical R-squared | Measured prediction request |
|---|---:|---:|---:|---:|---:|
| AAPL | 2,512 | 754 | 6.376 | 0.9798 | 3.99 seconds |
| RELIANCE.NS | 2,471 | 742 | 20.975 | 0.9630 | 3.09 seconds |

All four chart fields returned decodable PNG images for both symbols. These values are a recorded snapshot and will change with incoming history. Request timings describe these observations and are not a latency guarantee.

## Browser verification

The public application was exercised in the in-app browser:

- Created a synthetic account and reached the dashboard automatically.
- Loaded current provider quotes.
- Added AAPL to the watchlist, reloaded, and confirmed it remained saved.
- Selected AAPL and generated its prediction.
- Confirmed all four chart images loaded.
- Opened and closed the enlarged historical-comparison chart.
- Updated the synthetic account's email and observed the success message.
- Logged out and signed back in.

Synthetic credentials, access tokens, and full response payloads are excluded from this report and Git.

## Boundaries

This verifies a deployed demonstration app. Historical comparison does not establish a guaranteed future return, and the repository does not establish the original model's training period or symbol coverage. R-squared is a fit statistic, not a probability.

Market prices depend on Yahoo Finance availability and may be delayed. Vercel and Neon quotas apply. Caching and API throttling are per process, not a shared global admission system.
