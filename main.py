from twisted.internet import reactor, threads
from twisted.web.resource import Resource
from twisted.web.server import Site
import config
import time
import webserver
import threading

#--------------------------------------------------------------------------------
# Daemon thread to monitor mumudvb
#--------------------------------------------------------------------------------
class mumudvbThread(threading.Thread):
    def __init__(self, threadID, name, delay):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay
        self.daemon = 1
    def run(self):
        print 'Starting ' + self.name
        while(1):
            time.sleep(self.delay)
            print "%s: %s" % (self.name, time.ctime(time.time()))
        
threadLock = threading.Lock()
threads = []

mumudvbThread = mumudvbThread(1, "MuMuDVB thread", 5)
mumudvbThread.start()
threads.append(mumudvbThread)

#--------------------------------------------------------------------------------
# Main webserver thread
#--------------------------------------------------------------------------------
root = Resource()
root.putChild('status', webserver.StatusPage())
root.putChild('', webserver.Status())
factory = Site(root)
reactor.listenTCP(config.port, factory)
reactor.run()
