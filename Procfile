web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker --chdir fastapi_project main:app --bind 0.0.0.0:$PORT --forwarded-allow-ips="*"
