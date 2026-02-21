import requests

API_URL = "http://localhost:8000/check-name"

def test():
    # Buscamos por apellido primero como suele estar en OFAC
    query = "MADURO MOROS"
    print("Consultando: " + query)
    r = requests.get(API_URL, params={"name": query, "threshold": 50})
    if r.status_code == 200:
        results = r.json().get("results", [])
        for res in results:
            print("Match: " + res["nombre_original"] + " | Score: " + str(res["score"]))
    else:
        print("Error: " + str(r.status_code))

if __name__ == "__main__":
    test()
