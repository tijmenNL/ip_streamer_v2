#!/usr/bin/env python

import argparse
import os
import signal
import sys

from application import log
from application.process import process, ProcessError

import ipstreamer

def main():
    name = 'ip-streamer'
    fullname = 'IP Streamer v2'
    version = ipstreamer.__version__
    runtime_directory = '/var/run/ip-streamer'
    system_config_directory = '/etc/vice'
    default_pid = os.path.join(runtime_directory, 'server.pid')
    default_config = ipstreamer.cfg_filename if os.path.isfile(ipstreamer.cfg_filename) else os.path.join(system_config_directory, ipstreamer.cfg_filename)

    parser = argparse.ArgumentParser(description='VICE ip streamer to control mumudvb.')
    parser.add_argument('--version', action='version', version='%s %s' % (fullname, version))
    parser.add_argument('--no-fork', action='store_false', dest='fork', default=True, help='run the process in the foreground')
    parser.add_argument('-c', '--config-file', dest='config_file', default=default_config, help='configuration file', metavar='FILE')
    parser.add_argument('-p', '--pid', dest='pid_file', default=default_pid, help='PID file', metavar='FILE')
    parser.add_argument('-d', '--debug', help='Run in debug mode', action='store_true', default=False, dest='debug')
    args = parser.parse_args()
    debug = args.debug

    path, cfg_file = os.path.split(args.config_file)
    if path:
        system_config_directory = path

    process.system_config_directory = system_config_directory
    ipstreamer.cfg_filename = process.config_file(cfg_file)

    # when run in foreground, do not require root access because of PID file in /var/run
    if args.fork:
        try:
            process.runtime_directory = runtime_directory
            process.daemonize(args.pid_file)
        except ProcessError, e:
            log.fatal("Cannot start %s: %s" % (fullname, e))
            sys.exit(1)
        log.start_syslog(name)

    if ipstreamer.cfg_filename:
        log.msg("Starting %s %s, config=%s" % (fullname, version, ipstreamer.cfg_filename))
    else:
        log.fatal("Starting %s %s, with no configuration file" % (fullname, version))
        sys.exit(1)

    try:
        from ipstreamer.server import IPStreamerDaemon
        server = IPStreamerDaemon()
    except Exception, e:
        log.fatal("failed to start %s" % fullname)
        log.err()
        sys.exit(1)

    def stop_server(*args):
        if not server.stopping:
            log.msg('Stopping %s...' % fullname)
            server.stop()

    def kill_server(*args):
        log.msg('Killing %s...' % fullname)
        os._exit(1)

    process.signals.add_handler(signal.SIGTERM, stop_server)
    process.signals.add_handler(signal.SIGINT, stop_server)

    try:
        server.start()
        while True:
            signal.pause()
            if server.stopping:
                break
        process.signals.add_handler(signal.SIGALRM, kill_server)
        signal.alarm(5)
        server.stop_event.wait(5)
        log.msg("%s stopped" % fullname)
    except Exception, e:
        log.fatal("failed to run %s" % fullname)
        log.err()
        sys.exit(1)


if __name__ == "__main__":
    main()