from datetime import date
from flask import Blueprint, request, jsonify, session
from backend.models import db, User, SearchHistory
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""

    if not username or not email or not phone or not password:
        return jsonify({"error": "Username, email, phone number, and password are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username is already taken."}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered."}), 409

    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone number is already registered."}), 409

    user = User(
        username=username,
        email=email,
        phone=phone
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id

    return jsonify({
        "message": "Account created successfully.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        }
    }), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Username, email, or phone number and password are required."}), 400

    user = (
        User.query.filter_by(username=identifier).first()
        or User.query.filter_by(email=identifier.lower()).first()
        or User.query.filter_by(phone=identifier).first()
    )

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid login details."}), 401

    session["user_id"] = user.id

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        }
    })


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully."})


@auth_bp.route("/api/me", methods=["GET"])
def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not logged in."}), 401

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone
        }
    })


@auth_bp.route("/api/history", methods=["GET"])
def search_history():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not logged in."}), 401

    searches = (
        SearchHistory.query
        .filter_by(user_id=user_id)
        .order_by(SearchHistory.created_at.desc())
        .all()
    )

    return jsonify({
        "searches": [
            {
                "id": search.id,
                "keyword": search.keyword,
                "platform": search.platform,
                "search_date": search.search_date.isoformat(),
                "created_at": search.created_at.isoformat(),
                "total_posts": search.total_posts,
                "total_likes": search.total_likes,
                "total_comments": search.total_comments,
                "total_shares": search.total_shares,
                "total_views": search.total_views,
                "total_engagement": search.total_engagement
            }
            for search in searches
        ]
    })