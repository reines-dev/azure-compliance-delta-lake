import requests

BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod/check/"

def test_contraloria():
    # Caso 1: Hit (Nombre común en listas de responsables fiscales)
    resp_hit = requests.get(BASE_URL, params={"name": "ALVARO", "threshold": 70})
    data_hit = resp_hit.json()
    
    # Caso 2: Miss
    resp_miss = requests.get(BASE_URL, params={"name": "USUARIO TOTALMENTE LIMPIO", "threshold": 70})
    data_miss = resp_miss.json()
    
    print(f"CONTRALORIA HIT  | Result: {data_hit.get('match_found')} | Top Match: {data_hit['results'][0]['nombre_original'] if data_hit.get('results') else 'N/A'}")
    print(f"CONTRALORIA MISS | Result: {data_miss.get('match_found')}")

if __name__ == "__main__":
    test_contraloria()
