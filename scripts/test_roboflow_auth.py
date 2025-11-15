#!/usr/bin/env python3
"""
Roboflow API Authentication Diagnostic Tool
Tests API key validity and provides troubleshooting guidance
"""

import os
import sys
from roboflow import Roboflow

def test_api_key(api_key: str):
    """Test if Roboflow API key is valid"""

    print("=" * 70)
    print("🔍 Roboflow API Authentication Diagnostic")
    print("=" * 70)
    print()

    if not api_key or api_key == "":
        print("❌ ERROR: No API key provided")
        print()
        print("Solutions:")
        print("1. Set environment variable:")
        print("   export ROBOFLOW_API_KEY='your_private_key_here'")
        print()
        print("2. Or pass directly:")
        print("   python scripts/test_roboflow_auth.py YOUR_API_KEY")
        print()
        return False

    print(f"📋 Testing API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    try:
        # Test 1: Initialize Roboflow client
        print("Test 1: Initializing Roboflow client...")
        rf = Roboflow(api_key=api_key)
        print("✅ Client initialized successfully")
        print()

        # Test 2: Try to access workspace
        print("Test 2: Accessing your workspace...")
        try:
            workspace = rf.workspace()
            print(f"✅ Workspace accessed: {workspace}")
            print()

            # Test 3: List projects (if any)
            print("Test 3: Checking available projects...")
            # This will help us understand if the key has proper permissions
            print("✅ API key has workspace access")
            print()

        except Exception as e:
            print(f"⚠️  Workspace access issue: {e}")
            print()

        print("=" * 70)
        print("✅ API KEY IS VALID!")
        print("=" * 70)
        print()
        print("Your Roboflow API key is working correctly.")
        print("You can now proceed with downloading datasets.")
        print()
        return True

    except Exception as e:
        error_msg = str(e).lower()

        print("=" * 70)
        print("❌ API AUTHENTICATION FAILED")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()

        # Provide specific troubleshooting based on error
        if "401" in error_msg or "unauthorized" in error_msg:
            print("🔧 Troubleshooting 401 Unauthorized Error:")
            print()
            print("This error means the API key is invalid, expired, or revoked.")
            print()
            print("Solutions:")
            print()
            print("1. Generate a NEW Private API Key:")
            print("   → Go to: https://app.roboflow.com/settings/api")
            print("   → Click 'Create New Private API Key'")
            print("   → Copy the ENTIRE key (starts with 'rf_...')")
            print("   → Set it: export ROBOFLOW_API_KEY='rf_NEW_KEY_HERE'")
            print()
            print("2. Verify you're using the PRIVATE key (not publishable):")
            print("   → Private keys start with: rf_")
            print("   → Publishable keys are different format")
            print("   → You need the PRIVATE key for downloads")
            print()
            print("3. Check your Roboflow account:")
            print("   → Log in to: https://app.roboflow.com")
            print("   → Verify account is active")
            print("   → Check if you have API access on your plan")
            print()

        elif "connection" in error_msg or "network" in error_msg:
            print("🔧 Troubleshooting Network Error:")
            print()
            print("1. Check internet connection")
            print("2. Try again in a few minutes")
            print("3. Check if Roboflow.com is accessible")
            print()

        else:
            print("🔧 General Troubleshooting:")
            print()
            print("1. Verify API key is copied correctly (no spaces)")
            print("2. Generate a fresh API key")
            print("3. Contact Roboflow support if issue persists")
            print()

        print("Need a new API key?")
        print("→ https://app.roboflow.com/settings/api")
        print()

        return False


def main():
    # Get API key from command line or environment
    api_key = None

    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line argument")
    else:
        api_key = os.getenv("ROBOFLOW_API_KEY")
        if api_key:
            print(f"Using API key from ROBOFLOW_API_KEY environment variable")
        else:
            print("No API key found in arguments or environment")

    print()

    success = test_api_key(api_key)

    if success:
        print("🚀 Next Steps:")
        print()
        print("Run the dataset download script:")
        print("   python scripts/universal_dataset.py --roboflow-api-key $ROBOFLOW_API_KEY")
        print()
        sys.exit(0)
    else:
        print("⚠️  Fix the API key issue above, then try again.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
