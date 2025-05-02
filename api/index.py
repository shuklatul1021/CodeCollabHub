import os
import sys
import logging
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import path
from django.conf import settings
from django.core.management import execute_from_command_line
from http.server import BaseHTTPRequestHandler
from io import BytesIO

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codecollabhub.settings')

# Get the WSGI application
app = get_wsgi_application()

class VercelRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, event, context):
        self.event = event
        self.context = context
        self.rfile = BytesIO(event.get('body', '').encode('utf-8') if event.get('body') else b'')
        self.wfile = BytesIO()
        self.headers = self.event.get('headers', {})
        self.path = self.event.get('path', '/')
        self.command = self.event.get('httpMethod', 'GET')
        self.request_version = 'HTTP/1.1'

    def send_response(self, code, message=None):
        self.response_code = code

    def send_header(self, keyword, value):
        if not hasattr(self, 'response_headers'):
            self.response_headers = {}
        self.response_headers[keyword] = value

    def end_headers(self):
        pass

    def handle_one_request(self):
        try:
            environ = {
                'REQUEST_METHOD': self.command,
                'PATH_INFO': self.path,
                'QUERY_STRING': self.event.get('queryStringParameters', {}),
                'CONTENT_TYPE': self.headers.get('content-type', ''),
                'CONTENT_LENGTH': self.headers.get('content-length', ''),
                'wsgi.input': self.rfile,
                'wsgi.url_scheme': 'https',
                'wsgi.errors': sys.stderr,
                'wsgi.version': (1, 0),
                'wsgi.run_once': False,
                'wsgi.multithread': True,
                'wsgi.multiprocess': False,
            }

            for key, value in self.headers.items():
                environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

            response = app(environ, lambda status, headers: None)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
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

def handler(event, context):
    try:
        handler = VercelRequestHandler(event, context)
        return handler.handle_one_request()
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
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