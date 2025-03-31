import os
import sys
import warnings
import re

# Filter out the specific PyTorch warning
class TorchWarningFilter(warnings.WarningMessage):
    def __init__(self, message='', category=UserWarning, filename='', lineno=0, line=''):
        super().__init__(message, category, filename, lineno, line)

    def is_torch_path_warning(self):
        if not hasattr(self.message, 'args'):
            return False
        for arg in self.message.args:
            if isinstance(arg, str) and "Examining the path of torch.classes" in arg:
                return True
        return False

original_showwarning = warnings.showwarning

def custom_showwarning(message, category, filename, lineno, file=None, line=None):
    if category == UserWarning and "torch.classes" in str(message):
        return  # Skip the warning
    original_showwarning(message, category, filename, lineno, file, line)

warnings.showwarning = custom_showwarning

# Force streamlit to run in headless mode to avoid browser issues
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# Run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli

    # Get the app file from command line or default to app.py
    app_file = sys.argv[1] if len(sys.argv) > 1 else "app.py"

    # Build the Streamlit command arguments
    sys.argv = [
        "streamlit", "run",
        app_file,
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]

    print(f"Running Streamlit app: {app_file}")
    print("Access the app at http://localhost:8501")

    # Start Streamlit
    stcli.main()
