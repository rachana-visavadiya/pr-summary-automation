#!/usr/bin/env python3
import os
import sys
import json
import datetime
import requests
from github import Github

# ---------- CONFIGURATION ----------
BRANCH = "develop"               # Branch to monitor in the target repo
LOOKBACK_DAYS = 7
# ----------------------------------

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")      # This is the PAT we stored
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TARGET_REPO = os.getenv("TARGET_REPO")        # e.g., "owner/repo"

if not all([GITHUB_TOKEN, DEEPSEEK_API_KEY, TARGET_REPO]):
    print("Missing environment variables")
    sys.exit(1)

# GitHub API client – using the PAT
g = Github(GITHUB_TOKEN)
try:
    repo = g.get_repo(TARGET_REPO)
except Exception as e:
    print(f"Failed to access repo {TARGET_REPO}: {e}")
    sys.exit(1)

# Rest of the script stays exactly the same as before
# ... (the part that fetches merged PRs, calls DeepSeek, and writes pr_summary.md)
