#!/usr/bin/env python3
"""
Test script for Anthropic API connectivity.
This script tests the connection to the Anthropic API and helps diagnose SSL/TLS issues.
"""
import os
import sys
import json
import time
import ssl
import requests
from dotenv import load_dotenv

# Try different versions of the anthropic library
try:
    import anthropic
    print(f"Anthropic library version: {anthropic.__version__}")
except ImportError:
    print("Anthropic library not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic==0.3.11"])
    import anthropic
    print(f"Installed anthropic version: {anthropic.__version__}")

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
    print("Please set it in your .env file.")
    sys.exit(1)

if not api_key.startswith("sk-ant"):
    print(f"WARNING: API key format doesn't match expected pattern (sk-ant...)")
    print(f"Current key format: {api_key[:8]}...")

# Function to test basic connection
def test_basic_connection():
    """Test basic connection to api.anthropic.com."""
    print("\n===== Testing basic connectivity =====")
    try:
        # Add required anthropic-version header
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

        response = requests.get("https://api.anthropic.com/v1/models",
                                headers=headers,
                                timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Connection successful!")
            models = response.json().get("models", [])
            print(f"Available models: {', '.join(model['id'] for model in models)}")
            return True
        elif response.status_code == 401:
            print("Authentication error. Your API key may be invalid.")
            return False
        else:
            print(f"Unexpected response: {response.text}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        print("\nThis indicates there is an issue with your SSL/TLS configuration.")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False

# Function to test with custom SSL context
def test_with_custom_ssl():
    """Test connection with a custom SSL context."""
    print("\n===== Testing with custom SSL context =====")

    # Create a custom SSL context specifically for LibreSSL
    class TlsAdapterLibreSSL(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
            ctx = ssl.create_default_context()
            # LibreSSL specific options
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED

            # Use compatibility mode
            ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

            import urllib3
            self.poolmanager = urllib3.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_context=ctx
            )

    # Create a session with a modified SSL adapter
    session = requests.Session()

    # Mount the adapter
    session.mount('https://', TlsAdapterLibreSSL())

    try:
        # Add required anthropic-version header
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

        response = session.get("https://api.anthropic.com/v1/models",
                               headers=headers,
                               timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Connection with custom SSL context successful!")
            return True
        else:
            print(f"Unexpected response with custom SSL context: {response.text}")
            return False
    except Exception as e:
        print(f"Error with custom SSL context: {e}")
        return False

# Function to test with anthropic client
def test_anthropic_client():
    """Test using the anthropic client library."""
    print("\n===== Testing Anthropic client library =====")

    # Detect client version
    if hasattr(anthropic, 'Anthropic'):
        print("Using newer Anthropic client...")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # Test messages API
            if hasattr(client, 'messages'):
                print("Testing messages API...")
                try:
                    response = client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Say hello"}]
                    )
                    print("Messages API test successful!")
                    print(f"Response: {response.content[0].text}")
                    return True
                except Exception as e:
                    print(f"Messages API test failed: {e}")

                    # Try completions API
                    try:
                        print("Testing completions API...")
                        response = client.completions.create(
                            model="claude-2.0",
                            prompt=f"{anthropic.HUMAN_PROMPT} Say hello {anthropic.AI_PROMPT}",
                            max_tokens_to_sample=10,
                        )
                        print("Completions API test successful!")
                        print(f"Response: {response.completion}")
                        return True
                    except Exception as comp_error:
                        print(f"Completions API test failed: {comp_error}")
                        return False
            else:
                print("Messages API not available, testing completions...")
                try:
                    response = client.completions.create(
                        model="claude-2.0",
                        prompt=f"{anthropic.HUMAN_PROMPT} Say hello {anthropic.AI_PROMPT}",
                        max_tokens_to_sample=10,
                    )
                    print("Completions API test successful!")
                    print(f"Response: {response.completion}")
                    return True
                except Exception as e:
                    print(f"Completions API test failed: {e}")
                    return False
        except Exception as e:
            print(f"Error initializing Anthropic client: {e}")
            return False
    else:
        print("Using older Client API...")
        try:
            client = anthropic.Client(api_key=api_key)
            response = client.completion(
                prompt=f"{anthropic.HUMAN_PROMPT} Say hello {anthropic.AI_PROMPT}",
                model="claude-2.0",
                max_tokens_to_sample=10,
            )
            print("Client API test successful!")
            print(f"Response: {response.completion}")
            return True
        except Exception as e:
            print(f"Client API test failed: {e}")
            return False

# Function to provide SSL/TLS troubleshooting info
def print_ssl_info():
    print("\n===== SSL/TLS Information =====")
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"Default verify paths: {ssl.get_default_verify_paths()}")

    # Check if cert file exists
    cafile = ssl.get_default_verify_paths().cafile
    if cafile and os.path.exists(cafile):
        print(f"Certificate file exists: {cafile}")
    else:
        print(f"Certificate file does not exist or is not accessible: {cafile}")

    # Verify we can create a context
    try:
        ctx = ssl.create_default_context()
        print("Successfully created SSL context")
    except Exception as e:
        print(f"Error creating SSL context: {e}")

def main():
    """Run the test suite."""
    print("=" * 50)
    print("Anthropic API Connection Test")
    print("=" * 50)

    # Print system information
    import platform
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")

    # Print SSL/TLS information
    print_ssl_info()

    # Test basic connection
    basic_success = test_basic_connection()

    # If basic connection fails, try with custom SSL
    if not basic_success:
        custom_success = test_with_custom_ssl()
    else:
        custom_success = True

    # Test anthropic client
    client_success = test_anthropic_client()

    # Print summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"Basic connection test: {'✅ Passed' if basic_success else '❌ Failed'}")
    print(f"Custom SSL connection: {'✅ Passed' if custom_success else '❌ Failed'}")
    print(f"Anthropic client test: {'✅ Passed' if client_success else '❌ Failed'}")

    if not (basic_success and client_success):
        print("\n===== Troubleshooting Recommendations =====")

        if not basic_success and not custom_success:
            print("1. Network connectivity issues detected:")
            print("   - Check your internet connection")
            print("   - Ensure your firewall is not blocking HTTPS connections")
            print("   - If using a VPN, try disabling it temporarily")

        if not basic_success and custom_success:
            print("1. SSL/TLS configuration issues detected:")
            print("   - Your SSL certificates may be outdated")
            print("   - Try updating your CA certificates package")
            print("   - On macOS: Check if root certificates are properly installed")

        print("\n2. API key issues to check:")
        print("   - Verify your API key in the .env file starts with 'sk-ant'")
        print("   - Ensure the API key is valid and not expired")
        print("   - Log into https://console.anthropic.com/ to check your API key status")

        print("\n3. Python environment issues:")
        print("   - Try upgrading the anthropic package: pip install --upgrade anthropic==0.3.11")
        print("   - Try upgrading requests: pip install --upgrade requests")
        print("   - Consider creating a fresh virtual environment")

        print("\n4. For SSL/TLS specific issues:")
        print("   - Try adding the following code to your application:")
        print("     ```")
        print("     import ssl")
        print("     import requests")
        print("     from requests.adapters import HTTPAdapter")
        print("     from requests.packages.urllib3.poolmanager import PoolManager")
        print("     ")
        print("     class TlsAdapter(HTTPAdapter):")
        print("         def init_poolmanager(self, connections, maxsize, block=False):")
        print("             ctx = ssl.create_default_context()")
        print("             ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT")
        print("             self.poolmanager = PoolManager(")
        print("                 num_pools=connections,")
        print("                 maxsize=maxsize,")
        print("                 block=block,")
        print("                 ssl_context=ctx")
        print("             )")
        print("     ")
        print("     session = requests.Session()")
        print("     session.mount('https://', TlsAdapter())")
        print("     ```")
    else:
        print("\n✅ All tests passed! Your Anthropic API connection is working correctly.")

if __name__ == "__main__":
    main()
