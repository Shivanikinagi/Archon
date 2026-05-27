#!/bin/bash
# startup.sh - Quick startup script for Deep Research Agent

set -e

echo "🚀 Deep Research Agent Startup Script"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Ollama is available
echo "1️⃣  Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}✗ Ollama not found${NC}"
    echo "Please install Ollama from https://ollama.ai"
    exit 1
fi
echo -e "${GREEN}✓ Ollama found${NC}"

# Check if Ollama service is running
echo ""
echo "2️⃣  Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama service running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama service not running${NC}"
    echo "Start Ollama with: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment if needed
echo ""
echo "3️⃣  Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo ""
echo "4️⃣  Installing dependencies..."
pip install -q -e ".[dev]"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup configuration
echo ""
echo "5️⃣  Checking configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env with your configuration${NC}"
    echo "Key settings:"
    echo "  OLLAMA_ENABLED=true"
    echo "  OLLAMA_BASE_URL=http://localhost:11434"
    echo "  OLLAMA_MODEL=mistral"
else
    echo -e "${GREEN}✓ .env exists${NC}"
fi

# Pull Ollama models
echo ""
echo "6️⃣  Checking Ollama models..."
if ollama list | grep -q "mistral"; then
    echo -e "${GREEN}✓ Mistral model available${NC}"
else
    echo -e "${YELLOW}⚠ Mistral model not found${NC}"
    read -p "Pull Mistral model? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Pulling Mistral (this may take a few minutes)..."
        ollama pull mistral
    fi
fi

if ollama list | grep -q "nomic-embed"; then
    echo -e "${GREEN}✓ Nomic Embed model available${NC}"
else
    echo -e "${YELLOW}⚠ Nomic Embed model not found${NC}"
    read -p "Pull Nomic Embed model? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Pulling Nomic Embed (this may take a few minutes)..."
        ollama pull nomic-embed-text
    fi
fi

# Test setup
echo ""
echo "7️⃣  Testing setup..."
python -m src.cli ollama-status > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Setup test passed${NC}"
else
    echo -e "${RED}✗ Setup test failed${NC}"
    exit 1
fi

echo ""
echo "===================================="
echo -e "${GREEN}✓ Setup complete!${NC}"
echo "===================================="
echo ""
echo "Next steps:"
echo "  1. Research:  python -m src.cli research \"Your query\""
echo "  2. API:       python -m src.cli api-run"
echo "  3. Examples:  python examples/ollama_usage.py"
echo ""
echo "Documentation: https://github.com/your-org/deep-research-agent"
echo ""
