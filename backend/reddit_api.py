import os
import requests
from datetime import datetime, timedelta

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_SEARCH_URL = "https://oauth.reddit.com/search"


def get_reddit_token():
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None

    try:
        response = requests.post(
            REDDIT_TOKEN_URL,
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            data={
                "grant_type": "client_credentials"
            },
            headers={
                "User-Agent": "SocialMediaTrendDashboard/1.0"
            },
            timeout=15
        )

        response.raise_for_status()
        return response.json().get("access_token")

    except requests.exceptions.RequestException:
        return None


def fetch_reddit_posts(keyword, search_date, limit=25):
    token = get_reddit_token()

    if not token:
        return []

    try:
        response = requests.get(
            REDDIT_SEARCH_URL,
            headers={
                "Authorization": f"bearer {token}",
                "User-Agent": "SocialMediaTrendDashboard/1.0"
            },
            params={
                "q": keyword,
                "sort": "new",
                "limit": limit,
                "t": "day"
            },
            timeout=15
        )

        response.raise_for_status()
        posts = response.json().get("data", {}).get("children", [])

        results = []

        for item in posts:
            post = item.get("data", {})

            created_timestamp = post.get("created_utc", 0)
            created_date = datetime.fromtimestamp(created_timestamp).date()

            if str(created_date) != str(search_date):
                continue

            title = post.get("title", "")
            text = post.get("selftext", "") or ""

            results.append({
                "platform": "Reddit",
                "title": title,
                "content": text,
                "author": post.get("author", ""),
                "url": f"https://www.reddit.com{post.get('permalink', '')}",
                "likes": post.get("ups", 0),
                "comments": post.get("num_comments", 0),
                "shares": 0,
                "created_at": str(created_date)
            })

        return results

    except requests.exceptions.RequestException:
        return []