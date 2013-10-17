#!/usr/bin/env python

from twisted.internet import reactor, task, defer, utils, threads 
from twisted.internet.task import deferLater
from twisted.python import log, logfile
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
import argparse
import ConfigParser
import cyclone.httpclient
import json
import os
import re
import socket
import sys
import time
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

#--------------------------------------------------------------------------------
# Command line options
#--------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='VICE ip streamer to control mumudvb.')
parser.add_argument('-d', '--debug', help='Run in debug mode', action='store_true', default=False, dest='debug')

args = parser.parse_args()
debug = args.debug

#--------------------------------------------------------------------------------
# Log handler
#--------------------------------------------------------------------------------
if (debug):
    log.startLogging(sys.stdout)
else:
    logFile = logfile.LogFile("ip_streamer.log", "/tmp")
    log.startLogging(logFile)
    
#-------------------------------------------------------------------------------
# Help information on flags
#-------------------------------------------------------------------------------
# something with wargs
    
#--------------------------------------------------------------------------------
# Read config, exit if no config is found
#--------------------------------------------------------------------------------
config = ConfigParser.ConfigParser()
if(os.path.isfile('/etc/vice/config.ini')):
    config.read('/etc/vice/config.ini')
    viceIp = config.get('settings','server')
    vicePort = config.get('settings','port')
    viceServer = 'http://' + viceIp + ':' + vicePort
    updatetime = config.get('settings_mumudude','updatetime')
    tmpdir = config.get('settings_mumudude','tmpdir')
    mumudvblogdir = config.get('settings_mumudude','mumudvblogdir')
    mumudvbbindir = config.get('settings_mumudude','mumudvbbindir')    
else:
    sys.exit('No config file found, please install /etc/vice/config.ini')

#--------------------------------------------------------------------------------
# Calculate uptime
#--------------------------------------------------------------------------------
def getUptime():
    return time.time() - startTime

#--------------------------------------------------------------------------------
# Return the current streamer status in JSON format
#--------------------------------------------------------------------------------    
def getStatus():
        streamerStatus = {}
        streamerStatus['version'] =  version
        streamerStatus['uptime'] = int(getUptime())
        streamerStatus['ip'] = socket.gethostbyname(socket.gethostname())
        streamerStatus['role_type'] = role_type
        streamerStatus['port'] = port
        streamerStatus['mumudvb_version'] = 0
        return json.dumps(streamerStatus)
    
#--------------------------------------------------------------------------------
# Daemon thread to monitor mumudvb
#--------------------------------------------------------------------------------
def mumudvbThread(name):
    print "%s: %s" % (name, time.ctime(time.time()))

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
# Analyze post response
#--------------------------------------------------------------------------------
def postResponse(self,successMsg,failMsg, die):
    if (self.code != 200):
        log.msg(failMsg)
        log.msg(str(self.code) + ' ' + self.phrase)
        s = re.findall('<title>.*</title>',self.body)[0]
        log.msg(s[7:s.rfind("</title>")])
        if(die):
            log.msg('Invalid response from VICE, missing key information. Will now stop!')
            reactor.stop()            
    else:
        log.msg(successMsg)
        
#--------------------------------------------------------------------------------
# Post status to vice server
#--------------------------------------------------------------------------------
def postStatus():
        d = cyclone.httpclient.fetch(viceServer + '/frontend_test.php/role_status',postdata=getStatus(), headers={"Content-Type": ["application/json"]})
        d.addCallback(postResponse,'Posted status to VICE server','Posting to VICE server failed!', False)        
        #post(viceServer + '/frontend_test.php/role_status',getStatus())
        
#--------------------------------------------------------------------------------
# Main page
#--------------------------------------------------------------------------------
class base(Resource):
    def render_GET(self, request):
        request.setResponseCode(404)
        request.write('<html><h1>404 not found</h1></html>')
        request.finish()
        return NOT_DONE_YET

#--------------------------------------------------------------------------------
# Channel status page
#--------------------------------------------------------------------------------      
class channelPage(Handling):
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
# Config page
#--------------------------------------------------------------------------------      
class configPage(Handling):
    def render_POST(self, request):        
        jsonConfig = json.loads(request.content.getvalue())        
        mumudvbConfig = ConfigParser.SafeConfigParser()
        type = jsonConfig[0]['_']['type'] 
        if (type == 'DVB-C'):
            jsonConfig[0]['_']['freq'] =  int(jsonConfig[0]['_']['freq'])/1000
        jsonConfig[0]['_']['srate'] = int(jsonConfig[0]['_']['srate'])/1000
        for index in sorted(jsonConfig[0], reverse=True):                
            mumudvbConfig.add_section(index)
            for key in jsonConfig[0][index]:
                if (jsonConfig[0][index][key] != None and key != 'type'):
                        mumudvbConfig.set(index,str(key),str(jsonConfig[0][index][key]))
        with open('mumu.ini', 'wb') as configfile:   
            mumudvbConfig.write(configfile)
        return ''

#--------------------------------------------------------------------------------
# Streamer status page
#--------------------------------------------------------------------------------
class statusPage(Resource):                
    def render_GET(self, request):
        request.write(getStatus())
        request.finish()
        return NOT_DONE_YET
        
#--------------------------------------------------------------------------------
# Channel page, post or get with child info
#--------------------------------------------------------------------------------     
class channel(Resource):
    def getChild(self, name, request):
        return channelPage(str(name))
        
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
root = base()
root.putChild('status', statusPage())
root.putChild('channel', channel())
root.putChild('config', configPage())
root.putChild('', base())
factory = Site(root)
mumudvbThread = task.LoopingCall(mumudvbThread,"MuMuDVB thread")
reactor.listenTCP(port, factory)
mumudvbThread.start(10)
reactor.callLater(0, postStatus)
reactor.run()



