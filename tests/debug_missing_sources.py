import requests

BASE_URL = "https://1plkktk2ak.execute-api.us-east-1.amazonaws.com/prod"
API_KEY = "yKEM6Phs6rW5Pb9j04Sl1AayX5KsL5w9Zqb85X25"
HEADERS = {"x-api-key": API_KEY}
MISSING = ["worldbank", "ue", "dea", "interpol", "contraloria"]

def debug_missing():
    for s in MISSING:
        print(f"\n--- DEBUGGING: {s.upper()} ---")
        try:
            r1 = requests.post(f"{BASE_URL}/etl/ingest/{s}").json()
            print(f"Ingest: {r1}")
            r2 = requests.post(f"{BASE_URL}/etl/transform/{s}").json()
            print(f"Transform: {r2}")
            r3 = requests.post(f"{BASE_URL}/etl/load/{s}").json()
            print(f"Load: {r3}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_missing()
