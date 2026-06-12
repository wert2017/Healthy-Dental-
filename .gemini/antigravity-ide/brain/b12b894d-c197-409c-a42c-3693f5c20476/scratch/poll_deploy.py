import time
import requests

url = "https://healthydentalec.com/static/gastos.html"
max_attempts = 20
delay = 15

print("Starting deployment check on: " + url)
for attempt in range(1, max_attempts + 1):
    try:
        r = requests.get(url, timeout=10)
        found = ':class="totalNetoFiltradosEsNegativo ? \'border-rose-500\' : \'border-emerald-500\'"' in r.text
        print(f"Attempt {attempt}/{max_attempts}: Status {r.status_code}, Found: {found}")
        if found:
            print("DEPLOYMENT SUCCESSFUL!")
            break
    except Exception as e:
        print(f"Attempt {attempt}/{max_attempts}: Error - {e}")
    time.sleep(delay)
else:
    print("DEPLOYMENT TIMEOUT - Please check build logs on Railway.")
