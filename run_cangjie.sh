#!/usr/bin/env bash
# Cangjie AI launcher for WSL2 (Ollama on Windows)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "${OLLAMA_HOST:-}" ]; then
  if curl -sf --connect-timeout 1 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    export OLLAMA_HOST="http://127.0.0.1:11434"
  else
    GW=$(ip route show default 2>/dev/null | awk '{print $3}' | head -n1)
    if [ -n "$GW" ] && curl -sf --connect-timeout 1 "http://${GW}:11434/api/tags" >/dev/null 2>&1; then
      export OLLAMA_HOST="http://${GW}:11434"
    else
      echo "Cannot reach Ollama. Start Ollama on Windows, or set OLLAMA_HOST."
      exit 1
    fi
  fi
fi

exec python3 "$SCRIPT_DIR/cangjie_agent.py" --host "$OLLAMA_HOST" "$@"
