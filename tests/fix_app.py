import os
import sys
import warnings
import subprocess
import webbrowser
import time
import socket
from contextlib import closing

# Set environment variables to optimize Streamlit
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"

# Find an available port
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

# Get an available port
port = find_free_port()
print(f"Selected port: {port}")

# Suppress PyTorch warnings
def custom_showwarning(message, category, filename, lineno, file=None, line=None):
    if category == UserWarning and "torch.classes" in str(message):
        return  # Skip the warning
    if hasattr(warnings, '_original_showwarning'):
        warnings._original_showwarning(message, category, filename, lineno, file, line)

if not hasattr(warnings, '_original_showwarning'):
    warnings._original_showwarning = warnings.showwarning
    warnings.showwarning = custom_showwarning

# Get the app file from command args or use default
app_file = sys.argv[1] if len(sys.argv) > 1 else "app.py"
print(f"Running Streamlit app: {app_file}")

# Build the Streamlit command
streamlit_cmd = [
    sys.executable,
    "-m", "streamlit", "run",
    app_file,
    "--server.port", str(port),
    "--server.enableCORS=true",
    "--server.enableXsrfProtection=false",
    "--browser.gatherUsageStats=false",
    "--server.headless=true"
]

# Start the process
print("Starting Streamlit server...")
process = subprocess.Popen(
    streamlit_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True
)

# Wait for server to start
time.sleep(5)

# Open the app in the default browser
app_url = f"http://localhost:{port}"
print(f"Opening {app_url} in browser")
webbrowser.open(app_url)

print("Server running. Press Ctrl+C to stop.")
try:
    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())
        err = process.stderr.readline()
        if err and "torch" not in err and "warning" not in err.lower():
            print(f"ERROR: {err.strip()}")

        # Check if process has ended
        if process.poll() is not None:
            break

        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping server...")
    process.terminate()

print("Server stopped.")
