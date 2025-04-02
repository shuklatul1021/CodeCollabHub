import os
import sys
import logging
from django.core.wsgi import get_wsgi_application

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codecollabhub.settings')
    
    # Get the WSGI application
    app = get_wsgi_application()
    
    logger.info("Django application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Django application: {str(e)}")
    raise 