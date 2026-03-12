import subprocess


def send_notification(title, message):
    """Send a native macOS notification with sound using osascript."""
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        timeout=5,
    )
