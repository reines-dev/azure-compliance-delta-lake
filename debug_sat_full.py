import urllib3

http = urllib3.PoolManager()

# Test different possible full URLs
urls = [
    "http://omawww.sat.gob.mx/cifras_sat/Documents/69_B_Definitivo.csv",
    "http://omawww.sat.gob.mx/cifras_sat/Documents/Definitivos69_B.csv",
    "https://www.sat.gob.mx/cs/Satellite?blobcol=urldata&blobkey=id&blobtable=MungoBlobs&blobwhere=1461174558024&ssbinary=true",
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for url in urls:
    try:
        r = http.request('GET', url, headers=headers, timeout=10.0, redirect=True)
        print(f"[{r.status}] {len(r.data)} bytes | {url[:80]}")
        if r.status == 200 and len(r.data) > 5000:
            print(f"  => FULL FILE! First 200 chars: {r.data[:200].decode('latin-1', errors='replace')}")
    except Exception as e:
        print(f"[ERR] {url[:60]} - {e}")
