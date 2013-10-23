from application import log
from application.notification import IObserver, NotificationCenter
from application.python import Null
from application.python.types import Singleton

from eventlib import api, coros, proc

from threading import Lock
from twisted.internet import reactor
from zope.interface import implements

__all__ = ['MumuCheck']

class MumuApplication(object):
    implements(IObserver)

    log.msg("Mumu")


    def start(self):
        notification_center = NotificationCenter()
        notification_center.add_observer(self, name='SystemIPAddressDidChange')
        notification_center.add_observer(self, name='SystemDidWakeUpFromSleep')
        self._select_proc = proc.spawn(self._process_files)
        proc.spawn(self._handle_commands)
        self._activate()

