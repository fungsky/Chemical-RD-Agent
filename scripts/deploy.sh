#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#    ChemAgent - Cross-Platform Deployment Script
#    Supports: Linux, macOS, Windows (Git Bash/WSL)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

MODE="${1:-docker}"

check_deps() {
    info "Checking dependencies..."
    if ! command -v docker &>/dev/null; then
        error "Docker not found. Install: https://docs.docker.com/engine/install/"
    fi
    docker compose version &>/dev/null || docker-compose version &>/dev/null || error "Docker Compose not found"
    info "Docker OK"
}

setup_env() {
    if [ ! -f ".env" ]; then
        cp .env.example .env
        warn "Created .env from .env.example - please edit with your settings"
    fi
}

start_docker() {
    info "Starting ChemAgent with Docker..."
    check_deps
    setup_env
    local profile=""
    [ "${2:-}" = "postgres" ] && profile="--profile postgres"
    [ "${2:-}" = "mysql" ] && profile="--profile mysql"
    [ "${2:-}" = "full" ] && profile="--profile full"
    docker compose up -d $profile
    sleep 5
    docker compose ps
    echo ""
    info "ChemAgent is starting!"
    echo "  UI:   http://localhost:8501"
    echo "  API:  http://localhost:8000/docs"
    echo "  Neo4j: http://localhost:7474"
    echo "  Login: admin / admin123"
}

start_local() {
    info "Starting in local dev mode..."
    local py="python3"
    command -v python3 &>/dev/null || py="python"
    if [ ! -d ".venv" ]; then
        $py -m venv .venv
    fi
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
    pip install -q -r requirements.txt
    $py -m uvicorn chem_agent.api.main:app --reload --host 0.0.0.0 --port 8000 &
    $py -m streamlit run chem_agent/ui/app.py --server.port 8501 &
    echo "UI: http://localhost:8501 | API: http://localhost:8000/docs"
    wait
}

case "$MODE" in
    docker|up|start) start_docker "$@" ;;
    local|dev)       start_local ;;
    stop|down)       docker compose down; info "Stopped" ;;
    logs)            docker compose logs -f --tail=100 ;;
    status|ps)       docker compose ps ;;
    *)
        echo "Usage: ./deploy.sh {docker|local|stop|logs|status} [profile]"
        echo "  docker   Start with Docker (default)"
        echo "  local    Start local dev mode"
        echo "  stop     Stop all services"
        echo "  logs     View logs"
        echo "  status   Show status"
        echo "Profiles: postgres | mysql | full"
        exit 1 ;;
esac