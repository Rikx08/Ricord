"""
ASGI config for Ricord project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
import socketio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ricord.settings')
django.setup()

# Создаём Socket.IO сервер
sio = socketio.AsyncServer(async_mode='asgi')
django_app = get_asgi_application()
application = socketio.ASGIApp(sio, django_app)