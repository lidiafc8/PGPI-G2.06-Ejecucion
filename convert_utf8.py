import codecs

# Abrir "como sea" y escribir en UTF-8
with open("fixtures/home.json", "rb") as f:
    data = f.read()

# Decodificar ignorando errores y luego volver a UTF-8
text = data.decode("utf-8", errors="ignore")

with open("fixtures/home.json", "w", encoding="utf-8") as f:
    f.write(text)

print("Archivo convertido a UTF-8")