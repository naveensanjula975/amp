#!/bin/bash
# automated-trading-bot VPS Ubuntu Installation Script
# Run this via terminal: sudo ./setup_vps.sh

echo "============================================="
echo "   Automated Trading Bot VPS Setup Script    "
echo "============================================="

# 1. Update OS and Install requirements
echo "[1/7] Updating apt repositories and installing packages..."
apt-get update
apt-get install -y python3-pip python3-venv nginx ufw certbot python3-certbot-nginx

# 2. Firewall configuration (UFW)
echo "[2/7] Configuring UFW Firewall (allow SSH, HTTP, HTTPS)..."
# In case UFW isn't enabled yet, apply default rules
ufw default deny incoming
ufw default allow outgoing
ufw allow 'Nginx Full' # allows ports 80 and 443
ufw allow OpenSSH      # allows ssh on port 22
ufw --force enable

# 3. Setting up Python environment
echo "[3/7] Setting up Python virtual environment..."
cd /home/ubuntu/automated-trading-bot || exit 1
python3 -m venv venv
source venv/bin/activate
pip install gunicorn uvicorn
pip install -r requirements.txt

# 4. Configure Gunicorn configuration
echo "[4/7] Verifying gunicorn configuration..."
if [ ! -f "gunicorn_conf.py" ]; then
    echo "Creating basic gunicorn config."
    echo "workers = 2" > gunicorn_conf.py
    echo "bind = '127.0.0.1:8000'" >> gunicorn_conf.py
    echo "worker_class = 'uvicorn.workers.UvicornWorker'" >> gunicorn_conf.py
    echo "accesslog = '/home/ubuntu/automated-trading-bot/gunicorn_access.log'" >> gunicorn_conf.py
    echo "errorlog = '/home/ubuntu/automated-trading-bot/gunicorn_error.log'" >> gunicorn_conf.py
fi

# 5. Configuring systemd service
echo "[5/7] Establishing systemd service..."
cp deploy/tradingbot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tradingbot
systemctl restart tradingbot

# 6. Configure Nginx proxy
echo "[6/7] Linking Nginx reverse proxy..."
cp deploy/nginx_tradingbot.conf /etc/nginx/sites-available/tradingbot
ln -sf /etc/nginx/sites-available/tradingbot /etc/nginx/sites-enabled/
# Remove default nginx binding if it exists
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# 7. Ask for domain setting to install SSL certificate
echo "[7/7] Checking for HTTPS configuration (Certbot)..."
echo "To finish your setup, please ensure your DNS is pointing your domain to this VPS IP."
read -p "Do you want to run certbot now to enforce HTTPS mapping? (y/n) " config_ssl
if [[ "$config_ssl" == "y" || "$config_ssl" == "Y" ]]; then
    read -p "Enter your live Domain name (e.g. tradingbot.mydomain.com): " domain_name
    
    # Quick replace in the nginx config
    sed -i "s/tradingbot.yourdomain.com/$domain_name/g" /etc/nginx/sites-available/tradingbot
    systemctl reload nginx
    certbot --nginx -d $domain_name
else
    echo "Skipping SSL cert generation. You can always run: sudo certbot --nginx -d YOUR_DOMAIN.com manually later."
fi

echo "============================================="
echo "   Deployment Complete! The Trading Bot is Live. "
echo "   Monitor logs via: sudo journalctl -fu tradingbot  "
echo "============================================="
