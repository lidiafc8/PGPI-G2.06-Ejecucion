import smtplib, os, traceback

host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
port = int(os.environ.get('EMAIL_PORT', '587'))
user = os.environ.get('GMAIL_HOST_USER', '')
pwd = os.environ.get('GMAIL_HOST_PASSWORD', '')

print("Conectando a", host, port, "como", user)
try:
    s = smtplib.SMTP(host, port, timeout=15)
    # Mostrar diálogo SMTP para depuración
    s.set_debuglevel(1)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(user, pwd)
    print("Login OK")
    s.quit()
except Exception:
    traceback.print_exc()
