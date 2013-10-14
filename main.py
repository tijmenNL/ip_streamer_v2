from twisted.internet import reactor, task
from twisted.web.resource import Resource
from twisted.web.server import Site
import config
import time
import webserver
import threading

#--------------------------------------------------------------------------------
# Daemon thread to monitor mumudvb
#--------------------------------------------------------------------------------
def mumudvbThread(name):
    print "%s: %s" % (name, time.ctime(time.time()))
        
#--------------------------------------------------------------------------------
# Main webserver thread
#--------------------------------------------------------------------------------
root = webserver.Root()
root.putChild('status', webserver.StatusPage())
root.putChild('channel', webserver.Channel())
root.putChild('', webserver.Root())
factory = Site(root)
thread = task.LoopingCall(mumudvbThread,"MuMuDVB thread")
thread.start(10)
reactor.listenTCP(config.port, factory)
reactor.run()
