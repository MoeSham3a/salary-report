"""
Desktop launcher — Salary Report App
Opens the salary app in your default browser and keeps Flask running.
Close the console window to stop the server.
"""
import sys
import os
import socket
import threading
import webbrowser
import time

# Ensure we can find project modules when running as .exe
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


def find_free_port():
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def wait_for_server(port, timeout=10):
    """Wait until the Flask server is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.2)
    return False


def start_flask(port):
    """Start the Flask server."""
    import database as db
    from app import app

    db.init_db()

    # Suppress Flask request logs for cleaner console
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def main():
    # Fix console encoding on Windows
    if sys.platform == 'win32':
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except Exception:
            pass

    port = find_free_port()
    url = f'http://127.0.0.1:{port}'

    # Start Flask in background thread
    server = threading.Thread(target=start_flask, args=(port,), daemon=True)
    server.start()

    print()
    print('=' * 50)
    print('  Salary Report App')
    print('=' * 50)

    # Wait for server
    if wait_for_server(port):
        print(f'  Server running at {url}')
        print('  Opening browser...')
        print()
        print('  Press Ctrl+C or close this window to stop.')
        print('=' * 50)
        webbrowser.open(url)
    else:
        print('  ERROR: Server failed to start!')
        return

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n  Shutting down...')


if __name__ == '__main__':
    main()
