import urllib3

http = urllib3.PoolManager()
headers = {'User-Agent': 'Mozilla/5.0'}

# Try datos.gob.mx CKAN API for SAT 69B
urls = [
    "https://datos.gob.mx/busca/api/action/resource_show?id=2c71a54b-a9ef-4fe0-9d42-4b8ebf52dd5d",
    "https://datos.gob.mx/busca/api/action/datastore_search?resource_id=2c71a54b-a9ef-4fe0-9d42-4b8ebf52dd5d&limit=5",
    "https://datos.gob.mx/busca/api/action/package_search?q=69-B+sat+definitivo",
]

for url in urls:
    try:
        r = http.request('GET', url, headers=headers, timeout=15.0)
        print(f"[{r.status}] {len(r.data)} bytes | {url[:80]}")
        if r.status == 200:
            print(f"  Preview: {r.data[:200].decode('utf-8', errors='replace')[:150]}")
    except Exception as e:
        print(f"[ERR] {url[:70]} - {e}")
