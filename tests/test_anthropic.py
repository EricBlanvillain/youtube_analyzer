#!/usr/bin/env python3
"""
A simple script to test Anthropic API key configuration.
This will help verify if your API key is valid and the Anthropic
library is installed correctly.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_anthropic_key():
    """Test the Anthropic API key configuration."""
    print("\n=== Anthropic API Key Test ===\n")

    # Check if the anthropic module is installed
    try:
        import anthropic
        print("✅ Anthropic library is installed")
    except ImportError:
        print("❌ Failed to import the anthropic library")
        print("    Try: pip install anthropic==0.3.11")
        return False

    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ No API key found in environment variables")
        print("    Make sure you have an ANTHROPIC_API_KEY in your .env file")
        return False

    # Check API key format
    if not api_key.startswith("sk-ant"):
        print("⚠️ API key does not have the expected format")
        print(f"    Current format: {api_key[:10]}...")
        print("    Valid Anthropic API keys should start with 'sk-ant-'")
    else:
        print(f"✅ API key format looks correct: {api_key[:10]}...")

    # Try to create a client
    try:
        # First try newer client
        print("\nTrying to initialize Anthropic client...")
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Successfully created Anthropic client!")

        # Determine API version
        if hasattr(client, 'messages'):
            print("   Using newer API version with messages")
        elif hasattr(client, 'completions'):
            print("   Using newer API version with completions")
        else:
            print("   Using unknown API version structure")

        return True
    except Exception as e:
        print(f"❌ Error creating Anthropic client: {e}")
        if "401" in str(e) or "authentication" in str(e).lower():
            print("\n⚠️ Authentication error detected!")
            print("    Your API key appears to be invalid or expired")
            print("    Please get a new key from https://console.anthropic.com/")

        # Try older client as fallback
        try:
            client = anthropic.Client(api_key=api_key)
            print("✅ Successfully created Anthropic client (older version)!")
            return True
        except Exception as older_e:
            print(f"❌ Error creating Anthropic client (older version): {older_e}")
            return False

    return True

if __name__ == "__main__":
    success = test_anthropic_key()
    if success:
        print("\n✅ Test completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)
