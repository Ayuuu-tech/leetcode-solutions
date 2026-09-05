"""
LeetCode → Notion + GitHub sync.
Repo path: scripts/leetcode_sync.py

Secrets to add at GitHub → repo → Settings → Secrets and variables → Actions:
  LEETCODE_SESSION  : the LEETCODE_SESSION cookie value (DevTools → Application → Cookies)
  NOTION_KEY        : secret_xxx from notion.so/my-integrations (same integration as Apps Script)

Notion database IDs are already correct below — no placeholders left.
Set LEETCODE_USERNAME to your handle before the first run.
"""

import os
import json
import datetime
import sys
import requests

LEETCODE_USERNAME = "ayuuu_13"          # <-- your LeetCode handle, e.g. "yashsharma4205"

LC_URL     = "https://leetcode.com/graphql"
SESSION    = os.environ["LEETCODE_SESSION"]
NOTION_KEY = os.environ["NOTION_KEY"]

# Data source IDs (the 2025-09-03 Notion API queries data sources, not databases).
CODING_DS = "2aad84f6-9d87-4abd-8a89-64f712c86f6e"   # Coding Log
DAILY_DS  = "f9bdc9ab-08c9-4d39-a7b6-19cc145ffea4"   # Daily Logs

LC_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"LEETCODE_SESSION={SESSION}",
}
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

RECENT_Q = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id title titleSlug timestamp lang
  }
}
"""

DETAIL_Q = """
query questionDetail($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    difficulty
    topicTags { name }
  }
}
"""

STATS_Q = """
query userProblemsSolved($username: String!) {
  matchedUser(username: $username) {
    submitStatsGlobal { acSubmissionNum { difficulty count } }
  }
}
"""

# Map LeetCode tag names onto the multi-select options that exist in Notion.
TAG_MAP = {
    "Array": "Arrays", "String": "Strings", "Hash Table": "Hashing",
    "Two Pointers": "Two Pointers", "Sliding Window": "Sliding Window",
    "Binary Search": "Binary Search", "Linked List": "Linked List",
    "Stack": "Stack", "Tree": "Trees", "Binary Tree": "Trees",
    "Graph": "Graphs", "Dynamic Programming": "DP", "Greedy": "Greedy",
    "Backtracking": "Backtracking", "Bit Manipulation": "Bit Manipulation",
    "Math": "Math",
}
LANG_MAP = {"python3": "Python", "python": "Python", "cpp": "C++",
            "java": "Java", "javascript": "JavaScript"}


def gql(query, variables):
    r = requests.post(LC_URL, headers=LC_HEADERS,
                      json={"query": query, "variables": variables}, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def notion(path, payload, method="post"):
    r = requests.request(method, f"https://api.notion.com/v1/{path}",
                         headers=NOTION_HEADERS, json=payload, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"Notion {r.status_code}: {r.text}")
    return r.json()


def ensure_daily_row(date_str):
    q = notion(f"data_sources/{DAILY_DS}/query",
               {"filter": {"property": "Date", "date": {"equals": date_str}},
                "page_size": 1})
    if q["results"]:
        return q["results"][0]["id"]
    return notion("pages", {
        "parent": {"type": "data_source_id", "data_source_id": DAILY_DS},
        "properties": {
            "Name":   {"title": [{"text": {"content": date_str}}]},
            "Date":   {"date": {"start": date_str}},
            "Status": {"select": {"name": "In Progress"}},
        }})["id"]


def already_logged(slug_title, date_str):
    q = notion(f"data_sources/{CODING_DS}/query", {
        "filter": {"and": [
            {"property": "Name", "title": {"equals": slug_title}},
            {"property": "Date", "date": {"equals": date_str}},
        ]}, "page_size": 1})
    return bool(q["results"])


def main():
    if LEETCODE_USERNAME == "CHANGE_ME":
        sys.exit("Set LEETCODE_USERNAME at the top of this file first.")

    today = datetime.date.today()
    recent = gql(RECENT_Q, {"username": LEETCODE_USERNAME, "limit": 20})["recentAcSubmissionList"]

    todays, seen = [], set()
    for s in recent:
        d = datetime.datetime.fromtimestamp(int(s["timestamp"])).date()
        if d == today and s["titleSlug"] not in seen:
            seen.add(s["titleSlug"])
            todays.append(s)

    if not todays:
        print("No accepted submissions today — nothing to commit or log.")
        return  # honest streak: no fake commit on an empty day

    daily_id = ensure_daily_row(str(today))

    for s in todays:
        if already_logged(s["title"], str(today)):
            print(f"skip (already logged): {s['title']}")
            continue

        detail = gql(DETAIL_Q, {"titleSlug": s["titleSlug"]})["question"]
        topics = [TAG_MAP[t["name"]] for t in detail.get("topicTags", [])
                  if t["name"] in TAG_MAP][:4]

        props = {
            "Name":        {"title": [{"text": {"content": s["title"]}}]},
            "Date":        {"date": {"start": str(today)}},
            "Platform":    {"select": {"name": "LeetCode"}},
            "Problem URL": {"url": f"https://leetcode.com/problems/{s['titleSlug']}/"},
            "Daily Log":   {"relation": [{"id": daily_id}]},
        }
        if detail.get("difficulty"):
            props["Difficulty"] = {"select": {"name": detail["difficulty"]}}
        if topics:
            props["Topic"] = {"multi_select": [{"name": t} for t in topics]}
        lang = LANG_MAP.get(s["lang"])
        if lang:
            props["Language"] = {"select": {"name": lang}}

        notion("pages", {"parent": {"type": "data_source_id", "data_source_id": CODING_DS}, "properties": props})
        print(f"logged: {s['title']}")

    # Write a stats file so the repo has a real commit on days you actually practised.
    stats = gql(STATS_Q, {"username": LEETCODE_USERNAME})["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
    os.makedirs("stats", exist_ok=True)
    with open("stats/progress.json", "w") as f:
        json.dump({"updated": str(today),
                   "totals": stats,
                   "solved_today": [s["title"] for s in todays]}, f, indent=2)

    print(f"Done — {len(todays)} problem(s) today.")


if __name__ == "__main__":
    main()
