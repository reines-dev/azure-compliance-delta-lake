import urllib3

http = urllib3.PoolManager()
headers = {'User-Agent': 'Mozilla/5.0'}

# Try the Datos Abiertos file format (Listado Completo)
test_urls = [
    "https://www.sat.gob.mx/cifras_sat/paginas/datos/vinculo.html?fileName=69B_Definitivos.zip",
    "http://omawww.sat.gob.mx/cifras_sat/Documents/69B_Definitivo.csv",
    "https://www.datos.gob.mx/busca/api/action/resource_show?id=2c71a54b-a9ef-4fe0-9d42-4b8ebf52dd5d",
    "https://datosabiertos.sat.gob.mx/recursos/69_B_Definitivo.csv",
]

for url in test_urls:
    try:
        r = http.request('GET', url, headers=headers, timeout=10.0)
        print(f"[{r.status}] {len(r.data)} bytes | {url[:90]}")
        if r.status == 200 and len(r.data) > 5000:
            print(f"  => Preview: {r.data[:150].decode('latin-1', errors='replace')}")
    except Exception as e:
        print(f"[ERR] {url[:70]} - {e}")
