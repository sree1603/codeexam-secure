#!/usr/bin/env bash
echo "SECRET-$(date +%s)" > /tmp/canary_secret.txt
chmod 600 /tmp/canary_secret.txt
echo "canary created"
