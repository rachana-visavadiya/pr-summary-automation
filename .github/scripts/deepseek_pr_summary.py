#!/usr/bin/env python3
import os
import sys
import datetime
import requests
from github import Github, Auth

# ---------- CONFIGURATION ----------
BRANCH = "main"               # Branch to monitor in the target repo
LOOKBACK_DAYS = 7
# ----------------------------------

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TARGET_REPO = os.getenv("TARGET_REPO")

if not all([GITHUB_TOKEN, DEEPSEEK_API_KEY, TARGET_REPO]):
    print("Missing environment variables")
    sys.exit(1)

# GitHub API client using new auth style
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)
try:
    repo = g.get_repo(TARGET_REPO)
except Exception as e:
    print(f"Failed to access repo {TARGET_REPO}: {e}")
    sys.exit(1)

# Calculate date range (timezone‑aware)
since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=LOOKBACK_DAYS)
print(f"Fetching PRs merged to {BRANCH} since {since.isoformat()}")

# Get merged PRs
prs = repo.get_pulls(state='closed', base=BRANCH, sort='updated', direction='desc')
merged_prs = []

for pr in prs:
    if pr.merged and pr.merged_at and pr.merged_at > since:
        # Fetch changed files for this PR (first 10 to keep token count low)
        changed_files = [f.filename for f in pr.get_files()[:10]]
        merged_prs.append({
            'title': pr.title,
            'author': pr.user.login,
            'url': pr.html_url,
            'labels': [label.name for label in pr.labels],
            'description': (pr.body or '')[:300],
            'files': changed_files,
            'additions': pr.additions,
            'deletions': pr.deletions
        })

if not merged_prs:
    print("No new merged PRs.")
    with open("pr_summary.md", "w") as f:
        f.write("No PRs merged this week.")
    sys.exit(0)

# Limit to 15 PRs to avoid token overload
merged_prs = merged_prs[:15]

# Build a richer prompt that includes file changes
pr_text = ""
for pr in merged_prs:
    pr_text += f"- **{pr['title']}** by @{pr['author']}\n"
    pr_text += f"  URL: {pr['url']}\n"
    pr_text += f"  Labels: {', '.join(pr['labels']) if pr['labels'] else 'none'}\n"
    pr_text += f"  Changed files: {', '.join(pr['files']) if pr['files'] else 'none'}\n"
    pr_text += f"  Additions: {pr['additions']}, Deletions: {pr['deletions']}\n"
    if pr['description']:
        pr_text += f"  Description: {pr['description']}\n"
    pr_text += "\n"

prompt = f"""You are a technical writer. Summarize these merged pull requests for the team in a concise, friendly style.

Include:
- A short intro
- Group the PRs into categories (Features, Bug Fixes, Documentation, Other)
- For each PR, briefly describe what changed (both the feature/bug and the main code files affected)
- End with the total PR count

Here are the PRs:

{pr_text}

Output in Markdown, with clear sections and bullet points. Use line breaks appropriately.
"""

# Call DeepSeek API
headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "max_tokens": 2000      # increased to accommodate code details
}

try:
    resp = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    resp.raise_for_status()
    result = resp.json()
    summary = result["choices"][0]["message"]["content"]
except Exception as e:
    print(f"DeepSeek API error: {e}")
    summary = "⚠️ AI summary generation failed. Please check the logs."

# Save summary to a markdown file
with open("pr_summary.md", "w") as f:
    f.write(summary)

print("Summary saved to pr_summary.md")
