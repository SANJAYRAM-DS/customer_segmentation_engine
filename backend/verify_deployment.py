import requests
import sys
import time

BASE_URL = "http://127.0.0.1:8000/api"

def check(name, url):
    try:
        print(f"Checking {name} ({url})...", end=" ")
        resp = requests.get(url)
        if resp.status_code == 200:
            print("OK")
            # Try to parse JSON to be sure
            data = resp.json()
            # print(str(data)[:100])
            return True
        else:
            print(f"FAILED ({resp.status_code})")
            print(resp.text[:500])
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("Waiting for server to be ready...")
for i in range(5):
    if check("Health", "http://127.0.0.1:8000/health"):
        break
    time.sleep(2)
else:
    print("Server not responding after 10s. setup failed.")
    sys.exit(1)

success = True
success &= check("Overview", f"{BASE_URL}/overview/")
success &= check("Segments", f"{BASE_URL}/segments/")
success &= check("Risk", f"{BASE_URL}/risk/")
success &= check("Value", f"{BASE_URL}/value/")
success &= check("HealthRoutes", f"{BASE_URL}/health/")
success &= check("Customers", f"{BASE_URL}/customers/")
success &= check("Alerts", f"{BASE_URL}/alerts/")

if success:
    print("\nALL SYSTEMS GO. Backend is serving data correctly.")
else:
    print("\nSome endpoints failed.")
    sys.exit(1)
