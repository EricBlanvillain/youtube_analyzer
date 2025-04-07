#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Clear Streamlit cache
echo "Clearing Streamlit cache..."
if [ -d "/Users/ericblanvillain/Library/Application Support/streamlit" ]; then
    rm -rf "/Users/ericblanvillain/Library/Application Support/streamlit"
    echo "Successfully cleared cache in /Users/ericblanvillain/Library/Application Support/streamlit"
elif [ -d "/Users/ericblanvillain/.streamlit" ]; then
    rm -rf "/Users/ericblanvillain/.streamlit"
    echo "Successfully cleared cache in /Users/ericblanvillain/.streamlit"
fi

# Run the application
echo "Running Streamlit multipage app with: src/Home.py"
python -m streamlit run src/Home.py --browser.gatherUsageStats=false

# Keep the terminal window open in case of errors
read -p "Press Enter to exit..."
