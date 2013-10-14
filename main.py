from twisted.internet import reactor, defer, utils
from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from calendar import calendar
import json
import socket
import time

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

#--------------------------------------------------------------------------------
# Calculate uptime
#--------------------------------------------------------------------------------
def getUptime():
    return time.time() - startTime

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

class StatusPage2(Resource):
    def __init__(self, year):
        Resource.__init__(self)
        self.year = year

    def _delayedRender(self, message, request):
        request.write('<html><body><pre>'+ message + '</pre></body></html>', )
        request.finish()
                
    def _errorRender(self, error, request):
        request.write('<html><body>Internal server error</body></html>')
        request.finish()
                
    def render_GET(self, request):
        d = utils.getProcessOutput('w')
        #d = self.Resource.getW()
        d.addCallback(self._delayedRender, request)
        d.addErrback(self._errorRender, request)
        return NOT_DONE_YET

class Status(Resource):
  def getChild(self, name, request):
      return YearPage(int(name))
      
  def getW(self):
      return utils.getProcessOutput('w')

root = Resource()
root.putChild('status', StatusPage())
root.putChild('', Status())
factory = Site(root)
reactor.listenTCP(port, factory)
reactor.run()