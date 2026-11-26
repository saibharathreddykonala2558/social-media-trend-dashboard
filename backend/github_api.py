import requests
from datetime import datetime, timezone

SEARCH_URL = "https://api.github.com/search/repositories"


def fetch_github_repositories(keyword, limit=25):
    response = requests.get(
        SEARCH_URL,
        params={
            "q": keyword,
            "sort": "updated",
            "order": "desc",
            "per_page": limit
        },
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SocialMediaTrendDashboard"
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    repositories = []

    for item in data.get("items", []):
        updated_at = item.get("updated_at")
        repo_date = (
            datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .date()
            .isoformat()
            if updated_at else None
        )

        stars = item.get("stargazers_count", 0) or 0
        forks = item.get("forks_count", 0) or 0
        watchers = item.get("watchers_count", 0) or 0

        repositories.append({
            "platform": "GitHub",
            "post_id": str(item.get("id", "")),
            "title": item.get("name", ""),
            "text": item.get("description") or "",
            "author": item.get("owner", {}).get("login", ""),
            "subreddit": "",
            "url": item.get("html_url", ""),
            "created_at": repo_date,
            "likes": stars,
            "comments": forks,
            "shares": 0,
            "views": watchers,
            "engagement": stars + forks + watchers
        })

    return repositories