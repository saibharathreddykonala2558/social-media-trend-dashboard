import json
import os
from datetime import date, datetime
from flask import Blueprint, request, jsonify, session, send_file
import pandas as pd

from backend.models import db, User, SearchHistory
from backend.reddit_api import fetch_reddit_posts
from backend.youtube_api import fetch_youtube_videos
from backend.github_api import fetch_github_repositories
from backend.analysis import analyze_results

api_bp = Blueprint("api", __name__)

DATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@api_bp.route("/api/search", methods=["POST"])
def search():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in to search."}), 401

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}

    keyword = (data.get("keyword") or "").strip()
    platform = (data.get("platform") or "all").strip().lower()
    search_date_value = data.get("search_date") or date.today().isoformat()

    if not keyword:
        return jsonify({"error": "Please enter a keyword."}), 400

    try:
        search_date = datetime.strptime(search_date_value, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date. Use YYYY-MM-DD format."}), 400

    results = []

    try:
        if platform in ["all", "reddit"]:
            results.extend(fetch_reddit_posts(keyword))

        if platform in ["all", "youtube"]:
            results.extend(fetch_youtube_videos(keyword))

        if platform in ["all", "github"]:
            results.extend(fetch_github_repositories(keyword))

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not fetch live data. Check your internet connection or API keys."}), 502

    analysis = analyze_results(results, keyword)

    search_record = SearchHistory(
        user_id=user.id,
        keyword=keyword,
        platform=platform,
        search_date=search_date,
        total_posts=analysis["summary"]["total_posts"],
        total_likes=analysis["summary"]["total_likes"],
        total_comments=analysis["summary"]["total_comments"],
        total_shares=analysis["summary"]["total_shares"],
        total_views=analysis["summary"]["total_views"],
        total_engagement=analysis["summary"]["total_engagement"],
        results_json=json.dumps({
            "results": results,
            "analysis": analysis
        })
    )

    db.session.add(search_record)
    db.session.commit()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = "".join(
        character if character.isalnum() else "_"
        for character in keyword
    )[:50]

    csv_filename = f"{safe_keyword}_{timestamp}.csv"
    csv_path = os.path.join(DATA_FOLDER, csv_filename)

    if results:
        pd.DataFrame(results).to_csv(csv_path, index=False, encoding="utf-8-sig")

    return jsonify({
        "message": "Live data fetched successfully.",
        "search_id": search_record.id,
        "analysis": analysis,
        "results": results,
        "csv_file": csv_filename if results else None
    })


@api_bp.route("/api/history/<int:search_id>", methods=["GET"])
def previous_search(search_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in."}), 401

    search_record = SearchHistory.query.filter_by(
        id=search_id,
        user_id=user_id
    ).first()

    if not search_record:
        return jsonify({"error": "Search not found."}), 404

    saved_data = json.loads(search_record.results_json)

    return jsonify({
        "search": {
            "id": search_record.id,
            "keyword": search_record.keyword,
            "platform": search_record.platform,
            "search_date": search_record.search_date.isoformat(),
            "created_at": search_record.created_at.isoformat()
        },
        "analysis": saved_data.get("analysis", {}),
        "results": saved_data.get("results", [])
    })


@api_bp.route("/api/download/<int:search_id>", methods=["GET"])
def download_search_csv(search_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in."}), 401

    search_record = SearchHistory.query.filter_by(
        id=search_id,
        user_id=user_id
    ).first()

    if not search_record:
        return jsonify({"error": "Search not found."}), 404

    saved_data = json.loads(search_record.results_json)
    results = saved_data.get("results", [])

    if not results:
        return jsonify({"error": "No downloadable results for this search."}), 404

    timestamp = search_record.created_at.strftime("%Y%m%d_%H%M%S")
    safe_keyword = "".join(
        character if character.isalnum() else "_"
        for character in search_record.keyword
    )[:50]

    filename = f"{safe_keyword}_{timestamp}.csv"
    filepath = os.path.join(DATA_FOLDER, filename)

    pd.DataFrame(results).to_csv(filepath, index=False, encoding="utf-8-sig")

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv"
    )