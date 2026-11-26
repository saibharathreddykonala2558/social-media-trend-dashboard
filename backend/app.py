from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
import os


from models import db, User
from auth import auth_bp
from routes import api_bp


load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///social_media_dashboard.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

    mail = Mail(app)
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    CORS(
        app,
        supports_credentials=True,
        origins=[
            "https://saibharathreddykonala2558.github.io"
        ]
    )

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {
            "status": "success",
            "message": "Social Media Trend Dashboard backend is running"
        }

    @app.route("/api/forgot-password", methods=["POST"])
    def forgot_password():
        data = request.get_json()
        email = data.get("email", "").strip().lower()

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"message": "If this email exists, a reset link has been sent."}), 200

        token = serializer.dumps(user.email, salt="password-reset")

        reset_link = f"https://saibharathreddykonala2558.github.io/social-media-trend-dashboard/reset-password.html?token={token}"

        message = Message(
            subject="Reset your password",
            sender=app.config["MAIL_USERNAME"],
            recipients=[user.email],
            body=f"Click this link to reset your password:\n\n{reset_link}"
        )

        mail.send(message)

        return jsonify({"message": "If this email exists, a reset link has been sent."}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)