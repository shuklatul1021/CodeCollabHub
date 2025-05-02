import os
import sys
import logging
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import path
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codecollabhub.settings')

# Get the WSGI application
app = get_wsgi_application()

def handler(event, context):
    try:
        # Convert Vercel event to WSGI environ
        environ = {
            'REQUEST_METHOD': event.get('httpMethod', 'GET'),
            'PATH_INFO': event.get('path', '/'),
            'QUERY_STRING': event.get('queryStringParameters', {}),
            'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
            'CONTENT_LENGTH': event.get('headers', {}).get('content-length', ''),
            'wsgi.input': event.get('body', ''),
            'wsgi.url_scheme': 'https',
            'wsgi.errors': sys.stderr,
            'wsgi.version': (1, 0),
            'wsgi.run_once': False,
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
        }

        # Add headers
        for key, value in event.get('headers', {}).items():
            environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

        # Get Django response
        response = app(environ, lambda status, headers: None)

        # Convert Django response to Vercel response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': ''.join(response),
        }
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return {
            'statusCode': 500,
            'body': str(e),
        }

# Initialize Django
try:
    logger.info("Django application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Django application: {str(e)}")
    raise 