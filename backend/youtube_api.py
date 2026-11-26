import os
import requests
from datetime import datetime, timezone

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_youtube_videos(keyword, limit=25):
    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YouTube API key is missing. Add YOUTUBE_API_KEY to backend/.env"
        )

    search_response = requests.get(
        SEARCH_URL,
        params={
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "date",
            "maxResults": limit,
            "key": YOUTUBE_API_KEY
        },
        timeout=30
    )

    search_response.raise_for_status()
    search_data = search_response.json()

    video_ids = [
        item["id"]["videoId"]
        for item in search_data.get("items", [])
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    videos_response = requests.get(
        VIDEOS_URL,
        params={
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY
        },
        timeout=30
    )

    videos_response.raise_for_status()
    videos_data = videos_response.json()

    videos = []

    for item in videos_data.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        published_at = snippet.get("publishedAt")
        video_date = (
            datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .date()
            .isoformat()
            if published_at else None
        )

        views = int(statistics.get("viewCount", 0) or 0)
        likes = int(statistics.get("likeCount", 0) or 0)
        comments = int(statistics.get("commentCount", 0) or 0)

        videos.append({
            "platform": "YouTube",
            "post_id": item.get("id"),
            "title": snippet.get("title", ""),
            "text": snippet.get("description", ""),
            "author": snippet.get("channelTitle", ""),
            "subreddit": "",
            "url": f"https://www.youtube.com/watch?v={item.get('id')}",
            "created_at": video_date,
            "likes": likes,
            "comments": comments,
            "shares": 0,
            "views": views,
            "engagement": likes + comments
        })

    return videos
