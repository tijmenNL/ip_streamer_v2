from application.configuration import ConfigSection, ConfigSetting
from sipsimple.configuration.datatypes import Port

from ipstreamer import cfg_filename
import os

class GeneralConfiguration(ConfigSection):
    __cfgfile__ = cfg_filename
    __section__ = 'settings'

    server   = ConfigSetting(type=str, value=None)
    port = ConfigSetting(type=Port, value=8088)
    role_port = ConfigSetting(type=Port, value=8765)
    vice_server = 'http://' + server + ':' + port


class MumuConfiguration(ConfigSection):
    updatetime = ConfigSetting(type=str, value=10)
    tmpdir = ConfigSetting(type=str, value=None)
    mumudvblogdir = ConfigSetting(type=str, value=None)
    mumudvbbindir = ConfigSetting(type=str, value=None)

    if not os.isdir(tmpdir):
        os.mkdirs(tmpdir)

    if not os.isdir(mumudvblogdir):
        os.mkdirs(mumudvblogdir)



