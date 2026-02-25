#!/usr/bin/env bash
# Generates a self-signed TLS certificate for local development.
# For production, replace these files with certs from Let's Encrypt or your CA.
set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERT_DIR/server.key" \
  -out    "$CERT_DIR/server.crt" \
  -subj   "/CN=localhost"

echo "Self-signed certificate generated in $CERT_DIR"
echo "WARNING: This is for development only. Use a real CA cert in production."
