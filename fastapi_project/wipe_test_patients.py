import requests

def run_nuke():
    print("Iniciando borrado de base de datos de pruebas en Railway...")
    
    # 1. Login auth
    url_login = "https://web-production-a3740.up.railway.app/token"
    # El usuario debe usar sus credenciales de Super-Administrador.
    # Cambia esto si tu contraseña de 'admin' no es 'admin'
    data = {"username": "admin", "password": "admin"} 
    
    print("Autenticando como Administrador...")
    try:
        resp = requests.post(url_login, data=data)
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Trigger Nuke Endpoint
            print("Enviando orden de borrado global al servidor...")
            url_nuke = "https://web-production-a3740.up.railway.app/api/admin/nuke-pacientes"
            nuke_resp = requests.delete(url_nuke, headers=headers)
            
            if nuke_resp.status_code == 200:
                print("¡EXITO!")
                print(nuke_resp.json().get("message"))
            else:
                print(f"Error en el servidor: {nuke_resp.status_code} - {nuke_resp.text}")
                
        else:
            print(f"Fallo al autenticar. Revisa que la contraseña local del admin sea correcta. {resp.text}")
            
    except Exception as e:
        print(f"No se pudo contactar al servidor: {e}")

if __name__ == "__main__":
    run_nuke()
