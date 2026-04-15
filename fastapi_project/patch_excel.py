import re

path = "c:/HD/fastapi_project/main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add branch prefix resolution before the loop
target1 = """        existing_count = session.exec(select(Paciente)).all()
        hc_counter = len(existing_count) + 1"""

replacement1 = """        suc = session.get(Sucursal, user.sucursal_id)
        prefix = suc.nombre[:3].upper() if suc and len(suc.nombre) >= 3 else "GEN"
        last_patient = session.exec(select(Paciente).order_by(Paciente.id.desc())).first()
        hc_counter = (last_patient.id + 1) if last_patient else 1"""

text = text.replace(target1, replacement1)

# 2. Modify loop content to apply the new format
target2 = """            ficha_val = clean_str(get_col('FICHA'))
            if ficha_val:
                historia_clinica = ficha_val
            else:
                historia_clinica = f"HC-{hc_counter:05d}"
                hc_counter += 1"""

replacement2 = """            historia_clinica = f"HC-{prefix}-{hc_counter:04d}"
            hc_counter += 1"""

text = text.replace(target2, replacement2)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Excel patch applied.")
