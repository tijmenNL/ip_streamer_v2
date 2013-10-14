from twisted.internet import defer, utils
from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
import config
import json
import socket
import time

#--------------------------------------------------------------------------------
# Status page
#--------------------------------------------------------------------------------
class StatusPage(Resource):                
    def render_GET(self, request):
        streamerStatus = {}
        streamerStatus['version'] =  config.version
        streamerStatus['uptime'] = int(config.getUptime())
        streamerStatus['IP'] = socket.gethostbyname(socket.gethostname())
        streamerStatus['role_type'] = config.role_type
        streamerStatus['port'] = config.port
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