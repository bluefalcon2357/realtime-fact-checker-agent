#!/usr/bin/env bash
# Documented gcloud commands for provisioning Pub/Sub topics + Firestore.
# Not auto-run. Source `.env` and run manually after auth.
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?GOOGLE_CLOUD_PROJECT not set}"

gcloud config set project "${GOOGLE_CLOUD_PROJECT}"

gcloud pubsub topics create fact-check-chunks   --quiet || true
gcloud pubsub topics create fact-check-verdicts --quiet || true

gcloud firestore databases create \
  --location="${VERTEX_LOCATION:-us-central1}" \
  --type=firestore-native --quiet || true

gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  --quiet
