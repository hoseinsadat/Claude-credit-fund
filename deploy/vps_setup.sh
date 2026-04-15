#!/bin/bash
# Run on VPS as ubuntu user (with sudo)
# Installs all packages from transferred files and sets up the project

set -e

PACKAGES_DIR="$HOME/vps_packages"
WHEELS_DIR="$HOME/vps_wheels"
PROJECT_DIR="$HOME/credit_fund"
VENV_DIR="$HOME/venv"

echo "=== Step 1: Install system packages from .deb files ==="
cd "$PACKAGES_DIR/debs"
# Install in the right order - dpkg handles most deps if we install all together
sudo dpkg -i *.deb 2>&1 || sudo apt-get install -f -y 2>&1 || true

echo "=== Step 2: Verify PostgreSQL ==="
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql --no-pager | head -5

echo "=== Step 3: Verify Redis ==="
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server --no-pager | head -5

echo "=== Step 4: Create Python venv ==="
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "=== Step 5: Bootstrap pip from local get-pip.py ==="
python3 "$PACKAGES_DIR/get-pip.py" --no-index --find-links="$WHEELS_DIR" 2>/dev/null || \
python3 "$PACKAGES_DIR/get-pip.py" 2>&1 | tail -3

echo "=== Step 6: Install Python packages from local wheels ==="
pip install --no-index --find-links="$WHEELS_DIR" \
  -r "$PROJECT_DIR/requirements/base.txt" \
  -r "$PROJECT_DIR/requirements/prod.txt" \
  2>&1 | tail -10

echo "=== Step 7: Setup PostgreSQL database ==="
sudo -u postgres psql -c "CREATE USER credit_user WITH PASSWORD 'credit_pass_2024';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE credit_fund OWNER credit_user;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE credit_fund TO credit_user;" 2>/dev/null || true

echo "=== Done! ==="
echo "Now run vps_deploy.sh to configure and start the Django app."
