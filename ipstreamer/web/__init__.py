from application import log
from application.python.types import Singleton
from twisted.internet import reactor

from ipstreamer.configuration import GeneralConfiguration
from ipstreamer.web.site import get_site


class WebHandler(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._listener = None

    def start(self):
        if self._listener is None:
            self._listener = reactor.listenTCP(Configuration.role_port, get_site())
            log.msg('Web services listening on: %s' % self._listener.getHost())

    def stop(self):
        if self._listener is not None:
            self._listener.stopListening()