"""
ASGI config for codecollabhub project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# Set up Django settings before importing any models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codecollabhub.settings')

# Get the Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
application = get_asgi_application()
