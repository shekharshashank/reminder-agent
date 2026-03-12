# Reminder Agent

An AI-powered desktop reminder application for macOS. Set reminders using natural language through a conversational chat interface powered by Claude 3.5 Haiku via AWS Bedrock.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.0-lightgrey)
![Platform](https://img.shields.io/badge/Platform-macOS-black)

## Features

- **Natural Language Input** — Create reminders by typing conversational messages like _"Remind me to call the dentist at 3pm tomorrow"_
- **Multi-Turn Conversations** — If details are missing (date, time, or agenda), the AI asks follow-up questions
- **Relative Date/Time Support** — Understands phrases like "tomorrow", "next Friday", "in 2 hours", "noon", "evening"
- **Native macOS Notifications** — Sends system-level notifications with sound when reminders come due
- **In-App Audio Alerts** — Plays a 3-beep audio tone for due reminders within the app
- **Desktop App** — Runs as a native macOS window using `pywebview` (WebKit-based)
- **Browser Mode** — Can also run as a standard web app accessible at `http://127.0.0.1:5050`
- **Local Storage** — Reminders are persisted in a local `reminders.json` file
- **Dismiss & Delete** — Manage reminders directly from the sidebar panel

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Backend | Flask 3.1.0 |
| LLM | Claude 3.5 Haiku (AWS Bedrock) |
| Desktop Shell | pywebview (native macOS WebKit window) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Notifications | macOS `osascript` (AppleScript) |
| Storage | Local JSON file |

## Project Structure

```
reminder-agent/
├── app.py              # Flask application (routes, reminder CRUD, chat endpoint)
├── desktop.py          # Desktop launcher using pywebview
├── llm_client.py       # AWS Bedrock / Claude API client with tool-use extraction
├── notification.py     # macOS native notification sender
├── requirements.txt    # Python dependencies
├── reminders.json      # Persistent reminder storage
├── prompts/
│   └── skill.md        # System prompt template for the LLM
└── templates/
    └── index.html      # Single-page web UI (chat + reminders panel)
```

## Prerequisites

- **macOS** (notifications use `osascript` which is macOS-specific)
- **Python 3.12+**
- **AWS Bedrock access** with Claude 3.5 Haiku model enabled

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd reminder-agent
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   ```bash
   export AWS_BEARER_TOKEN_BEDROCK="your-aws-bedrock-bearer-token"
   export AWS_REGION="us-west-2"  # optional, defaults to us-west-2
   ```

   Alternatively, create a `.env` file in the project root (git-ignored by default).

## Usage

### Desktop App (Recommended)

Launch the app as a native macOS window:

```bash
python desktop.py
```

This starts a local Flask server on a random free port and opens a 1100x720 native window.

### Browser Mode

Run as a standard web application:

```bash
python app.py
```

Then open `http://127.0.0.1:5050` in your browser.

<img width="1727" height="1106" alt="image" src="https://github.com/user-attachments/assets/44ae1915-9a24-4ca5-b77f-af2e2a7f787d" />


## How It Works

1. You type a message in the chat pane (e.g., _"Remind me to buy groceries at 6pm"_)
2. The message is sent to Claude 3.5 Haiku via AWS Bedrock
3. The LLM extracts structured reminder data (agenda, date, time) using tool-use
4. If any information is missing, it asks a follow-up question
5. Once complete, the reminder is saved to `reminders.json` and appears in the sidebar
6. The frontend polls for due reminders every 10 seconds
7. When a reminder is due, you get both an in-app audio alert and a native macOS notification

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the web UI |
| `POST` | `/api/chat` | Send a chat message; returns AI reply and optionally a created reminder |
| `GET` | `/api/reminders` | List all reminders |
| `DELETE` | `/api/reminders/<id>` | Delete a reminder |
| `POST` | `/api/reminders/<id>/dismiss` | Dismiss a reminder |
| `POST` | `/api/notify` | Trigger a native macOS notification |

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `AWS_BEARER_TOKEN_BEDROCK` | Bearer token for AWS Bedrock API authentication | _Required_ |
| `AWS_REGION` | AWS region for the Bedrock endpoint | `us-west-2` |

## License

This project is provided as-is for personal use.
