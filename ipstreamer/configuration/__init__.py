from application.configuration import ConfigSection, ConfigSetting

from ipstreamer import cfg_filename
import os
import os.path

class Port(int):
    def __new__(cls, value):
        value = int(value)
        if not (0 <= value <= 65535):
            raise ValueError("illegal port value: %s" % value)
        return value


class GeneralConfiguration(ConfigSection):
    __cfgfile__ = cfg_filename
    __section__ = 'settings'

    server   = ConfigSetting(type=str, value=None)
    port = ConfigSetting(type=Port, value=8088)
    role_port = ConfigSetting(type=Port, value=8765)
    #vice_server = 'http://' + server + ':' + port


class MumuConfiguration(ConfigSection):
    updatetime = ConfigSetting(type=str, value=10)
    tmpdir = ConfigSetting(type=str, value=None)
    mumudvblogdir = ConfigSetting(type=str, value=None)
    mumudvbbindir = ConfigSetting(type=str, value=None)

#    if not os.path.isdir(tmpdir):
#        os.mkdirs(tmpdir)

#    if not os.path.isdir(mumudvblogdir):
#        os.mkdirs(mumudvblogdir)



