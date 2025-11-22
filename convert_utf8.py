import os

input_file = "fixtures/home_utf8.json"          # tu archivo original
output_file = "fixtures/home_utf8_1.json"    # archivo de salida en UTF-8

# Intentamos abrir como UTF-16LE o UTF-16BE
for enc in ["utf-16", "utf-16le", "utf-16be", "latin-1", "utf-8"]:
    try:
        with open(input_file, "r", encoding=enc) as f:
            data = f.read()
        print(f"Archivo leído correctamente con encoding: {enc}")
        break
    except UnicodeError:
        continue
else:
    raise ValueError("No se pudo determinar la codificación del archivo.")

# Guardamos en UTF-8 asegurando que las tildes se mantengan
with open(output_file, "w", encoding="utf-8") as f:
    f.write(data)

print(f"Archivo convertido a UTF-8 correctamente: {output_file}")