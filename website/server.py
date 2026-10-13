"""WSGI entry point; secrets are injected by the service environment."""
import os
from . import create_app

app = create_app(os.environ.get('BOOKSITE_DATA_DIR', 'output/website-data'))
