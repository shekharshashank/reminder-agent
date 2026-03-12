import json
import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

from llm_client import BedrockAPIError, get_reminder_extraction
from notification import send_notification

app = Flask(__name__)

REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")

# Per-session conversation history (in-memory).
# Maps session_id -> list of {"role": "user"|"assistant", "content": str}
_conversations = {}
MAX_HISTORY_TURNS = 20


def load_reminders():
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2, default=str)


def _make_reminder(result):
    """Create a reminder dict from validated LLM output."""
    date_str = result["date"]
    time_str = result["time"]
    agenda = result["agenda"]

    final_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    if final_dt < datetime.now():
        final_dt += timedelta(days=1)

    return {
        "id": str(uuid.uuid4())[:8],
        "agenda": agenda,
        "date": final_dt.strftime("%Y-%m-%d"),
        "time": final_dt.strftime("%H:%M"),
        "created_at": datetime.now().isoformat(),
        "dismissed": False,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not user_message:
        return jsonify({"reply": "Please type a message.", "reminders": []}), 400

    # Get or initialize conversation history
    if session_id not in _conversations:
        _conversations[session_id] = []
    history = _conversations[session_id]

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Trim history to bound token usage
    if len(history) > MAX_HISTORY_TURNS:
        history = history[-MAX_HISTORY_TURNS:]
        _conversations[session_id] = history

    # Call the LLM via Bedrock
    try:
        result = get_reminder_extraction(history)
    except BedrockAPIError as e:
        app.logger.error(f"Bedrock API error: {e.status_code} {e.message}")
        history.pop()  # remove user message so they can retry
        if e.status_code == 429:
            return jsonify({
                "reply": "Too many requests right now. Please wait a moment and try again.",
                "reminders": [],
            }), 429
        return jsonify({
            "reply": f"Bedrock API error ({e.status_code}). Check server logs.",
            "reminders": [],
        }), 503
    except Exception as e:
        app.logger.error(f"Unexpected error calling LLM: {e}")
        history.pop()
        return jsonify({
            "reply": "Something went wrong. Please try again.",
            "reminders": [],
        }), 500

    reply = result.get("reply", "I had trouble understanding. Could you rephrase that?")

    # Append assistant reply to history for multi-turn context
    history.append({"role": "assistant", "content": reply})

    # If complete, create the reminder and clear conversation
    if result.get("complete") and result.get("agenda") and result.get("date") and result.get("time"):
        try:
            reminder = _make_reminder(result)
            all_reminders = load_reminders()
            all_reminders.append(reminder)
            save_reminders(all_reminders)
            _conversations.pop(session_id, None)
            return jsonify({"reply": reply, "reminders": [reminder]})
        except (ValueError, KeyError) as e:
            app.logger.error(f"Failed to create reminder from LLM output: {e}")
            return jsonify({
                "reply": "I understood your request but had trouble saving it. Could you try rephrasing?",
                "reminders": [],
            }), 500

    # Not complete — return the follow-up question
    return jsonify({"reply": reply, "reminders": []})


@app.route("/api/reminders", methods=["GET"])
def get_reminders():
    return jsonify(load_reminders())


@app.route("/api/reminders/<reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    reminders = load_reminders()
    reminders = [r for r in reminders if r["id"] != reminder_id]
    save_reminders(reminders)
    return jsonify({"status": "deleted"})


@app.route("/api/reminders/<reminder_id>/dismiss", methods=["POST"])
def dismiss_reminder(reminder_id):
    reminders = load_reminders()
    for r in reminders:
        if r["id"] == reminder_id:
            r["dismissed"] = True
    save_reminders(reminders)
    return jsonify({"status": "dismissed"})


@app.route("/api/notify", methods=["POST"])
def notify():
    data = request.get_json()
    title = data.get("title", "Reminder")
    message = data.get("message", "")
    if message:
        send_notification(title, message)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
