#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Bootstrap & Deploy Ticketly on DigitalOcean droplet
# Domain: arosai.in | Server: 64.227.176.214
# Usage: Run this script on the server as root
#   curl -fsSL https://raw.githubusercontent.com/naveen9871/ticket-booking/main/deploy.sh | bash
# Or scp and run:
#   scp deploy.sh root@64.227.176.214:/root/
#   ssh root@64.227.176.214 "bash /root/deploy.sh"
# =============================================================================
set -euo pipefail

DOMAIN="arosai.in"
REPO_URL="https://github.com/naveen9871/ticket-booking.git"
APP_DIR="/opt/ticket-booking"
EMAIL="your-email@example.com"   # <-- CHANGE THIS for Let's Encrypt notifications

echo "========================================"
echo "  Ticketly Deployment Script"
echo "  Domain: $DOMAIN"
echo "========================================"

# ─── 1. System Update ────────────────────────────────────────────────────────
echo "[1/8] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ─── 2. Install Docker ───────────────────────────────────────────────────────
echo "[2/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed: $(docker --version)"
fi

# Install Docker Compose v2 plugin
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

# ─── 3. Install Nginx & Certbot ──────────────────────────────────────────────
echo "[3/8] Installing Nginx and Certbot..."
apt-get install -y nginx certbot python3-certbot-nginx

# ─── 4. Clone / Update Repo ──────────────────────────────────────────────────
echo "[4/8] Cloning/updating repository..."
if [ -d "$APP_DIR" ]; then
    echo "Repository exists — pulling latest..."
    git -C "$APP_DIR" pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# ─── 5. Set Up Environment Files ─────────────────────────────────────────────
echo "[5/8] Setting up environment files..."

# Generate a strong DB password if not already set
if [ ! -f "$APP_DIR/.db_password" ]; then
    DB_PASSWORD=$(openssl rand -hex 24)
    echo "$DB_PASSWORD" > "$APP_DIR/.db_password"
    chmod 600 "$APP_DIR/.db_password"
    echo "Generated DB password saved to $APP_DIR/.db_password"
fi
DB_PASSWORD=$(cat "$APP_DIR/.db_password")

# Create .env file for docker-compose (DB_PASSWORD variable)
cat > "$APP_DIR/.env" <<EOF
DB_PASSWORD=$DB_PASSWORD
EOF

# Check if backend prod env exists; if not, create from template
if [ ! -f "$APP_DIR/backend/.env.prod" ]; then
    echo "⚠️  WARNING: backend/.env.prod not found, creating from template."
    echo "   You MUST fill in SECRET_KEY, OPENAI_API_KEY, GOOGLE_* etc."
    cp "$APP_DIR/backend/.env.prod" "$APP_DIR/backend/.env.prod.bak" 2>/dev/null || true
fi

# Replace CHANGE_ME_DB_PASSWORD in backend/.env.prod
sed -i "s/CHANGE_ME_DB_PASSWORD/$DB_PASSWORD/g" "$APP_DIR/backend/.env.prod"

# Generate SECRET_KEY if still set to placeholder
if grep -q "CHANGE_ME_use_openssl_rand_hex_32" "$APP_DIR/backend/.env.prod"; then
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/CHANGE_ME_use_openssl_rand_hex_32/$SECRET_KEY/g" "$APP_DIR/backend/.env.prod"
    echo "Generated SECRET_KEY and saved to backend/.env.prod"
fi

# ─── 6. Configure Nginx ──────────────────────────────────────────────────────
echo "[6/8] Configuring Nginx..."

# Copy our nginx config
cp "$APP_DIR/infra/nginx/arosai.in.conf" /etc/nginx/sites-available/arosai.in
ln -sf /etc/nginx/sites-available/arosai.in /etc/nginx/sites-enabled/arosai.in

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

# Create certbot webroot
mkdir -p /var/www/certbot

nginx -t && systemctl reload nginx
echo "Nginx configured and reloaded."

# ─── 7. Obtain SSL Certificate ───────────────────────────────────────────────
echo "[7/8] Obtaining SSL certificate from Let's Encrypt..."

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    certbot --nginx \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        --redirect
    echo "SSL certificate obtained successfully!"
else
    echo "SSL certificate already exists for $DOMAIN."
    certbot renew --dry-run
fi

# Set up auto-renewal cron
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | sort -u | crontab -
echo "Auto-renewal cron job configured."

# ─── 8. Start Docker Services ────────────────────────────────────────────────
echo "[8/8] Building and starting Docker services..."
cd "$APP_DIR"

docker compose -f docker-compose.prod.yml pull --ignore-buildable
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "========================================"
echo "  ✅ Deployment Complete!"
echo "========================================"
echo ""
echo "  🌐 Frontend:  https://$DOMAIN"
echo "  📡 API Docs:  https://$DOMAIN/api/v1/docs"
echo ""
echo "  Check service status:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml ps"
echo ""
echo "  View logs:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml logs -f"
echo ""
echo "⚠️  IMPORTANT: If you haven't filled in API keys yet:"
echo "   Edit $APP_DIR/backend/.env.prod and run:"
echo "   docker compose -f $APP_DIR/docker-compose.prod.yml up -d backend"
echo ""
