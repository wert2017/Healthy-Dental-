import re

path = "c:/HD/fastapi_project/main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Fix 1: Try/except block for on_startup user creation
pattern1 = r'(with Session\(engine\) as session:[\s]+)(user = session\.exec\(select\(User\)\.where\(User\.username == "admin"\)\)\.first\(\))'
replacement1 = r'\1try:\n            \2'
text = re.sub(pattern1, replacement1, text, count=1)

pattern1_cont = r'(session\.commit\(\))([\s]+)(# --- API ROUTES ---|@app\.get\("/api/public)'
replacement1_cont = r'\1\n        except Exception as e:\n            session.rollback()\n            print(f"Skipping default user creation: {e}")\2\3'
text = re.sub(pattern1_cont, replacement1_cont, text)

# By introducing 'try:', everything inside needs to be indented. But wait! Python 3 doesn't demand that replacing the first line indents the rest. If I just add 'try:' I HAVE to indent the rest of the block manually!
# Actually, it's easier to just catch IntegrityError exactly around session.commit() ONLY!
# If session.commit() fails because of UNIQUE constraint, we just catch it there!
# Let's read the file again and just wrap session.commit() inside a try-except.

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "        session.commit()",
    "        try:\n            session.commit()\n        except Exception as e:\n            session.rollback()\n            print(f\"Skipping user creation error: {e}\")", 
    1  # only first occurrence which is in on_startup
)

# Fix 2: Add user sucursal_id to Excel importer
text = text.replace(
    'async def importar_pacientes_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):',
    'async def importar_pacientes_excel(file: UploadFile = File(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):'
)

text = text.replace(
    '                activo=True\n            )\n            session.add(nuevo_paciente)',
    '                activo=True,\n                sucursal_id=user.sucursal_id\n            )\n            session.add(nuevo_paciente)'
)

text = text.replace(
    '                activo=True\r\n            )\r\n            session.add(nuevo_paciente)',
    '                activo=True,\r\n                sucursal_id=user.sucursal_id\r\n            )\r\n            session.add(nuevo_paciente)'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Patch applied.")
