#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python src/run_multipage_app.py

# Keep the terminal window open in case of errors
read -p "Press Enter to exit..."
