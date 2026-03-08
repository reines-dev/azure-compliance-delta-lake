import urllib3, io

http = urllib3.PoolManager()
url = "http://omawww.sat.gob.mx/cifras_sat/Documents/ListadoGlobalDefinitivo.csv"
print(f"Testing: {url}")
try:
    response = http.request('GET', url, headers={'User-Agent':'Mozilla/5.0'}, timeout=30.0)
    print(f"HTTP Status: {response.status}")
    print(f"Content-Length: {len(response.data)} bytes")
    head = response.data[:400].decode('latin-1', errors='replace')
    print(f"Content preview: {head}")
except Exception as e:
    print(f"Error: {e}")
