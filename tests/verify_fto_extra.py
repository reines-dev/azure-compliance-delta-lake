import requests

BASE_URL = "https://1plkktk2ak.execute-api.us-east-1.amazonaws.com/prod/check/"
API_KEY = "yKEM6Phs6rW5Pb9j04Sl1AayX5KsL5w9Zqb85X25"
HEADERS = {"x-api-key": API_KEY}

def test_fto():
    # Caso 1: Hit directo (ISIS)
    resp_hit = requests.get(BASE_URL, params={"name": "ISIS", "threshold": 90})
    data_hit = resp_hit.json()
    
    # Caso 2: Miss total
    resp_miss = requests.get(BASE_URL, params={"name": "REINES COFFEE SHOP", "threshold": 70})
    data_miss = resp_miss.json()
    
    print(f"FTO HIT (ISIS)   | Result: {data_hit.get('match_found')} | Top Match: {data_hit['results'][0]['nombre_original'] if data_hit.get('results') else 'N/A'}")
    print(f"FTO MISS (CLEAN) | Result: {data_miss.get('match_found')}")

if __name__ == "__main__":
    test_fto()
