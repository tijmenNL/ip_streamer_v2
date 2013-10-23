
import platform

from application import log
from flask import Flask, request
from werkzeug.routing import BaseConverter

import op2d

from ipstreamer.web.api.utils import error_response, get_state, get_json, jsonify, set_state

__all__ = ['app']


app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'msg': 'resource not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'msg': 'internal server error'}), 500


@app.route('/')
def index():
    message = 'OP2d version %s APIv1' % op2d.__version__
    return jsonify({'message': message})

#--------------------------------------------------------------------------------
# Channel page (/channel) post or get with child info
#--------------------------------------------------------------------------------

@app.route('/channel/<address>', methods=['GET','POST'])
def handle_channel(address):
    if request.method == 'POST':
        return 'Done'
    else:
        log.msg('Got status request for %s' % address)
        try:
            return str(channelStatus[address])
        except KeyError:
            log.msg('Got channel status request for unknown address %s' % address)
            abort(404)

#--------------------------------------------------------------------------------
# Config page (/config)
#--------------------------------------------------------------------------------
@app.route('/config', methods=['POST'])
def handle_config():
    if request.method == 'POST':
        log.msg('Received JSON post with config')
        jsonConfig = request.get_json(True)
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