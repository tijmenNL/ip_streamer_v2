#!/usr/bin/env python

from twisted.internet import reactor, task, defer, utils, threads, defer, protocol
from twisted.internet.task import deferLater
from twisted.python import log, logfile
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
import argparse
import ConfigParser
import cyclone.httpclient
import json
import re
import socket
import sys
import time
import warnings

#--------------------------------------------------------------------------------
# Initial values
#--------------------------------------------------------------------------------
startTime = time.time()
channelStatus = {}
subProcesses = {}

#--------------------------------------------------------------------------------
# Program settings
#--------------------------------------------------------------------------------
version = '0.1'
role_type = 'ip_streamer'
port = 8765
mumudvbVersion = 0

class getMumudvbVersion(protocol.ProcessProtocol):
    def errReceived(self, data):
        #print "errReceived! with %s" % (data)
        global mumudvbVersion
        mumudvbVersion = re.findall('Version.*',data)[0][8:]
    def processEnded(self, reason):
        reactor.callLater(0, postStatus)
mumu = getMumudvbVersion()
cmd = ["mumudvb", "--help"]
reactor.spawnProcess(mumu, cmd[0], cmd, env=None, childFDs={0:"w", 1:"r", 2:"r", 3:"w"})

#--------------------------------------------------------------------------------
# Start mumudvb on card
#--------------------------------------------------------------------------------
class startMumudvb(protocol.ProcessProtocol):
    def __init__(self, card):
        self.card = card
    def connectionMade(self):
        self.pid = self.transport.pid
    def outReceived(self, data):
        print "outReceived! with %d bytes!" % len(data)
        print data
        print self.pid
    def errReceived(self, data):
        print "errReceived! with %d bytes!" % len(data)
        print data        
    def inConnectionLost(self):
        print "inConnectionLost! stdin is closed! (we probably did it)"
    def outConnectionLost(self):
        print "outConnectionLost! The child closed their stdout."
    def errConnectionLost(self):
        print "errConnectionLost! The child closed their stderr."
    def processExited(self, reason):
        log.msg("MuMuDVB exited with status code %d" % (reason.value.exitCode))
        
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
    
#--------------------------------------------------------------------------------
# Read config, exit if no config is found
#--------------------------------------------------------------------------------
config = ConfigParser.ConfigParser()
path = FilePath('/etc/vice/config.ini')
if(FilePath.isfile(path)):
    config.read('/etc/vice/config.ini')
    viceIp = config.get('settings','server')
    vicePort = config.get('settings','port')
    viceServer = 'http://' + viceIp + ':' + vicePort
    updatetime = config.get('settings_mumudude','updatetime')
    tmpdir = FilePath(config.get('settings_mumudude','tmpdir'))
    if not FilePath.isdir(tmpdir):
        FilePath.createDirectory(tmpdir)
    mumudvblogdir = FilePath(config.get('settings_mumudude','mumudvblogdir'))
    if not FilePath.isdir(mumudvblogdir):
        FilePath.createDirectory(mumudvblogdir)
    mumudvbbindir = FilePath(config.get('settings_mumudude','mumudvbbindir'))   
    if not FilePath.isdir(mumudvbbindir):
        FilePath.createDirectory(mumudvbbindir)
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
    streamerStatus['mumudvb_version'] = mumudvbVersion
    return json.dumps(streamerStatus)

def getChannelStatus():
    statusFiles = FilePath.globChildren(mumudvblogdir, 'channels*')
    for path in statusFiles:
        for line in FilePath.open(path):
            card = path.path.split('adapter')[1].split('_')[0]
            fields = line.split(':')
            channelStatus[fields[0] + ':' + fields[1]] = {}
            try:
                channelStatus[fields[0] + ':' + fields[1]]['streamstatus']  = fields[3][:len(fields[3])-1]
            except IndexError:
                channelStatus[fields[0] + ':' + fields[1]]['streamstatus'] = 'NotTransmitted'            
            channelStatus[fields[0] + ':' + fields[1]]['card'] = card
            channelStatus[fields[0] + ':' + fields[1]]['ip'] = fields[0] + ':' + fields[1]
            channelStatus[fields[0] + ':' + fields[1]]['name'] = fields[2]
            # Set cardstatus to 0 if it does not yet exist
            channelStatus[fields[0] + ':' + fields[1]]['cardstatus'] = (channelStatus[fields[0] + ':' + fields[1]].get('cardstatus',0))
    
