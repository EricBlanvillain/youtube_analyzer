#!/usr/bin/env python3
"""
Test script for Anthropic API call with TLS adapter fix.
"""
import os
import ssl
import time
import json
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set in .env file")
    exit(1)

# Try importing anthropic
try:
    import anthropic
    print(f"Using anthropic version: {anthropic.__version__}")
except ImportError:
    print("Installing anthropic package...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic==0.3.11"])
    import anthropic

# Create a TLS adapter that works with LibreSSL
class TlsAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        ctx = ssl.create_default_context()
        # Set verification mode explicitly
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        # Enable legacy server connect option
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

        import urllib3
        self.poolmanager = urllib3.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

def test_direct_api_call():
    """Test a direct API call using requests with our custom adapter."""
    print("\n===== Testing direct API call with custom TLS adapter =====")

    session = requests.Session()
    session.mount('https://', TlsAdapter())

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-2.0",
        "prompt": "\n\nHuman: Say hello\n\nAssistant:",
        "max_tokens_to_sample": 50
    }

    try:
        print("Making API request...")
        response = session.post(
            "https://api.anthropic.com/v1/complete",
            headers=headers,
            json=data,
            timeout=10
        )

        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("API call successful!")
            print(f"Response: {result.get('completion', '')}")
            return True
        else:
            print(f"API call failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error making API call: {e}")
        return False

def test_anthropic_client():
    """Test using the anthropic client with our custom TLS adapter."""
    print("\n===== Testing anthropic client with TLS patch =====")

    try:
        # Check which client version we have
        if hasattr(anthropic, "Anthropic"):
            print("Using newer Anthropic client...")
            client = anthropic.Anthropic(api_key=api_key)

            # Try to patch the client's session
            if hasattr(client, "_client"):
                session = getattr(client._client, "_session", None)
                if session:
                    session.mount('https://', TlsAdapter())
                    print("Successfully patched client session")

                # Update headers if needed
                if hasattr(client, "default_headers"):
                    client.default_headers["anthropic-version"] = "2023-06-01"
                    print("Updated client headers")

            # Try completions API
            print("Testing completions...")
            try:
                response = client.completions.create(
                    model="claude-2.0",
                    prompt=f"{anthropic.HUMAN_PROMPT} Say hello{anthropic.AI_PROMPT}",
                    max_tokens_to_sample=50
                )
                print("Completions API successful!")
                print(f"Response: {response.completion}")
                return True
            except Exception as e:
                print(f"Completions API error: {e}")

                # Try messages API if completions fails
                try:
                    print("Testing messages API...")
                    response = client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=50,
                        messages=[{"role": "user", "content": "Say hello"}]
                    )
                    print("Messages API successful!")
                    print(f"Response: {response.content[0].text}")
                    return True
                except Exception as e2:
                    print(f"Messages API error: {e2}")
                    return False
        else:
            # Using older client
            print("Using older Anthropic client...")
            client = anthropic.Client(api_key=api_key)

            # Add anthropic-version header if possible
            if hasattr(client, "headers"):
                client.headers["anthropic-version"] = "2023-06-01"
                print("Updated client headers")

            response = client.completion(
                prompt=f"{anthropic.HUMAN_PROMPT} Say hello {anthropic.AI_PROMPT}",
                model="claude-2.0",
                max_tokens_to_sample=50
            )
            print("API call successful!")
            print(f"Response: {response.completion}")
            return True
    except Exception as e:
        print(f"Error using anthropic client: {e}")
        return False

if __name__ == "__main__":
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"SSL verify paths: {ssl.get_default_verify_paths()}")

    # Test with direct API call first
    direct_success = test_direct_api_call()

    # Then test with client
    client_success = test_anthropic_client()

    print("\n===== Test Results =====")
    print(f"Direct API call: {'✅ Success' if direct_success else '❌ Failed'}")
    print(f"Anthropic client: {'✅ Success' if client_success else '❌ Failed'}")

    if direct_success or client_success:
        print("\n👍 At least one test passed! The SSL/TLS fix should work for the application.")
    else:
        print("\n❌ All tests failed. Please check your API key and network connection.")
