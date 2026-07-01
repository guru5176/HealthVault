"""Quick connectivity check for MongoDB Atlas + Ollama/DeepSeek."""

import os, sys
from dotenv import load_dotenv

load_dotenv()

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def check_mongo():
    print("=" * 50)
    print("  MongoDB Atlas Connection Test")
    print("=" * 50)
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "health_wallet")

    if not uri:
        print("[FAIL] MONGODB_URI not set in .env")
        return False

    print(f"  URI    : {uri[:30]}...{uri[-30:]}")
    print(f"  DB     : {db_name}")

    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        print("  Ping   : OK")

        db = client[db_name]
        cols = db.list_collection_names()
        print(f"  Collections: {cols if cols else '(none yet - empty DB)'}")
        client.close()
        print("\n  [PASS] MongoDB connection SUCCESSFUL\n")
        return True
    except Exception as e:
        print(f"\n  [FAIL] MongoDB connection FAILED: {e}\n")
        return False


def check_ollama():
    print("=" * 50)
    print("  Ollama / DeepSeek Connection Test")
    print("=" * 50)
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")
    print(f"  URL    : {base_url}")
    print(f"  Model  : {model}")

    try:
        import urllib.request, json
        # Check if Ollama is running
        req = urllib.request.Request(f"{base_url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            print(f"  Available models: {models}")

            if any(model in m for m in models):
                print(f"  [OK] Model '{model}' is available")
            else:
                print(f"  [WARN] Model '{model}' not found in list (may need: ollama pull {model})")

        # Quick generation test
        print("\n  Testing inference (short prompt)...")
        payload = json.dumps({
            "model": model,
            "prompt": "Say 'hello' in one word.",
            "stream": False,
            "options": {"num_predict": 20}
        }).encode()
        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            response_text = result.get("response", "").strip()[:100]
            print(f"  Response: {response_text}")
            print("\n  [PASS] Ollama/DeepSeek inference SUCCESSFUL\n")
            return True
    except Exception as e:
        print(f"\n  [FAIL] Ollama connection FAILED: {e}\n")
        return False


if __name__ == "__main__":
    mongo_ok = check_mongo()
    ollama_ok = check_ollama()

    print("=" * 50)
    print("  SUMMARY")
    print("=" * 50)
    print(f"  MongoDB  : {'PASS' if mongo_ok else 'FAIL'}")
    print(f"  Ollama   : {'PASS' if ollama_ok else 'FAIL'}")
    print("=" * 50)
    sys.exit(0 if (mongo_ok and ollama_ok) else 1)
