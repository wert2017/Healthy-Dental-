import requests

try:
    r = requests.post('http://localhost:8000/token', data={'username':'admin','password':'password123'})
    token = r.json().get('access_token')

    headers = {'Authorization': f'Bearer {token}'}
    r2 = requests.get('http://localhost:8000/api/nomina/pendientes', headers=headers)
    print(f"Status: {r2.status_code}")
    print(r2.text[:1000] if len(r2.text) > 1000 else r2.text)
except Exception as e:
    print("Error:", e)
