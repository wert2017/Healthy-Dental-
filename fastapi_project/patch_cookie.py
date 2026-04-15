import re

path = "c:/HD/fastapi_project/main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = '    response.set_cookie(key="user_role", value=user.role, httponly=False)'
replacement = '    response.set_cookie(key="user_role", value=user.role, httponly=False)\n    if final_sucursal_id:\n        response.set_cookie(key="sucursal_id", value=str(final_sucursal_id), httponly=False)'

text = text.replace(target, replacement)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Cookie patch applied.")
