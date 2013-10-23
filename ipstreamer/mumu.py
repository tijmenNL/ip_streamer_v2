from application import log
from application.notification import IObserver, NotificationCenter
from application.python import Null
from application.python.types import Singleton

from threading import Lock
from twisted.internet import reactor
from zope.interface import implements

__all__ = ['MumuCheck']

class MumuApplication(object):
    implements(IObserver)

    log.msg("Mumu")


    def start(self):
        self._activate()

