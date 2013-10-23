from application import log
from application.notification import IObserver, NotificationCenter
from application.python import Null
from application.python.types import Singleton

__all__ = ['MumuCheck']

class MumuApplication(object):
    log.msg("Mumu")
