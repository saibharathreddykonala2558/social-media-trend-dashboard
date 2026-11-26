import re
from collections import Counter
import pandas as pd


STOP_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "have", "has",
    "are", "was", "were", "will", "your", "you", "how", "what", "when",
    "why", "who", "which", "into", "about", "their", "them", "they",
    "more", "most", "than", "then", "there", "here", "over", "under",
    "after", "before", "because", "been", "being", "can", "could",
    "should", "would", "just", "also", "very", "not", "but", "all",
    "any", "one", "two", "new", "get", "use", "using", "make", "made"
}


def clean_text(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def extract_keywords(texts, limit=15):
    words = []

    for text in texts:
        text = clean_text(text).lower()
        found = re.findall(r"[a-zA-Z][a-zA-Z0-9+#]{2,}", text)

        for word in found:
            if word not in STOP_WORDS and len(word) > 2:
                words.append(word)

    return [
        {"keyword": word, "count": count}
        for word, count in Counter(words).most_common(limit)
    ]


def extract_hashtags(texts, limit=15):
    hashtags = []

    for text in texts:
        found = re.findall(r"#\w+", clean_text(text).lower())

        for hashtag in found:
            hashtags.append(hashtag)

    return [
        {"hashtag": hashtag, "count": count}
        for hashtag, count in Counter(hashtags).most_common(limit)
    ]


def analyze_results(results, keyword):
    if not results:
        return {
            "summary": {
                "keyword": keyword,
                "total_posts": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_shares": 0,
                "total_views": 0,
                "total_engagement": 0,
                "average_engagement": 0,
                "platforms": []
            },
            "top_posts": [],
            "daily_trends": [],
            "platform_trends": [],
            "top_keywords": [],
            "top_hashtags": []
        }

    dataframe = pd.DataFrame(results)

    numeric_columns = [
        "likes", "comments", "shares", "views", "engagement"
    ]

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column], errors="coerce"
        ).fillna(0).astype(int)

    dataframe["created_at"] = dataframe["created_at"].fillna("Unknown")

    platform_summary = (
        dataframe.groupby("platform")
        .agg(
            total_posts=("post_id", "count"),
            total_likes=("likes", "sum"),
            total_comments=("comments", "sum"),
            total_shares=("shares", "sum"),
            total_views=("views", "sum"),
            total_engagement=("engagement", "sum")
        )
        .reset_index()
        .to_dict(orient="records")
    )

    daily_trends = (
        dataframe.groupby("created_at")
        .agg(
            total_posts=("post_id", "count"),
            total_engagement=("engagement", "sum")
        )
        .reset_index()
        .sort_values("created_at")
        .to_dict(orient="records")
    )

    top_posts = (
        dataframe.sort_values("engagement", ascending=False)
        .head(10)
        .to_dict(orient="records")
    )

    texts = dataframe["title"].astype(str).tolist() + dataframe["text"].astype(str).tolist()

    summary = {
        "keyword": keyword,
        "total_posts": int(len(dataframe)),
        "total_likes": int(dataframe["likes"].sum()),
        "total_comments": int(dataframe["comments"].sum()),
        "total_shares": int(dataframe["shares"].sum()),
        "total_views": int(dataframe["views"].sum()),
        "total_engagement": int(dataframe["engagement"].sum()),
        "average_engagement": round(float(dataframe["engagement"].mean()), 2),
        "platforms": platform_summary
    }

    return {
        "summary": summary,
        "top_posts": top_posts,
        "daily_trends": daily_trends,
        "platform_trends": platform_summary,
        "top_keywords": extract_keywords(texts),
        "top_hashtags": extract_hashtags(texts)
    }
