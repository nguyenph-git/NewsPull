import asyncio

from flask import Flask, render_template, request, jsonify

from newspull import db
from newspull.agents.feedback import FeedbackAgent
from newspull.agents.orchestrator import OrchestratorAgent


def create_app() -> Flask:
    app = Flask(__name__)
    db.init_db()

    @app.route("/")
    def index():
        articles = db.get_unread_articles(limit=30)
        return render_template("index.html", articles=articles)

    @app.route("/mark-read", methods=["POST"])
    def mark_read():
        ids = request.json.get("ids", [])
        db.mark_articles_read(ids)
        return jsonify({"ok": True})

    @app.route("/review", methods=["POST"])
    def review():
        text = request.json.get("review", "").strip()
        if not text:
            return jsonify({"success": False, "error": "empty review"}), 400
        try:
            agent = FeedbackAgent()
            success = asyncio.run(agent.process(text))
            return jsonify({"success": success})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/fetch", methods=["POST"])
    def fetch():
        try:
            agent = OrchestratorAgent()
            saved, errors = asyncio.run(agent.run())
            return jsonify({"saved": saved, "errors": errors})
        except Exception as e:
            return jsonify({"saved": 0, "errors": [str(e)]}), 500

    return app
