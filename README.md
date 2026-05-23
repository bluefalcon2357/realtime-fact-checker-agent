# Live Reality Fact-Check Overlay

Point a YouTube URL — recorded or livestreamed — at this app and watch claims get checked in real time. Floating overlay surfaces green / yellow / red verdicts on every factual claim within seconds of being spoken.

Built on **Google ADK** with **Gemini Flash** (`gemini-flash-latest`), running on Vertex AI + Cloud Run + Pub/Sub + Firestore.

## Architecture

```
YouTube URL ──► yt-dlp + ffmpeg ──► 5s audio chunks
                                          │
                                          ▼
                              RootOrchestrator (ADK)
                                          │
                ┌─────────────────────────┼─────────────────────────┐
                ▼                         ▼                         ▼
       TranscriberAgent          ClaimExtractorAgent           ContextAgent
       (Flash audio-in)        (structured JSON output)       (session.state)
                                          │
                                per extracted claim
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
                  SearchAgent                       TrustedSourceAgent
              (Flash + google_search)       (Flash + allowlist FunctionTool)
                        ▼                                   ▼
                        └────────────► VerdictAgent ◄───────┘
                                              │
                                              ▼
                                  SSE ──► Frontend overlay
                                          (synced to player.getCurrentTime())
```

## Quick start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
# Edit .env: set GOOGLE_CLOUD_PROJECT, run `gcloud auth application-default login`

# 3. Run
make dev

# 4. Open http://localhost:8080 and paste a YouTube URL
```

Set `STUB_LLM=true` in `.env` to bypass Gemini calls during offline development.

## Layout

```
backend/
  main.py              FastAPI app + SSE + static mount
  ingestion/           yt-dlp + ffmpeg chunkers (recorded + live HLS)
  agents/              ADK agent factories
  runtime/             Session manager, runner, dedupe, Firestore cache
  transport/           SSE, WebSocket, Pub/Sub shim
  tools/               Google Search wrapper + trusted-source FunctionTool
frontend/
  index.html           YouTube IFrame + overlay
  app.js               Player API + EventSource + RAF scheduler
infra/                 Cloud Run + Pub/Sub + Firestore config
scripts/               Demo helpers
tests/                 Pytest
```

## Demo

```bash
make demo-recorded   # posts a known short clip
make demo-live       # posts a known livestream URL
```

## Deploy

```bash
gcloud run deploy hackathon-io \
  --source . \
  --region $VERTEX_LOCATION \
  --concurrency 80 \
  --min-instances 1 \
  --set-env-vars LOCAL_MODE=false,GEMINI_MODEL=gemini-flash-latest
```
