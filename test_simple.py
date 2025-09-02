#!/usr/bin/env python3
"""
Simple test to check if Python is working
"""
print("🐍 Python is working!")
print("Testing imports...")

try:
    import sys
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Python executable: {sys.executable}")
    print(f"✅ Python path: {sys.path[:3]}...")
except Exception as e:
    print(f"❌ Error with sys: {e}")

try:
    import os
    print(f"✅ Current directory: {os.getcwd()}")
except Exception as e:
    print(f"❌ Error with os: {e}")

try:
    import datetime
    print(f"✅ Current time: {datetime.datetime.now()}")
except Exception as e:
    print(f"❌ Error with datetime: {e}")

try:
    import json
    print("✅ JSON module available")
except Exception as e:
    print(f"❌ Error with json: {e}")

print("\nTesting FastAPI installation...")
try:
    import fastapi
    print(f"✅ FastAPI version: {fastapi.__version__}")
except ImportError:
    print("❌ FastAPI not installed")
except Exception as e:
    print(f"❌ Error with FastAPI: {e}")

try:
    import uvicorn
    print("✅ Uvicorn available")
except ImportError:
    print("❌ Uvicorn not installed")
except Exception as e:
    print(f"❌ Error with Uvicorn: {e}")

print("\n🎉 Test completed!")
