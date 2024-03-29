from application import log
from application.notification import IObserver, NotificationCenter
from application.python import Null
from application.python.types import Singleton
from threading import Event
from zope.interface import implements

from twisted.internet import reactor, task, defer, utils, threads, defer, protocol

from ipstreamer.configuration import GeneralConfiguration,MumuConfiguration
from ipstreamer.web import WebHandler
from ipstreamer.mumu import MumuApplication

__all__ = ['IPStreamer']


class IPStreamerDaemon(object):
    __metaclass__ = Singleton
    implements(IObserver)

    def __init__(self):
        self.application = MumuApplication()
        self.stopping = False
        self.stop_event = Event()

        self.web_handler = WebHandler()

    def start(self):
        notification_center = NotificationCenter()
        notification_center.add_observer(self)
        notification_center.add_observer(self, sender=self.application)
        reactor.run();
        self.application.start()

    def stop(self):
        if self.stopping:
            return
        self.stopping = True
        self.application.stop()

    def handle_notification(self, notification):
        handler = getattr(self, '_NH_%s' % notification.name, Null)
        handler(notification)

    def _NH_SIPApplicationDidStart(self, notification):
        log.msg('IP streamer application started')
        self.web_handler.start()

    def _NH_SIPApplicationWillEnd(self, notification):
        self.web_handler.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        log.msg('IP Streamer application ended')
        self.stop_event.set()
