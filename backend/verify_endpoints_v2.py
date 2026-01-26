import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def check(name, url):
    print(f"Checking {name}...", end=" ", flush=True)
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            print("OK", flush=True)
            return True
        else:
            print(f"FAIL ({resp.status_code})", flush=True)
            print(resp.text[:200])
            return False
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        return False

endpoints = [
    ("Overview", f"{BASE_URL}/overview/"),
    ("Segments", f"{BASE_URL}/segments/"),
    ("Risk", f"{BASE_URL}/risk/"),
    ("Value", f"{BASE_URL}/value/"),
    ("Health", f"{BASE_URL}/health/"),
    ("Customers", f"{BASE_URL}/customers/"),
    ("Alerts", f"{BASE_URL}/alerts/"),
]

failed = []
print("Starting checks...", flush=True)
for name, url in endpoints:
    if not check(name, url):
        failed.append(name)

if failed:
    print(f"\nFailed: {failed}")
    sys.exit(1)
else:
    print("\nAll endpoints OK.")
