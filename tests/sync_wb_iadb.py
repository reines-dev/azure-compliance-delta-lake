import requests

BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod"
SOURCES = ["worldbank", "iadb"]

def sync():
    for s in SOURCES:
        print(f"Sincronizando {s.upper()}...")
        try:
            r1 = requests.post(f"{BASE_URL}/etl/ingest/{s}").json()
            print(f"   Ingest: {r1}")
            r2 = requests.post(f"{BASE_URL}/etl/transform/{s}").json()
            print(f"   Transform: {r2}")
            r3 = requests.post(f"{BASE_URL}/etl/load/{s}").json()
            print(f"   Load: {r3}")
        except Exception as e:
            print(f"   Error: {e}")

    print("Refrescando cache...")
    requests.get(f"{BASE_URL}/check/", params={"name": "REFRESH", "refresh": "True"})
    print("Hecho.")

if __name__ == "__main__":
    sync()
