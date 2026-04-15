import requests
import sys

try:
    r = requests.post('http://localhost:8000/token', data={'username':'admin','password':'password123','sucursal_id':'1'})
    token = r.json().get('access_token')
    if not token:
        print("No token")
        sys.exit(1)
    
    r2 = requests.get('http://localhost:8000/api/reportes/ingresos-mensuales', headers={'Authorization': f'Bearer {token}'})
    print(r2.status_code)
    data = r2.json()
    doctores = data.get("produccion_doctores", [])
    print(f"Doctors count: {len(doctores)}")
    if not doctores:
        print("List is EMPTY.")
    else:
        print("First doctor:", doctores[0]['nombre'])
except Exception as e:
    print(e)
