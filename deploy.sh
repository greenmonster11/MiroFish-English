#!/bin/bash
# MiroFish VPS Deployment Script
# Run this on your fresh Hostinger VPS:
#   curl -sSL https://raw.githubusercontent.com/greenmonster11/MiroFish-English/main/deploy.sh | bash

set -e

echo "========================================="
echo "  MiroFish English - VPS Deployment"
echo "========================================="

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/5] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "[1/5] Docker already installed"
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "[2/5] Installing Docker Compose..."
    apt-get update && apt-get install -y docker-compose-plugin
else
    echo "[2/5] Docker Compose already installed"
fi

# Clone repo
echo "[3/5] Cloning MiroFish..."
cd /opt
if [ -d "MiroFish-English" ]; then
    cd MiroFish-English
    git pull
else
    git clone https://github.com/greenmonster11/MiroFish-English.git
    cd MiroFish-English
fi

# Set up .env
if [ ! -f .env ]; then
    echo "[4/5] Setting up environment..."
    cp .env.example .env
    echo ""
    echo "========================================="
    echo "  Enter your API keys"
    echo "========================================="
    read -p "OpenAI API key (sk-...): " OPENAI_KEY
    read -p "Zep API key (z_...): " ZEP_KEY

    cat > .env << EOF
LLM_API_KEY=${OPENAI_KEY}
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
ZEP_API_KEY=${ZEP_KEY}
EOF
    echo "Keys saved to .env"
else
    echo "[4/5] .env already exists, keeping current keys"
fi

# Build and start
echo "[5/5] Building and starting MiroFish..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "========================================="
echo "  MiroFish is running!"
echo "========================================="
echo ""
echo "  Open in browser: http://$(curl -s ifconfig.me)"
echo ""
echo "  Useful commands:"
echo "    View logs:    docker logs -f mirofish"
echo "    Stop:         docker compose -f docker-compose.prod.yml down"
echo "    Restart:      docker compose -f docker-compose.prod.yml restart"
echo ""
