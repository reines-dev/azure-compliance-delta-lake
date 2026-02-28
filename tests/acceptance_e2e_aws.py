import requests
import sys

BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod/check/"

# Casos de prueba certificados para las 10 fuentes principales
ACCEPTANCE_TESTS = [
    {"source_id": "ONU", "query": "Al-Qaida", "threshold": 70},
    {"source_id": "OFAC", "query": "Maduro Moros", "threshold": 80},
    {"source_id": "SAT69B", "query": "BERNABASTOS", "threshold": 90},
    {"source_id": "FBI", "query": "OCHICHENKO", "threshold": 60},
    {"source_id": "WORLDBANK", "query": "China State Construction", "threshold": 60},
    {"source_id": "UE", "query": "Vladimir", "threshold": 60},
    {"source_id": "DEA", "query": "Marset Cabrera", "threshold": 70},
    {"source_id": "INTERPOL", "query": "Guzman", "threshold": 70},
    {"source_id": "FTO", "query": "ISIS", "threshold": 80},
    {"source_id": "CONTRALORIA", "query": "COLPATRIA", "threshold": 70}
]

def run_acceptance_suite():
    print("="*80)
    print("🚀 COMPLIANCEGUARD - CERTIFICACIÓN FINAL 10/10 E2E (AWS PROD)")
    print("="*80)
    print(f"{'FUENTE':<15} | {'BÚSQUEDA':<25} | {'STATUS'}")
    print("-" * 80)

    passed = 0
    total = len(ACCEPTANCE_TESTS)

    for test in ACCEPTANCE_TESTS:
        source_target = test["source_id"]
        query = test["query"]
        try:
            # Usamos el filtro de fuente para una validación pura de cada partición
            params = {"name": query, "threshold": test["threshold"], "limit": 10, "source": source_target}
            resp = requests.get(BASE_URL, params=params, timeout=30)
            data = resp.json()
            
            success = data.get("match_found", False)
            status_str = "✅ PASSED" if success else "❌ FAILED"
            
            if success:
                passed += 1
                score = data['results'][0]['score']
                status_str += f" ({score}%)"

            print(f"{source_target:<15} | {query:<25} | {status_str}")
        except Exception as e:
            print(f"{source_target:<15} | {query:<25} | ❌ ERROR: {str(e)[:20]}")

    print("="*80)
    print(f"RESUMEN FINAL: {passed}/{total} FUENTES OPERATIVAS ({(passed/total)*100:.1f}%)")
    print("="*80)
    
    if passed == total:
        print("🎉 ¡SISTEMA COMPLETAMENTE CERTIFICADO PARA PRODUCCIÓN!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_acceptance_suite()
