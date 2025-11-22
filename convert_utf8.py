import os

input_file = "fixtures/home.json"
output_file = "fixtures/home_utf8.json"

# Intentamos abrir como UTF-16LE primero
try:
    with open(input_file, "r", encoding="utf-16") as f:
        data = f.read()
except UnicodeError:
    # Si falla, lo abrimos como bytes y eliminamos bytes inválidos
    with open(input_file, "rb") as f:
        data = f.read().decode("utf-8", errors="ignore")

# Guardamos en UTF-8
with open(output_file, "w", encoding="utf-8") as f:
    f.write(data)

print(f"Archivo convertido a UTF-8: {output_file}")