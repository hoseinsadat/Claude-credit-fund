#!/bin/bash
# Run this in WSL Ubuntu 24.04 as root
# Downloads all packages needed for VPS deployment

set -e

DOWNLOAD_DIR="/tmp/vps_packages"
WHEELS_DIR="/tmp/vps_wheels"
PROJECT_REQ_DIR="/mnt/c/Users/Hosein/Desktop/CClud/credit_fund/requirements"

echo "=== Creating download directories ==="
mkdir -p "$DOWNLOAD_DIR/debs"
mkdir -p "$WHEELS_DIR"

echo "=== Updating apt cache ==="
apt-get update -q

echo "=== Downloading system .deb packages ==="
# Download PostgreSQL 16, Redis, Nginx and all dependencies
apt-get install -y --download-only \
  -o Dir::Cache::Archives="$DOWNLOAD_DIR/debs" \
  postgresql-16 \
  postgresql-client-16 \
  redis-server \
  nginx \
  python3-pip \
  python3-venv \
  python3-dev \
  libpq-dev \
  build-essential \
  gcc \
  libpangocairo-1.0-0 \
  libpango-1.0-0 \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev \
  libssl-dev \
  libwebp7 \
  libopenjp2-7 \
  fontconfig \
  fonts-noto \
  fonts-noto-cjk \
  supervisor \
  curl \
  2>&1

echo "=== Copying downloaded .deb files ==="
cp /var/cache/apt/archives/*.deb "$DOWNLOAD_DIR/debs/" 2>/dev/null || true
ls "$DOWNLOAD_DIR/debs/" | wc -l
echo "packages downloaded"

echo "=== Installing pip in WSL for downloading wheels ==="
apt-get install -y python3-pip 2>&1 | tail -3

echo "=== Downloading Python wheels for Linux ==="
python3 -m pip download \
  --dest "$WHEELS_DIR" \
  --platform manylinux_2_17_x86_64 \
  --python-version 312 \
  --implementation cp \
  --abi cp312 \
  --only-binary :all: \
  -r "$PROJECT_REQ_DIR/base.txt" \
  -r "$PROJECT_REQ_DIR/prod.txt" \
  2>&1 || {
    echo "=== Binary download had issues, trying without platform restriction ==="
    python3 -m pip download \
      --dest "$WHEELS_DIR" \
      -r "$PROJECT_REQ_DIR/base.txt" \
      -r "$PROJECT_REQ_DIR/prod.txt" \
      2>&1
  }

echo "=== Wheel count: ==="
ls "$WHEELS_DIR" | wc -l

echo "=== Creating get-pip.py ==="
curl -sSL https://bootstrap.pypa.io/get-pip.py -o "$DOWNLOAD_DIR/get-pip.py"

echo "=== Done preparing packages ==="
echo "debs: $(ls $DOWNLOAD_DIR/debs/ | wc -l)"
echo "wheels: $(ls $WHEELS_DIR | wc -l)"
