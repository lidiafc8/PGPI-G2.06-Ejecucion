import smtplib
import os

print('Usando variables:')
print('USE_GMAIL=', os.environ.get('USE_GMAIL'))
print('GMAIL_HOST_USER=', os.environ.get('GMAIL_HOST_USER'))
print('GMAIL_HOST_PASSWORD=', bool(os.environ.get('GMAIL_HOST_PASSWORD')) and '***SET***' or 'NOT SET')

s = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
s.set_debuglevel(1)
s.ehlo()
s.starttls()
s.ehlo()
try:
    user = os.environ.get('GMAIL_HOST_USER', '')
    passwd = os.environ.get('GMAIL_HOST_PASSWORD', '')
    print('Intentando login...')
    s.login(user, passwd)
    print('Login OK')
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    try:
        s.quit()
    except Exception:
        pass

print('Fin prueba SMTP')
