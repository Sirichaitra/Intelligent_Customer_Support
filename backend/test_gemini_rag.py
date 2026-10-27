
import os
import socket
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

HOSTNAME = "generativelanguage.googleapis.com"
TIMEOUT_MS = 30000


# --------------------------------------------------
# Main test
# --------------------------------------------------

def main():
    print("\n========== GEMINI CONNECTION TEST ==========\n")

    # Test 1: Environment configuration
    if not ENV_FILE.exists():
        print(f"[FAIL] .env file not found: {ENV_FILE}")
        return 1

    if not API_KEY:
        print("[FAIL] GOOGLE_API_KEY is missing from backend/.env")
        print("Add GOOGLE_API_KEY=your_api_key to your .env file.")
        return 1

    if not MODEL:
        print("[FAIL] GEMINI_MODEL is empty.")
        return 1

    print("[OK] .env file found.")
    print("[OK] GOOGLE_API_KEY is configured.")
    print(f"[INFO] Model configured: {MODEL}")

    # Test 2: DNS resolution
    try:
        ip_address = socket.gethostbyname(HOSTNAME)
        print(f"[OK] DNS resolution successful: {HOSTNAME} -> {ip_address}")
    except socket.gaierror as exc:
        print(f"[FAIL] DNS resolution failed: {exc}")
        print("Check your internet connection or DNS settings.")
        return 1

    # Test 3: Actual API request
    client = None

    try:
        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                timeout=TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(
    attempts=5,
    initial_delay=1.0,
    max_delay=60.0,
    exp_base=2.0,
    jitter=1.0,
),
            ),
        )

        print("\n[INFO] Sending test request to Gemini...")
        print("[INFO] This test makes one API request.")

        response = client.models.generate_content(
            model=MODEL,
            contents="Reply with exactly: Gemini connection successful",
            config=types.GenerateContentConfig(
                max_output_tokens=30,
                temperature=0,
            ),
        )

        answer = (response.text or "").strip()

        if answer:
            print("\n[OK] Gemini API request succeeded!")
            print(f"[RESPONSE] {answer}")
            print("\n[RESULT] Gemini is responding successfully.")
            return 0

        print("\n[WARNING] Gemini returned an empty response.")
        print("Check the model configuration and try again later.")
        return 1

    except Exception as exc:
        error_text = str(exc)
        error_upper = error_text.upper()

        print("\n[FAIL] Gemini API request failed.")
        print(f"[ERROR TYPE] {type(exc).__name__}")

        if "503" in error_text or "UNAVAILABLE" in error_upper:
            print("[ERROR CATEGORY] TEMPORARY SERVER AVAILABILITY")
            print("Gemini reports that the model may be overloaded.")
            print("Wait a few minutes before trying again.")

        elif "429" in error_text or "RESOURCE_EXHAUSTED" in error_upper:
            print("[ERROR CATEGORY] QUOTA OR RATE LIMIT")
            print("Check your current model quota and retry information.")
            print("https://ai.google.dev/gemini-api/docs/rate-limits")

        elif "401" in error_text or "UNAUTHENTICATED" in error_upper:
            print("[ERROR CATEGORY] AUTHENTICATION")
            print("Verify that the API key is valid and correctly configured.")

        elif "403" in error_text or "PERMISSION_DENIED" in error_upper:
            print("[ERROR CATEGORY] PERMISSION")
            print("Check API key restrictions, API access, and project settings.")

        elif any(term in error_upper for term in (
            "TIMEOUT",
            "TIMED OUT",
            "CONNECTION",
            "NETWORK",
        )):
            print("[ERROR CATEGORY] NETWORK OR TIMEOUT")
            print("Check connectivity and try again when the network is stable.")

        else:
            print("[ERROR CATEGORY] OTHER API ERROR")

        # Show the error for diagnosis, but never print the API key.
        print(f"[ERROR DETAILS] {error_text}")
        return 1

    finally:
        if client is not None:
            client.close()

    # Normally unreachable; included for clarity.
    return 0


if __name__ == "__main__":
    sys.exit(main())
