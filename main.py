from twisted.internet import reactor, task, defer, utils, threads 
from twisted.internet.task import deferLater
from twisted.python import log, logfile
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
import ConfigParser
import json
import os
import time
import socket
import sys
import warnings

#--------------------------------------------------------------------------------
# Initial values
#--------------------------------------------------------------------------------
startTime = time.time()

#--------------------------------------------------------------------------------
# Program settings
#--------------------------------------------------------------------------------
version = '0.01'
role_type = 'ip_streamer'
port = 8765
debug = True



#--------------------------------------------------------------------------------
# Calculate uptime
#--------------------------------------------------------------------------------
def getUptime():
    return time.time() - startTime

#--------------------------------------------------------------------------------
# Daemon thread to monitor mumudvb
#--------------------------------------------------------------------------------
def mumudvbThread(name):
    print "%s: %s" % (name, time.ctime(time.time()))
        
#--------------------------------------------------------------------------------
# Log handler
#--------------------------------------------------------------------------------
if (debug):
    log.startLogging(sys.stdout)
else:
    logFile = logfile.LogFile("test.log", "/tmp")
    log.startLogging(logFile)

#--------------------------------------------------------------------------------
# Error and message handling
#--------------------------------------------------------------------------------
class Handling(Resource):
    def _delayedRender(self, message, request):
        request.write('<html><body><pre>'+ message + '</pre></body></html>', )
        request.finish()
                
    def _errorRender(self, error, request):
        request.write('<html><body>' + str(error) + '</body></html>')
        request.finish()
        
#--------------------------------------------------------------------------------
# Main page
#--------------------------------------------------------------------------------
class Root(Resource):
    def render_GET(self, request):
        request.setResponseCode(404)
        request.write('<html><h1>404 not found</h1></html>')
        request.finish()
        return NOT_DONE_YET

#--------------------------------------------------------------------------------
# Channel status page
#--------------------------------------------------------------------------------      
class ChannelPage(Handling):
    def __init__(self,ip):
        Resource.__init__(self)
        self.ip = ip
                
    def readFile(self):
        os.path.isfile('/tmp/test.log')
        data = file('/tmp/test.log').read()
        return data
        
    def render_GET(self, request):
        d = threads.deferToThread(self.readFile)  
        #d = self.Resource.getW()
        d.addCallback(self._delayedRender, request)
        d.addErrback(self._errorRender, request)
        return NOT_DONE_YET
        
#--------------------------------------------------------------------------------
# Streamer status page
#--------------------------------------------------------------------------------
class StatusPage(Resource):                
    def render_GET(self, request):
        streamerStatus = {}
        streamerStatus['version'] =  version
        streamerStatus['uptime'] = int(getUptime())
        streamerStatus['IP'] = socket.gethostbyname(socket.gethostname())
        streamerStatus['role_type'] = role_type
        streamerStatus['port'] = port
        request.write(json.dumps(streamerStatus))
        request.finish()
        return NOT_DONE_YET
        
#--------------------------------------------------------------------------------
# Channel page, post or get with child info
#--------------------------------------------------------------------------------     
class Channel(Resource):
    def getChild(self, name, request):
        return ChannelPage(str(name))
        
    def render_POST(self, request):
        return 'post'
        
    def render_GET(self, request):
        request.setResponseCode(404)
        request.write('<html><h1>404 not found</h1></html>')
        request.finish()
        return NOT_DONE_YET
    
#--------------------------------------------------------------------------------
# Main webserver thread
#--------------------------------------------------------------------------------
root = Root()
root.putChild('status', StatusPage())
root.putChild('channel', Channel())
root.putChild('', Root())
factory = Site(root)
mumudvbThread = task.LoopingCall(mumudvbThread,"MuMuDVB thread")
reactor.listenTCP(port, factory)
mumudvbThread.start(10)
reactor.run()
