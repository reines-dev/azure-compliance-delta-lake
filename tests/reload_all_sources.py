import requests
import time

BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod"
SOURCES = ["ofac", "onu", "sat69b", "fbi", "worldbank", "ue", "dea", "interpol", "fto", "contraloria"]

def reload_all():
    print("🚀 Iniciando Recarga Masiva de 10 fuentes en AWS...")
    
    for source in SOURCES:
        print(f"\n--- Procesando: {source.upper()} ---")
        try:
            # 1. Ingest
            print(f"[{source}] Paso 1: Ingesta...", end=" ", flush=True)
            r1 = requests.post(f"{BASE_URL}/etl/ingest/{source}", timeout=120)
            print(f"✅ {r1.status_code}")
            
            # 2. Transform
            print(f"[{source}] Paso 2: Transformación...", end=" ", flush=True)
            r2 = requests.post(f"{BASE_URL}/etl/transform/{source}", timeout=120)
            print(f"✅ {r2.status_code}")
            
            # 3. Load
            print(f"[{source}] Paso 3: Carga Gold (Delta)...", end=" ", flush=True)
            r3 = requests.post(f"{BASE_URL}/etl/load/{source}", timeout=120)
            print(f"✅ {r3.status_code}")
            
        except Exception as e:
            print(f"❌ ERROR en {source}: {e}")
        
        time.sleep(1)

    print("\n--- Finalizando: Refrescando Cache de API ---")
    requests.get(f"{BASE_URL}/check/", params={"name": "TEST", "refresh": "true"})
    print("✨ Proceso completado. Todas las listas deberían estar visibles.")

if __name__ == "__main__":
    reload_all()
