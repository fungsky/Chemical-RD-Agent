#!/usr/bin/env bash
# Stop all ChemAgent services
cd "$(dirname "$0")/.."
docker compose down 2>/dev/null
echo "All ChemAgent services stopped."