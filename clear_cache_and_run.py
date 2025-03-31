import os
import sys
import shutil
import warnings
import subprocess
import platform
import webbrowser
import time

# Define paths to Streamlit cache directories
def get_cache_dirs():
    cache_dirs = []

    # Get user home directory
    home_dir = os.path.expanduser("~")

    # Streamlit cache locations
    if platform.system() == "Darwin":  # macOS
        cache_dirs.append(os.path.join(home_dir, "Library", "Application Support", "streamlit"))
        cache_dirs.append(os.path.join(home_dir, ".streamlit"))
    elif platform.system() == "Linux":
        cache_dirs.append(os.path.join(home_dir, ".streamlit"))
        cache_dirs.append(os.path.join(home_dir, ".cache", "streamlit"))
    elif platform.system() == "Windows":
        cache_dirs.append(os.path.join(home_dir, "AppData", "Local", "streamlit"))
        cache_dirs.append(os.path.join(home_dir, ".streamlit"))

    return cache_dirs

# Clear Streamlit cache
def clear_streamlit_cache():
    print("Clearing Streamlit cache...")
    cache_dirs = get_cache_dirs()

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"Found cache directory: {cache_dir}")
            try:
                # Clear the cache directory
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    if item != "credentials.toml" and item != "config.toml":
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            print(f"Removed directory: {item_path}")
                        else:
                            os.remove(item_path)
                            print(f"Removed file: {item_path}")
                print(f"Successfully cleared cache in {cache_dir}")
            except Exception as e:
                print(f"Error clearing cache in {cache_dir}: {str(e)}")
        else:
            print(f"Cache directory not found: {cache_dir}")

# Suppress PyTorch warnings
def suppress_pytorch_warnings():
    original_showwarning = warnings.showwarning

    def custom_showwarning(message, category, filename, lineno, file=None, line=None):
        if category == UserWarning and "torch.classes" in str(message):
            return  # Skip the warning
        original_showwarning(message, category, filename, lineno, file, line)

    warnings.showwarning = custom_showwarning

    # Also set environment variables
    os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"

# Force specific environment variables for Streamlit
def set_streamlit_env_vars():
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

# Main function
if __name__ == "__main__":
    # Clear Streamlit cache
    clear_streamlit_cache()

    # Suppress PyTorch warnings
    suppress_pytorch_warnings()

    # Set Streamlit environment variables
    set_streamlit_env_vars()

    # Get the app file from command line or default to app.py
    app_file = sys.argv[1] if len(sys.argv) > 1 else "app.py"
    print(f"Running Streamlit app: {app_file}")

    # Create the command
    command = [
        sys.executable, "-m", "streamlit", "run", app_file,
        "--server.port", "8503",  # Use a different port
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]

    # Run Streamlit with the app
    print("Starting Streamlit...")
    process = subprocess.Popen(command)

    # Wait for the server to start
    time.sleep(5)

    # Open the browser manually
    print("Opening browser at http://localhost:8503")
    webbrowser.open("http://localhost:8503")

    # Wait for the process to complete
    process.wait()
