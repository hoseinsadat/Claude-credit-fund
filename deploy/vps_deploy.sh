#!/bin/bash
# Run on VPS as ubuntu user after vps_setup.sh has been run
# Deploys the Django project, configures nginx and systemd services

set -e

PROJECT_DIR="$HOME/credit_fund"
VENV_DIR="$HOME/venv"
DEPLOY_DIR="$HOME/deploy"

echo "=== Activating virtualenv ==="
source "$VENV_DIR/bin/activate"

echo "=== Setting up log directory ==="
sudo mkdir -p /var/log/credit_fund
sudo chown ubuntu:ubuntu /var/log/credit_fund

echo "=== Copying .env file ==="
cp "$DEPLOY_DIR/.env.prod" "$HOME/.env"

echo "=== Collecting static files ==="
cd "$PROJECT_DIR"
source "$HOME/.env"
export DJANGO_SETTINGS_MODULE
export DJANGO_SECRET_KEY
export DJANGO_ALLOWED_HOSTS
export POSTGRES_DB
export POSTGRES_USER
export POSTGRES_PASSWORD
export POSTGRES_HOST
export REDIS_URL
export CELERY_BROKER_URL
export CELERY_RESULT_BACKEND

python manage.py collectstatic --noinput 2>&1 | tail -3

echo "=== Running migrations ==="
python manage.py migrate 2>&1 | tail -10

echo "=== Creating default groups ==="
python manage.py create_default_groups 2>&1 || echo "Groups might already exist"

echo "=== Running seed data ==="
python -c "from apps.guarantees.seed_data import seed_all; seed_all()" 2>&1

echo "=== Installing systemd services ==="
sudo cp "$DEPLOY_DIR/gunicorn.service" /etc/systemd/system/
sudo cp "$DEPLOY_DIR/celery_worker.service" /etc/systemd/system/
sudo cp "$DEPLOY_DIR/celery_beat.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo "=== Configuring Nginx ==="
sudo cp "$DEPLOY_DIR/nginx_vps.conf" /etc/nginx/sites-available/credit_fund
sudo ln -sf /etc/nginx/sites-available/credit_fund /etc/nginx/sites-enabled/credit_fund
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "=== Starting services ==="
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl enable celery_worker
sudo systemctl start celery_worker
sudo systemctl enable celery_beat
sudo systemctl start celery_beat

echo ""
echo "=== Deployment complete! ==="
echo ""
echo "Service status:"
sudo systemctl status gunicorn --no-pager -l | head -8
echo ""
echo "Site should be available at: http://188.121.118.173/"
echo "Admin: http://188.121.118.173/admin/"
echo ""
echo "To create superuser:"
echo "  source ~/venv/bin/activate && source ~/.env && cd ~/credit_fund"
echo "  python manage.py createsuperuser"
