import requests
import json
import time

API_URL = "http://localhost:8000/check-name"

def test_search(name, threshold=80, source=None):
    params = {
        "name": name,
        "threshold": threshold,
        "source": source
    }
    print(f"\n--- Buscando: '{name}' (Umbral: {threshold}%) ---")
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["match_found"]:
                print(f"✅ Se encontraron {len(data['results'])} coincidencias:")
                for res in data["results"]:
                    print(f"   [{res['fuente']}] {res['nombre_original']} - Score: {res['score']}%")
                    print(f"      - Tipo: {res['tipo_lista']}")
                    print(f"      - Metadata: {res['metadata']}")
            else:
                print("❌ No se encontraron coincidencias con ese umbral.")
        else:
            print(f"⚠️ Error en API: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexion: {e}")

if __name__ == "__main__":
    # Aseguramos que la API esté corriendo en WSL antes de llamar a este script
    test_search("NICOLAS MADURO", threshold=85)
    test_search("MADURO MOROS", threshold=80)
