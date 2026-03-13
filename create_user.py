import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
password = 'admin123'
email = 'admin@example.com'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Usuario creado: {username}")
    print(f"🔑 Contraseña: {password}")
else:
    u = User.objects.get(username=username)
    u.set_password(password)
    u.save()
    print(f"♻️ Usuario '{username}' ya existía. Se actualizó la contraseña a: {password}")
