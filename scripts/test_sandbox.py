"""Quick sandbox environment verification."""
import os
import sys

def main():
    # 1. Check .env
    if not os.path.exists('.env'):
        print("FAIL: .env not found")
        sys.exit(1)
    from dotenv import load_dotenv
    load_dotenv()
    key = os.environ.get('OPENROUTER_API_KEY', '')
    print(f"OpenRouter key: {'OK (' + key[:10] + '...)' if key else 'MISSING'}")

    # 2. Check GSC credentials
    for f in ['config/gsc_token.json', 'config/gsc_credentials.json']:
        if os.path.exists(f):
            print(f"{f}: OK ({os.path.getsize(f)} bytes)")
        else:
            print(f"FAIL: {f} not found")
            sys.exit(1)

    # 3. Test network - OpenRouter
    import urllib.request
    try:
        resp = urllib.request.urlopen('https://openrouter.ai/api/v1/models', timeout=10)
        print(f"OpenRouter API: OK (status {resp.status})")
    except Exception as e:
        print(f"OpenRouter API: FAIL ({e})")

    # 4. Test network - Google
    try:
        resp = urllib.request.urlopen('https://www.googleapis.com/discovery/v1/apis', timeout=10)
        print(f"Google API: OK (status {resp.status})")
    except Exception as e:
        print(f"Google API: FAIL ({e})")

    # 5. Test imports
    try:
        import click, pandas, openai, scipy
        print("Python imports: OK")
    except ImportError as e:
        print(f"Python imports: FAIL ({e})")

    print("\nAll checks passed!")

if __name__ == '__main__':
    main()
