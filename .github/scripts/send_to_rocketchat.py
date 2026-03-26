#!/usr/bin/env python3
import os
import sys
import requests

WEBHOOK_URL = os.getenv("ROCKETCHAT_WEBHOOK")
SUMMARY_FILE = "pr_summary.md"

if not WEBHOOK_URL:
    print("Missing ROCKETCHAT_WEBHOOK")
    sys.exit(1)

if not os.path.exists(SUMMARY_FILE):
    print(f"{SUMMARY_FILE} not found")
    sys.exit(1)

with open(SUMMARY_FILE, "r") as f:
    message_text = f.read().strip()

if not message_text:
    print("Summary file is empty")
    sys.exit(0)

# Create payload
payload = {
    "text": message_text,
    "username": "PR Summary Bot",
    "icon_emoji": ":robot:"
}

try:
    response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    response.raise_for_status()
    print("Message sent to Rocket.Chat successfully.")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed to send: {e}")
    sys.exit(1)
