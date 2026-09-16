#!/bin/bash
# NexAlert Demo Startup Script
# Starts backend and frontend services for presentation

set -e

echo "======================================"
echo "NEXALERT DEMO STARTUP"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend already running on http://localhost:8000"
else
    echo -e "${YELLOW}→${NC} Starting backend..."
    cd services/backend
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/nexalert-backend.log 2>&1 &
    BACKEND_PID=$!
    echo "  Backend PID: $BACKEND_PID"

    # Wait for backend to be ready
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Backend started successfully"
            break
        fi
        echo "  Waiting for backend... ($i/10)"
        sleep 1
    done
    cd ../..
fi

echo ""

# Check if authority dashboard is already running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Authority Dashboard already running on http://localhost:3000"
else
    echo -e "${YELLOW}→${NC} Starting Authority Dashboard..."
    cd apps/authority-dashboard
    npm run dev > /tmp/nexalert-dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo "  Dashboard PID: $DASHBOARD_PID"

    # Wait for dashboard to be ready
    sleep 3
    echo -e "${GREEN}✓${NC} Authority Dashboard starting..."
    cd ../..
fi

echo ""

# Check if citizen web is already running
if curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Citizen Emergency UI already running on http://localhost:3001"
else
    echo -e "${YELLOW}→${NC} Starting Citizen Emergency UI..."
    cd apps/citizen-web
    PORT=3001 npm run dev > /tmp/nexalert-citizen.log 2>&1 &
    CITIZEN_PID=$!
    echo "  Citizen PID: $CITIZEN_PID"

    # Wait for citizen app to be ready
    sleep 3
    echo -e "${GREEN}✓${NC} Citizen Emergency UI starting..."
    cd ../..
fi

echo ""
echo "======================================"
echo "NEXALERT DEMO READY"
echo "======================================"
echo ""
echo -e "${GREEN}Authority Dashboard:${NC}  http://localhost:3000"
echo -e "${GREEN}Citizen Emergency:${NC}    http://localhost:3001"
echo -e "${GREEN}Backend API:${NC}          http://localhost:8000"
echo -e "${GREEN}API Docs:${NC}             http://localhost:8000/docs"
echo ""
echo "======================================"
echo "DEMO CONTROLS"
echo "======================================"
echo ""
echo "Trigger fire scenario:"
echo "  curl -X POST http://localhost:8000/demo/trigger-fire"
echo ""
echo "Reset to normal:"
echo "  curl -X POST http://localhost:8000/demo/reset"
echo ""
echo "Check demo status:"
echo "  curl http://localhost:8000/demo/status"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
