#!/usr/bin/env bash
# Post a YouTube livestream URL and tail SSE. Pass the URL as $1 — livestream
# URLs rotate, no stable default.
set -euo pipefail

HOST="${HOST:-http://localhost:8080}"
if [ "$#" -lt 1 ]; then
  echo "usage: $0 <youtube-livestream-url>" >&2
  exit 1
fi
URL="$1"

session=$(curl -fsS -X POST "${HOST}/api/sessions" \
  -H 'Content-Type: application/json' \
  -d "{\"youtube_url\": \"${URL}\", \"kind\": \"live\"}")

session_id=$(echo "$session" | python -c 'import json,sys; print(json.load(sys.stdin)["session_id"])')
echo "session: ${session_id}"
curl -N "${HOST}/api/sessions/${session_id}/stream"
