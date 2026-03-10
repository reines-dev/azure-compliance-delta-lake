import requests
import json

BASE_URL = "https://1plkktk2ak.execute-api.us-east-1.amazonaws.com/prod/check/"
API_KEY = "yKEM6Phs6rW5Pb9j04Sl1AayX5KsL5w9Zqb85X25"
HEADERS = {"x-api-key": API_KEY}

test_cases = [
    # (Nombre, Hit Esperado, Descripcion)
    ("Al-Qaida", True, "ONU - Hit"),
    ("Usuario Limpio ONU", False, "ONU - Miss"),
    ("Hamas", True, "FTO - Hit"),
    ("Cruz Roja Internacional", False, "FTO - Miss"),
    ("Patel", True, "FBI - Hit"),
    ("Elon Musk FBI", False, "FBI - Miss"),
    ("Hizballah", True, "FTO - Hit"),
    ("ComplianceGuard Test Clear", False, "General - Miss")
]

def run_tests():
    print(f"{'CASO':<30} | {'EXPECTED':<10} | {'ACTUAL':<10} | {'STATUS'}")
    print("-" * 70)
    
    for name, expected, desc in test_cases:
        try:
            resp = requests.get(BASE_URL, params={"name": name, "threshold": 75, "limit": 1}, headers=HEADERS)
            data = resp.json()
            actual = data.get("match_found", False)
            status = "✅ OK" if actual == expected else "❌ FAIL"
            
            # Si hay un hit inesperado o esperado, mostrar el score
            hit_info = ""
            if actual and data.get("results"):
                res = data["results"][0]
                hit_info = f" (Hit: {res['nombre_original']} - {res['score']}%)"
            
            print(f"{desc:<30} | {str(expected):<10} | {str(actual):<10} | {status}{hit_info}")
        except Exception as e:
            print(f"{desc:<30} | Error: {e}")

if __name__ == "__main__":
    run_tests()
