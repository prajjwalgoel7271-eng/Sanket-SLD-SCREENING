import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

class VercelPathFix:
    """
    Middleware to fix PATH_INFO routing in Vercel CLI 59+.
    Strips internal rewrite prefixes (/api/index.py, /api/index, /api) so
    Flask matches application routes correctly.
    """
    def __init__(self, flask_app):
        self.flask_app = flask_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        for prefix in ['/api/index.py', '/api/index', '/api']:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
        if not path or not path.startswith('/'):
            path = '/' + path
        environ['PATH_INFO'] = path
        return self.flask_app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
