from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware

from ipstreamer.web.api import v1

__all__ = ['app']


# Empty app to  use with DispatcherMiddleware
_app = Flask(__name__)

@_app.route('/')
def index():
    return ''


# Support multiple API versions
app = DispatcherMiddleware(_app, {'/v1': v1.app})