import requests
import sys

try:
    # Get doctor token
    r = requests.post('http://localhost:8000/token', data={'username':'jrodriguez','password':'password123','sucursal_id':'1'})
    token = r.json().get('access_token')
    if not token:
        print("Login failed, trying admin")
        r = requests.post('http://localhost:8000/token', data={'username':'admin','password':'password123','sucursal_id':'1'})
        token = r.json().get('access_token')

    headers = {'Authorization': f'Bearer {token}'}
    # Get an attention id
    r_at = requests.get('http://localhost:8000/api/atenciones/dashboard', headers=headers)
    atenciones = r_at.json()
    if not atenciones:
        print("No atenciones")
        sys.exit(1)
        
    at_id = atenciones[0]['id']
    print(f"Testing atencion {at_id}")
    
    # Hit the endpoint
    r2 = requests.post(f'http://localhost:8000/api/atenciones/{at_id}/solicitar-revision', headers=headers)
    print(f"STATUS: {r2.status_code}")
    print(r2.text)

except Exception as e:
    print(e)
