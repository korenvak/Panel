import os
import sys
import webbrowser
import socket
from threading import Timer
from streamlit.web import cli as stcli

def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        return s.getsockname()[1]

def open_browser(port):
    """Open the default browser after a short delay."""
    webbrowser.open(f'http://localhost:{port}')

def main():
    port = find_free_port()
    Timer(3, open_browser, args=[port]).start()
    sys.argv = [
        "streamlit",
        "run",
        os.path.join(os.path.dirname(__file__), "app.py"),
        "--server.port",
        str(port),
        "--server.address",
        "localhost",
        "--browser.gatherUsageStats",
        "false",
        "--server.headless",
        "true",
        "--server.runOnSave",
        "false",
    ]
    stcli.main()

if __name__ == '__main__':
    main()