#--------------------------------------------------------------------------------
# Daemon thread to monitor mumudvb
#--------------------------------------------------------------------------------
def mumudvbThread(name):
    getChannelStatus()
    for ip in channelStatus:
        d = cyclone.httpclient.fetch(viceServer + '/frontend_test.php/ip_streamer_channel',postdata=json.dumps(channelStatus[ip]), headers={"Content-Type": ["application/json"]})
        d.addCallback(postResponse,'','Posting channel status failed')        
   
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
def postResponse(self,successMsg = '',failMsg = '', die = False):
    if (self.code != 200):
        log.msg(failMsg)
        log.msg(str(self.code) + ' ' + self.phrase)
        s = re.findall('<title>.*</title>',self.body)[0]
        log.msg(s[7:s.rfind("</title>")])
        if(die):
            log.msg('Invalid response from VICE, missing key information. Will now stop!')
            reactor.stop()            
    elif successMsg != '':
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
        request.write('<html><body><h1>404 not found</h1></body></html>')
        request.finish()
        return NOT_DONE_YET

#--------------------------------------------------------------------------------
# Channel status page
#--------------------------------------------------------------------------------      
class channelPage(Handling):
    def __init__(self,address):
        Resource.__init__(self)
        self.address = address
        
    def render_GET(self, request):
        log.msg(self.address)
        try:
            request.write('<html><body>' + str(channelStatus[self.address]) + '</body></html>')
        except KeyError:
            request.write('<html><body><h1>404 Not Found</h1></body></html>')
        request.finish()
        return NOT_DONE_YET

#--------------------------------------------------------------------------------
# Config page
#--------------------------------------------------------------------------------      
class configPage(Handling):
    def render_POST(self, request):        
        jsonConfig = json.loads(request.content.getvalue())        
        mumudvbConfig = ConfigParser.SafeConfigParser()
        for cardConfig in jsonConfig:
            card = cardConfig['_']['card']
            # Check the type, dvb-c = freq/1,000, dvb-s(2) = freq/1,000,000
            type = cardConfig['_']['type'] 
            if (type == 'DVB-C'):
                cardConfig['_']['freq'] =  int(cardConfig['_']['freq'])/1000
            else:
                cardConfig['_']['freq'] =  int(cardConfig['_']['freq'])/1000000
            # The DVB-S2 type needs an additional delivery system option
            if (type == 'DVB-S2'):
                cardConfig['_']['delivery_system'] = type
            cardConfig['_']['srate'] = int(cardConfig['_']['srate'])/1000
            cardConfig['_']['log_file'] = '/var/log/mumudvb' + card
            cardConfig['_']['log_type'] = 'syslog' 
            for section in sorted(cardConfig, reverse=True):                
                mumudvbConfig.add_section(section)
                for key in cardConfig[section]:
                    if (cardConfig[section][key] != None and key != 'type'):
                            mumudvbConfig.set(section,str(key),str(cardConfig[section][key]))                            
            cardConf = FilePath(tmpdir.path+'/dvbrc_adapter' + card + '.conf')
            with FilePath.open(cardConf, 'wb') as configfile:   
                mumudvbConfig.write(configfile)
            if FilePath.isfile(cardConf):
                mumu = startMumudvb(card)
                cmd = ["mumudvb","-d","-c", cardConf.path]
                log.msg('Starting MuMuDVB with the following flags: ' + str(cmd) + ' on card ' + card)
                process = reactor.spawnProcess(mumu, cmd[0], cmd, usePTY=True, env=None)
                log.msg(process)
        return ''

#--------------------------------------------------------------------------------
# Streamer status page
#--------------------------------------------------------------------------------
class statusPage(Handling):                
    def render_GET(self, request):        
        request.write(getStatus())
        request.finish()
        return NOT_DONE_YET
        
#--------------------------------------------------------------------------------
# Channel page, post or get with child info
#--------------------------------------------------------------------------------     
class channel(Handling):
    def getChild(self, name, request):
        log.msg(request)
        if name == '':
            return self        
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
def main():
    root = base()
    root.putChild('status', statusPage())
    root.putChild('channel', channel())
    root.putChild('config', configPage())
    root.putChild('', base())
    factory = Site(root)
    statusThread = task.LoopingCall(mumudvbThread,"MuMuDVB thread")
    reactor.listenTCP(port, factory)
    statusThread.start(10, False)
    reactor.run()
    
if __name__ == '__main__':
    main()


