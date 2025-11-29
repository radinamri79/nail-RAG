#!/bin/bash

# ============================================================================
# Nail RAG Local Development - Quick Commands Script
# ============================================================================
# Usage: source nail-rag-dev-commands.sh
# Then use: start-nail-rag, stop-nail-rag, etc.
# ============================================================================

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backend directory
BACKEND_DIR="/Users/radinamri/startup-projects/nail-rag/nail-rag-master"
FRONTEND_DIR="/Users/radinamri/startup-projects/Missland/Missland/frontend"

# ============================================================================
# Backend Commands
# ============================================================================

start-nail-rag() {
    echo -e "${BLUE}🚀 Starting Nail RAG Backend Services...${NC}"
    cd "$BACKEND_DIR"
    docker-compose up -d
    echo -e "${GREEN}✅ Services starting (wait 30s for full initialization)${NC}"
    echo ""
    echo -e "${YELLOW}📊 Checking service status...${NC}"
    sleep 5
    docker-compose ps
}

stop-nail-rag() {
    echo -e "${BLUE}🛑 Stopping Nail RAG Services...${NC}"
    cd "$BACKEND_DIR"
    docker-compose stop
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart-nail-rag() {
    echo -e "${BLUE}🔄 Restarting Nail RAG Services...${NC}"
    cd "$BACKEND_DIR"
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
    sleep 5
    docker-compose ps
}

reset-nail-rag() {
    echo -e "${RED}⚠️  Resetting Nail RAG (removes all data)...${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$BACKEND_DIR"
        docker-compose down -v
        echo -e "${GREEN}✅ Services and data cleared${NC}"
    else
        echo "Cancelled"
    fi
}

logs-nail-rag() {
    echo -e "${BLUE}📜 Showing Nail RAG Logs...${NC}"
    cd "$BACKEND_DIR"
    docker-compose logs -f --tail=50
}

logs-api() {
    echo -e "${BLUE}📜 Showing FastAPI Logs...${NC}"
    cd "$BACKEND_DIR"
    docker-compose logs -f nail-rag-api --tail=50
}

logs-weaviate() {
    echo -e "${BLUE}📜 Showing Weaviate Logs...${NC}"
    cd "$BACKEND_DIR"
    docker-compose logs -f weaviate --tail=50
}

import-dataset() {
    echo -e "${BLUE}📥 Importing Nail Dataset...${NC}"
    cd "$BACKEND_DIR"
    
    # Check if backend is running
    if ! docker-compose ps nail-rag-api | grep -q "Up"; then
        echo -e "${RED}❌ Backend not running. Start with: start-nail-rag${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
    sleep 10
    
    docker-compose exec nail-rag-api python -m app.scripts.bulk_import
}

status-nail-rag() {
    echo -e "${BLUE}📊 Nail RAG Status...${NC}"
    cd "$BACKEND_DIR"
    docker-compose ps
    echo ""
    echo -e "${BLUE}🏥 Health Checks:${NC}"
    
    echo -n "FastAPI: "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UP${NC}"
    else
        echo -e "${RED}❌ DOWN${NC}"
    fi
    
    echo -n "Weaviate: "
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UP${NC}"
    else
        echo -e "${RED}❌ DOWN${NC}"
    fi
}

# ============================================================================
# Frontend Commands
# ============================================================================

start-frontend() {
    echo -e "${BLUE}🚀 Starting Frontend Development Server...${NC}"
    cd "$FRONTEND_DIR"
    npm run dev
}

build-frontend() {
    echo -e "${BLUE}🔨 Building Frontend...${NC}"
    cd "$FRONTEND_DIR"
    npm run build
    echo -e "${GREEN}✅ Frontend built${NC}"
}

# ============================================================================
# Testing Commands
# ============================================================================

test-api() {
    echo -e "${BLUE}🧪 Testing Backend API...${NC}"
    
    echo -n "1. Health check: "
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -n "2. Create conversation: "
    CONV_ID=$(curl -s -X POST http://localhost:8000/api/chat/conversation \
        -H "Content-Type: application/json" \
        -d '{}' | grep -o '"conversation_id":"[^"]*' | cut -d'"' -f4)
    if [ ! -z "$CONV_ID" ]; then
        echo -e "${GREEN}✅${NC} (ID: ${CONV_ID:0:8}...)"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -n "3. Send message: "
    if [ ! -z "$CONV_ID" ]; then
        RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat/message \
            -H "Content-Type: application/json" \
            -d "{\"conversation_id\":\"$CONV_ID\",\"message\":\"Hello\"}")
        if echo "$RESPONSE" | grep -q "answer"; then
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${RED}❌${NC}"
        fi
    else
        echo -e "${RED}❌${NC} (no conversation)"
    fi
}

# ============================================================================
# Utility Commands
# ============================================================================

open-docs() {
    echo -e "${BLUE}📖 Opening API Documentation...${NC}"
    open http://localhost:8000/docs
}

open-frontend() {
    echo -e "${BLUE}🌐 Opening Frontend...${NC}"
    open http://localhost:3000/chat
}

open-weaviate() {
    echo -e "${BLUE}🔍 Opening Weaviate Console...${NC}"
    open http://localhost:8080/console
}

nail-rag-help() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Nail RAG Local Development - Available Commands       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}📦 Backend Commands:${NC}"
    echo "  start-nail-rag          Start all backend services (Weaviate + FastAPI)"
    echo "  stop-nail-rag           Stop all backend services"
    echo "  restart-nail-rag        Restart all backend services"
    echo "  reset-nail-rag          Remove all services and data (DESTRUCTIVE)"
    echo "  status-nail-rag         Show status and health checks"
    echo "  logs-nail-rag           View all service logs"
    echo "  logs-api                View FastAPI logs only"
    echo "  logs-weaviate           View Weaviate logs only"
    echo "  import-dataset          Import nail dataset into Weaviate"
    echo ""
    echo -e "${YELLOW}🌐 Frontend Commands:${NC}"
    echo "  start-frontend          Start frontend dev server (port 3000)"
    echo "  build-frontend          Build frontend for production"
    echo ""
    echo -e "${YELLOW}🧪 Testing Commands:${NC}"
    echo "  test-api                Test backend API endpoints"
    echo ""
    echo -e "${YELLOW}🔗 Quick Links:${NC}"
    echo "  open-docs               Open Swagger API documentation"
    echo "  open-frontend           Open frontend in browser"
    echo "  open-weaviate           Open Weaviate console"
    echo ""
    echo -e "${YELLOW}📝 Example Development Workflow:${NC}"
    echo "  1. start-nail-rag              # Start backend"
    echo "  2. import-dataset              # Import data (one time)"
    echo "  3. status-nail-rag             # Verify everything is running"
    echo "  4. open-docs                   # View API docs"
    echo "  5. (in new terminal) start-frontend   # Start frontend dev server"
    echo "  6. open-frontend               # Open chat interface"
    echo ""
    echo -e "${YELLOW}💡 Useful Tips:${NC}"
    echo "  - Use 'logs-nail-rag' to debug backend issues"
    echo "  - Run 'test-api' to verify backend is working"
    echo "  - Frontend hot-reloads on file changes (no restart needed)"
    echo "  - Backend changes require: stop-nail-rag → restart-nail-rag"
    echo "  - Check .env file for OpenAI API key and CORS settings"
    echo ""
}

# Show help on first load
nail-rag-help
