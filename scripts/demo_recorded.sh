#!/usr/bin/env bash
# Post a known short recorded YouTube clip to a running local server and tail SSE.
set -euo pipefail

HOST="${HOST:-http://localhost:8080}"
URL="${1:-https://www.youtube.com/watch?v=jNQXAC9IVRw}"  # "Me at the zoo" — 19s

session=$(curl -fsS -X POST "${HOST}/api/sessions" \
  -H 'Content-Type: application/json' \
  -d "{\"youtube_url\": \"${URL}\"}")

session_id=$(echo "$session" | python -c 'import json,sys; print(json.load(sys.stdin)["session_id"])')
echo "session: ${session_id}"
echo "streaming SSE (Ctrl-C to stop)…"
curl -N "${HOST}/api/sessions/${session_id}/stream"
