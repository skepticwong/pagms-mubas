import urllib.request
import urllib.error

try:
    # Need to send cookies if the route requires session
    # We will try without cookies first. If it 401s, we know the endpoint is up.
    req = urllib.request.Request("http://localhost:5000/api/effort/status/15")
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Exception: {e}")
