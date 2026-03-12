import socket
import threading

import webview

from app import app


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_flask(port):
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def main():
    port = _find_free_port()

    # Start Flask in a background daemon thread
    server = threading.Thread(target=_run_flask, args=(port,), daemon=True)
    server.start()

    # Open native macOS window
    webview.create_window(
        "Reminder Agent",
        f"http://127.0.0.1:{port}",
        width=1100,
        height=720,
        min_size=(800, 500),
    )
    webview.start()


if __name__ == "__main__":
    main()
