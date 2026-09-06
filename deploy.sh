#!/usr/bin/env bash
# Convenience wrapper - delegates to scripts/deploy.sh
exec "$(dirname "$0")/scripts/deploy.sh" "$@"