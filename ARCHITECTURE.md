# 🏗️ Architecture & Data Flow

## System Overview

The bot is a **3-layer pipeline** connecting TradingView signals to live broker execution:

```
┌──────────────────────────────────────────────────────────────────┐
│                         TRADINGVIEW                              │
│   Pine Script Strategy  →  Alert Fires  →  HTTP POST (JSON)     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │  HTTPS  (TradingView Webhook)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     VPS  (Ubuntu 22.04)                          │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │          Nginx (Reverse Proxy + SSL Termination)        │   │
│   │              Port 443 (HTTPS)  →  Port 8000             │   │
│   └──────────────────────────┬──────────────────────────────┘   │
│                              │                                   │
│   ┌──────────────────────────▼──────────────────────────────┐   │
│   │       Gunicorn + Uvicorn Workers (ASGI)                 │   │
│   │   ┌─────────────────────────────────────────────────┐   │   │
│   │   │              FastAPI Application                │   │   │
│   │   │  ┌────────────┐ ┌──────────────┐ ┌──────────┐  │   │   │
│   │   │  │Secret Auth │ │  Dedup Cache │ │  Logger  │  │   │   │
│   │   │  └────────────┘ └──────────────┘ └──────────┘  │   │   │
│   │   │  ┌─────────────────────────────────────────┐   │   │   │
│   │   │  │      Pydantic Payload Validation        │   │   │   │
│   │   │  └─────────────────────────────────────────┘   │   │   │
│   │   └─────────────────────────┬───────────────────────┘   │   │
│   └─────────────────────────────│───────────────────────────┘   │
│                                 │                                │
│   ┌─────────────────────────────▼───────────────────────────┐   │
│   │                  broker.py                              │   │
│   │          AMP Futures REST API Client                    │   │
│   │  Authenticate → Build Order → Submit → Handle Response  │   │
│   │  Retry Logic (Tenacity): max 5 attempts, exponential    │   │
│   └─────────────────────────────┬───────────────────────────┘   │
└─────────────────────────────────│────────────────────────────────┘
                                  │  REST API (HTTPS)
                                  ▼
              ┌───────────────────────────────┐
              │      AMP Futures Broker       │
              │  (Paper Mode or Live Account) │
              └───────────────────────────────┘
```

---

## Component Breakdown

### `tradingview_strategy.pine`
- Pine Script v5 Moving Average Crossover strategy
- Generates structured JSON alert messages on crossover events
- Uses `strategy.entry()` with `alert_message=` for rich JSON webhooks
- Fires `buy`, `sell`, and `close` actions with pre-calculated stop loss and take profit levels

### `app/main.py` — FastAPI Application
- Entrypoints: `/webhook` (POST), `/health` (GET), `/status` (GET)
- Binds all API routers
- Instruments startup logging

### `app/api/webhooks.py` — Webhook Handler
- Validates the incoming secret token
- Runs deduplication check against in-memory hash cache (5-second window)
- Dispatches `buy`, `sell`, `close`, or `close_all` to the broker client
- Returns structured JSON responses for TradingView acknowledgment

### `app/core/broker.py` — Broker Client
- `AMPBroker` class using `httpx.AsyncClient` for async HTTP calls
- `authenticate()` — Handles API key session token retrieval
- `place_order()` — Sends Market, Limit, or Stop orders
- `get_positions()` — Retrieves open positions
- `get_account_info()` — Retrieves balance/equity
- `close_position()` — Detects and sends opposing market order
- All network calls wrapped in **Tenacity retry** with exponential backoff (up to 5 attempts)

### `app/schemas/payload.py` — Pydantic Validation
- Strict type coercion for all incoming fields
- `ActionEnum`: `buy`, `sell`, `close`, `close_all`
- `OrderTypeEnum`: `market`, `limit`, `stop`
- Validation rules: limit orders require `price`, stop orders require `stop_loss`

### `app/core/config.py` — Settings
- All environment variables managed through `python-decouple`
- Single `settings` singleton used across the application

### `deploy/` — Infrastructure
| File | Purpose |
|---|---|
| `setup_vps.sh` | Full VPS bootstrap: apt install, UFW, venv, systemd, nginx, certbot |
| `nginx_tradingbot.conf` | Reverse proxy config (port 443/80 → 8000) |
| `tradingbot.service` | Systemd daemon for auto-start and crash recovery |

---

## Retry & Resilience Strategy

```
API Call Attempt 1
     │ Fails (network error or 429)
     ▼
Wait 1s → Retry Attempt 2
     │ Fails
     ▼
Wait 2s → Retry Attempt 3
     │ Fails
     ▼
Wait 4s → Retry Attempt 4
     │ Fails
     ▼
Wait 8s → Retry Attempt 5
     │ Fails → Raise AMPBrokerAPIException
     ▼
HTTP 500 returned to TradingView → Alert logged
```

---

## Security Layers

| Layer | Mechanism |
|---|---|
| Network | UFW Firewall: Only OpenSSH + HTTPS allowed |
| Transport | HTTPS with Let's Encrypt SSL |
| Application | HMAC-style secret token per webhook request |
| Data | API keys stored only in `.env` — never committed to Git |
| Abuse | In-memory rate-limit style deduplication cache |
