# 🚀 Phase 4: VPS Deployment Guide
*(For Ubuntu 22.04 LTS)*

This repository contains necessary scripts and templates under the `deploy/` directory to quickly stand up a production environment suitable for receiving TradingView Webhooks securely via HTTPS without downtime.

## Prerequisite Checklist
- [ ] A fresh VPS instance (DigitalOcean, AWS LightSail, Linode, AWS EC2, or equivalent) running **Ubuntu 22.04 LTS**
- [ ] Domain name or Sub-domain pointing to the VPS IP Address (A record) 
      *Note: TradingView requires webhooks properly secured with valid SSL certs on port 443 (HTTPS) OR port 80 (HTTP) which we'll configure.*

## Step 1: Initial Setup & Cloning

1. SSH into the server as the `ubuntu` user (or equivalent sudo user)
   ```shell
   ssh ubuntu@<YOUR_SERVER_IP>
   ```
2. Clone your repository.
   ```shell
   git clone <YOUR_GITHUB_REPO_URL> /home/ubuntu/automated-trading-bot
   cd /home/ubuntu/automated-trading-bot
   ```

## Step 2: Configure Environment

We need an `.env` file since this contains sensitive API keys. Copy the template and edit it:

```shell
cp .env.example .env
nano .env # Paste your webhook secret and AMP credentials here
```

> ⚠️ Ensure `WEBHOOK_SECRET` matches exactly the secret you entered into the Pine Script strategy!

## Step 3: Run the Auto Install Script

The included install shell script simplifies Python setup, installing requirements, establishing firewalls, Nginx reversing, and `systemd` persistence automatically:

```shell
chmod +x deploy/setup_vps.sh
sudo ./deploy/setup_vps.sh
```

**What this script does:**
1. Updates Apt repos.
2. Applies **UFW Firewalls** securing everything locally and locking external traffic strictly to `OpenSSH`, HTTP, and HTTPS.
3. Sets up Py-Venv inside `/home/ubuntu/automated-trading-bot/venv`
4. Uses `gunicorn` + `uvicorn` (ASGI gateway pattern for production concurrent routing) to run FastAPI.
5. Loads your `deploy/tradingbot.service` daemon so that if the bot crashes or server restarts, it kicks back on automatically.
6. Loads your `deploy/nginx_tradingbot.conf` config to map traffic port (80/443 -> 8000 internal port)
7. Automatically asks you if you want to run `certbot` to generate free Let's Encrypt SSL certificates. Have your DNS domain ready!

## Step 4: Verification (The "Live Endpoint" Test)

### Checking Logs
1. Verify the Python service is active without errors:
   ```shell
   sudo systemctl status tradingbot
   ```
2. View real-time application logs (useful for monitoring trades live):
   ```shell
   sudo journalctl -fu tradingbot
   ```

### Verifying TradingView Connection
At this point, use the `simulate_webhook.py` from your local machine, changing `WEBHOOK_URL` from `'http://127.0.0.1:8000/webhook'` to `'https://your-domain.com/webhook'`, and run it to verify traffic successfully loops across the public internet.

Finally, in TradingView:
1. Load up your finalized Pine Script.
2. Create an Alert.
3. Paste: `https://your-domain.com/webhook` into the Webhook URL field.
4. Input the correct JSON string we built in Pine Script.
5. Save the alert. Wait for the signal crossover. You will see traffic appear in `sudo journalctl -fu tradingbot` live.

---

> 🎉 **Phase 4 Complete**:
> VPS Provisioned · Nginx Reverse Proxy Configured · `systemd` applied · Firewalls hardened · Live endpoint mapped.
