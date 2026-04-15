import re

path = "c:/HD/fastapi_project/main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

target = """            historia_clinica = f"HC-{prefix}-{hc_counter:04d}"
            hc_counter += 1"""

replacement = """            ficha_val = clean_str(get_col('FICHA'))
            if ficha_val:
                try:
                    num_ficha = int(float(ficha_val))
                    historia_clinica = f"HC-{prefix}-{num_ficha:04d}"
                except (ValueError, TypeError):
                    # Si tiene letras u otros caracteres raros
                    historia_clinica = f"HC-{prefix}-{ficha_val}"
            else:
                historia_clinica = f"HC-{prefix}-{hc_counter:04d}"
                hc_counter += 1"""

text = text.replace(target, replacement)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Patch applied for FICHA maintenance.")
