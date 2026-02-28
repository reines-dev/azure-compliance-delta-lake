import requests

BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod/check/"

def test_fbi():
    # Caso 1: Hit Fuzzy (Nombre parcial del FBI)
    resp_hit = requests.get(BASE_URL, params={"name": "Artem Ochichenko", "threshold": 80})
    data_hit = resp_hit.json()
    
    # Caso 2: Miss total
    resp_miss = requests.get(BASE_URL, params={"name": "Zinedine Zidane", "threshold": 70})
    data_miss = resp_miss.json()
    
    print("--- RESULTADOS FBI ---")
    if data_hit.get("match_found"):
        res = data_hit["results"][0]
        print(f"✅ HIT POSITIVO: Encontrado '{res['nombre_original']}' con score {res['score']}%")
    else:
        print("❌ FALLO: No se encontró el hit esperado del FBI.")
        
    if not data_miss.get("match_found"):
        print(f"✅ MISS NEGATIVO: El nombre neutro no generó alertas.")
    else:
        print(f"⚠️ AVISO: El nombre neutro generó un hit inesperado ({data_miss['results'][0]['nombre_original']}).")

if __name__ == "__main__":
    test_fbi()
