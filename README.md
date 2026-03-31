# Automated Futures Trading Bot

> **Automated trading pipeline: TradingView Pine Script → Python Webhook → AMP Futures Broker**

A production-ready automated futures trading system that bridges TradingView strategy alerts directly to the AMP Futures broker API for live or paper trade execution — running 24/7 on a cloud VPS.

---

## ✨ Features

- **Secure Webhook Receiver** — FastAPI endpoint with secret-token authentication
- **AMP Futures Broker Integration** — Market, Limit, and Stop order support with full retry logic
- **Duplicate Alert Prevention** — In-memory deduplication cache with configurable time window
- **Auto-Recovery Server** — `systemd` daemon for crash-recovery and server-reboot persistence
- **HTTPS by Default** — Nginx reverse proxy with Let's Encrypt SSL (Certbot)
- **Structured Logging** — Full request/response logging with timestamps across all layers
- **Paper Trading Mode** — Safe sandbox testing before going live

---

## 📁 Project Structure

```
automated-trading-bot/
├── app/
│   ├── api/
│   │   └── webhooks.py          # POST /webhook endpoint + deduplication
│   ├── core/
│   │   ├── broker.py            # AMP Futures API client module
│   │   ├── config.py            # Central settings via python-decouple
│   │   ├── logger.py            # Structured logging setup
│   │   └── security.py          # Webhook secret validation
│   ├── schemas/
│   │   └── payload.py           # Pydantic models for webhook payload
│   └── main.py                  # FastAPI application entrypoint
├── deploy/
│   ├── setup_vps.sh             # VPS automated install script
│   ├── nginx_tradingbot.conf    # Nginx reverse proxy config
│   └── tradingbot.service       # systemd service daemon
├── tradingview_strategy.pine    # TradingView Pine Script v5 strategy
├── simulate_webhook.py          # Local e2e webhook test script
├── sandbox_test.py              # Broker API sandbox tests (mocked)
├── requirements.txt
├── .env.example
├── DEPLOYMENT.md
├── ARCHITECTURE.md
├── API.md
└── OPERATIONS.md
```

---

## ⚡ Quick Start (Local Development)

### 1. Clone & configure environment
```bash
git clone <YOUR_REPO_URL>
cd automated-trading-bot

cp .env.example .env
# Edit .env with your credentials
```

### 2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test the webhook locally
```bash
python simulate_webhook.py
```

---

## 🚀 Production Deployment

See the full guide in [`DEPLOYMENT.md`](DEPLOYMENT.md).

**TL;DR on a fresh Ubuntu 22.04 VPS:**
```bash
sudo ./deploy/setup_vps.sh
```

---

## 📋 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `WEBHOOK_SECRET` | Secret token to validate incoming TradingView alerts | *(required)* |
| `AMP_API_URL` | AMP Futures broker REST API base URL | `https://api.cqg.com/sandbox/v1` |
| `AMP_API_KEY` | AMP Futures API authentication key | *(required)* |
| `AMP_ACCOUNT_ID` | Your broker account identifier | *(required)* |
| `IS_PAPER_TRADING` | `True` for sandbox mode, `False` for live trading | `True` |

---

## 📄 Documentation Index

| Document | Description |
|---|---|
| [`README.md`](README.md) | Project overview and quick start (this file) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design, data flow, and component diagram |
| [`API.md`](API.md) | Webhook payload spec and endpoint reference |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Step-by-step VPS deployment guide |
| [`OPERATIONS.md`](OPERATIONS.md) | Monitoring, logs, manual intervention guide |

---

## ⚠️ Disclaimer

This software is provided for educational purposes. Futures trading carries significant financial risk. Always paper trade first and consult a financial advisor before trading live capital.
