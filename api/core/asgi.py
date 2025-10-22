import os

from django.core.asgi import get_asgi_application

# 1. Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 2. Get the ASGI application callable
application = get_asgi_application()