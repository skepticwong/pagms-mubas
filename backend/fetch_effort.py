import urllib.request
try:
    req = urllib.request.Request("http://localhost:5000/api/effort/status/15")
    with urllib.request.urlopen(req) as response:
        with open('out_fetch.txt', 'w') as f:
            f.write("Success: " + response.read().decode('utf-8'))
except Exception as e:
    with open('out_fetch.txt', 'w') as f:
        f.write(f"Exception: {e}\n")
        if hasattr(e, 'read'):
            f.write(e.read().decode('utf-8'))
