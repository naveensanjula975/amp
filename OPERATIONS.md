# 🛠️ Operations Guide

Day-to-day monitoring, log access, and manual intervention procedures for the trading bot in production.

---

## Monitoring the Bot

### Check if the service is running
```bash
sudo systemctl status tradingbot
```

Expected output:
```
● tradingbot.service - Gunicorn daemon for Automated Futures Trading Bot
   Loaded: loaded (/etc/systemd/system/tradingbot.service; enabled)
   Active: active (running) since ...
```

### Stream live application logs
```bash
sudo journalctl -fu tradingbot
```

> **Tip:** Press `Ctrl+C` to exit the log stream.

### Check Nginx status (reverse proxy)
```bash
sudo systemctl status nginx
```

### Check Nginx access logs (incoming webhook hits)
```bash
sudo tail -f /var/log/nginx/access.log
```

---

## Starting, Stopping, Restarting

| Action | Command |
|---|---|
| Start the bot | `sudo systemctl start tradingbot` |
| Stop the bot | `sudo systemctl stop tradingbot` |
| Restart the bot | `sudo systemctl restart tradingbot` |
| Reload config (no downtime) | `sudo systemctl reload tradingbot` |

---

## Deploying a Code Update

After pushing changes to the repository on the VPS:

```bash
cd /home/ubuntu/automated-trading-bot

# Pull latest code
git pull origin main

# Activate venv and install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart the bot to pick up changes
sudo systemctl restart tradingbot

# Confirm it's running
sudo systemctl status tradingbot
```

---

## Testing the Live Endpoint

From your **local machine**, run the simulation script against the live server:

```bash
# Edit simulate_webhook.py first:
# Change WEBHOOK_URL to "https://your-domain.com/webhook"
python simulate_webhook.py
```

Or use `curl` directly from anywhere:
```bash
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_super_secret_webhook_token_here",
    "action": "buy",
    "symbol": "ES",
    "quantity": 1,
    "order_type": "market",
    "price": null,
    "stop_loss": 5100.0,
    "take_profit": 5250.0,
    "strategy": "Manual Test",
    "timestamp": "2026-03-31T10:00:00Z"
  }'
```

---

## Rotating the Webhook Secret

1. Choose a new strong random secret:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update the `.env` file on the VPS:
   ```bash
   nano /home/ubuntu/automated-trading-bot/.env
   # Update WEBHOOK_SECRET=<new_value>
   ```
3. Update the `webhookSecret` variable inside `tradingview_strategy.pine` to match.
4. Re-publish the alert in TradingView (delete and recreate the alert).
5. Restart the bot:
   ```bash
   sudo systemctl restart tradingbot
   ```

---

## Rotating AMP API Keys

1. Generate a new API key in your AMP Futures / CQG account dashboard.
2. Update `.env` on the VPS:
   ```bash
   nano /home/ubuntu/automated-trading-bot/.env
   # Update AMP_API_KEY=<new_key>
   ```
3. Restart the bot:
   ```bash
   sudo systemctl restart tradingbot
   ```

---

## Switching from Paper to Live Trading

> ⚠️ **CAUTION:** Only switch after a successful paper trading period. Real capital is at risk.

1. Update `.env` on the VPS:
   ```
   IS_PAPER_TRADING=False
   AMP_API_URL=https://api.cqg.com/v1   # Replace with the live (non-sandbox) base URL
   ```
2. Restart the bot:
   ```bash
   sudo systemctl restart tradingbot
   ```
3. Monitor the first few live trades closely via `sudo journalctl -fu tradingbot`.

---

## Manually Closing a Position (Emergency)

If you need to close a position immediately without waiting for a TradingView signal, send a `close` action manually via `curl`:

```bash
curl -X POST https://your-domain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "your_super_secret_webhook_token_here",
    "action": "close",
    "symbol": "ES",
    "quantity": 1,
    "order_type": "market",
    "timestamp": "2026-03-31T10:00:00Z"
  }'
```

---

## SSL Certificate Renewal

Let's Encrypt certificates expire every 90 days. Certbot installs an automatic renewal cron job by default. Verify it is active:

```bash
sudo systemctl status certbot.timer
```

To manually force-renew ahead of expiry:
```bash
sudo certbot renew --dry-run   # Test renewal safely
sudo certbot renew             # Perform actual renewal
sudo systemctl reload nginx    # Apply the new cert
```

---

## Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Bot not receiving alerts | Nginx not running | `sudo systemctl restart nginx` |
| `401 Unauthorized` in logs | Secret mismatch | Re-check `.env` `WEBHOOK_SECRET` vs Pine Script value |
| `500` errors in logs | Broker API down or bad credentials | Check broker API status and API key validity |
| Duplicate trades being placed | Dedup window too short | Increase `DEDUP_WINDOW_SECONDS` in `webhooks.py` |
| Bot stopped after VPS reboot | systemd not enabled | `sudo systemctl enable tradingbot` |
| SSL cert expired | Certbot timer inactive | Run `sudo certbot renew` |
