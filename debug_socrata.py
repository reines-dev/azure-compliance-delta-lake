import requests
import json

url = 'https://www.datos.gov.co/api/v3/views/3qxn-uc22/query.json'
print("Fetching PEP data from Socrata...")
try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Data loaded successfully.")
        print("Available keys in root object:", data.keys())
        if 'meta' in data:
            print("Meta info:", data['meta'])
        if 'datasets' in data:
            print("Datasets inside:", len(data['datasets']))
            # Socrata v3 JSON can behave differently.
            # Usually the dataframe should be data['data'] or data just contains a flat list if api/v2/
            
        print("\n\nFirst 200 chars of raw JSON dump:")
        print(json.dumps(data)[:200])
    else:
        print("HTTP Error:", response.status_code)
except Exception as e:
    print(e)
