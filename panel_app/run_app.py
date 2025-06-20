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


def get_app_path():
    """Get the correct path to app.py whether running as script or frozen exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - files are in sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, 'app.py')


def main():
    # Set environment variables
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    # Find app.py path
    app_path = get_app_path()

    # Verify app.py exists
    if not os.path.exists(app_path):
        print(f"Error: app.py not found at {app_path}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Find free port
    port = find_free_port()

    # Open browser after delay
    Timer(3, open_browser, args=[port]).start()

    # Set up arguments for streamlit
    sys.argv = [
        "streamlit",
        "run",
        app_path,  # Use the correct path
        "--server.port", str(port),
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
        "--server.headless", "true",
        "--global.developmentMode", "false",
    ]

    # Run streamlit
    sys._argv = sys.argv
    stcli.main()


if __name__ == '__main__':
    main()