import requests, json

API_URL = "https://1plkktk2ak.execute-api.us-east-1.amazonaws.com/prod/check/"
API_KEY = "yKEM6Phs6rW5Pb9j04Sl1AayX5KsL5w9Zqb85X25"
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json"}

probes = [
    ("OFAC",          "Gustavo Petro",              80),
    ("ONU",           "Al-Qaida",                   70),
    ("PEP",           "ELKIN DAVID GALLEGO GIRALDO",80),
    ("US_FBI_MOST_WANTED", "Ochichenko",            60),
    ("WORLDBANK",     "China State Construction",   60),
    ("EU_FSF",        "Vladimir Putin",             75),
    ("US_DEA_FUGITIVES","Marset Cabrera",           70),
    ("INTERPOL_RED_NOTICES","Guzman",               70),
    ("FTO",           "ISIS",                       70),
    ("CONTRALORIA",   "ELECTRICARIBE",              70),
]

print(f"{'FUENTE':<25} | {'QUERY':<35} | STATUS")
print("-"*80)
for source, query, thresh in probes:
    try:
        r = requests.get(API_URL, params={"name":query,"threshold":thresh,"limit":5,"source":source,"refresh":"false"}, headers=HEADERS, timeout=20)
        d = r.json()
        if d.get("match_found"):
            hit = d["results"][0]
            print(f"{source:<25} | {query:<35} | ✅ '{hit['nombre_original'][:30]}' ({hit['score']}%)")
        else:
            print(f"{source:<25} | {query:<35} | ❌ NOT FOUND")
    except Exception as e:
        print(f"{source:<25} | {query:<35} | ❌ ERROR: {e}")
