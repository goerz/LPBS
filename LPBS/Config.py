# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2011 by Michael Goerz                                   #
#    http://michaelgoerz.net                                               #
#                                                                          #
#    This program is free software; you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 3 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

from ConfigParser import SafeConfigParser
import os
import sys
import socket
from StringIO import StringIO

""" Manage Configuration """

DEFAULTS = StringIO("""\
[Server]
hostname: localhost
domain: local

[Node]
hostname: localhost
domain: local

[LPBS]
username_in_jobid: 0
sequence_file: sequence
logfile: lpbs.log

[Scratch]
scratch_root: $SCRATCH_ROOT
create_jobid_folder: 1
keep_scratch: 0
delete_failed_scratch: 0

[Notification]
send_mail: 1
local_growl: 1
remote_growl: 0
write_to_log: 0
write_to_mbox: 0

[Mail]
from: nobody@example.org
smtp: smtp.example.com:587
username: user
password: secret
tls: 1

[Growl]
sticky: 1
growlnotify: growlnotify

[Log]
notification_log: notification.log
logfile: lpbs.log

[mbox]
mboxfile: lpbs.mbox
""")

def get_config(config_file):
    """ Return an instance of ConfigParser.SafeConfigParser, loaded with the
        data in config_file
    """
    config = SafeConfigParser()
    config.readfp(DEFAULTS)
    if config_file is None:
        if os.environ.has_key('LPBS_HOME'):
            config_file = os.path.join(os.environ['LPBS_HOME'], 'lpbs.cfg')
        else:
            print >>sys.stderr, "LPBS_HOME is not defined"
    try:
        if os.path.isfile(config_file):
            config.read(config_file)
        else:
            print >>sys.stderr, "%s does not exist" % config_file
    except TypeError:
        print >>sys.stderr, "Cannot read config file, using default values"
    return config


def verify_lpbs_home():
    """ Verify existence and writability of LPBS_HOME. Try to create files as
        necessary
    """
    if not os.environ.has_key('LPBS_HOME'):
        print >>sys.stderr, "LPBS_HOME must be defined"
        return 1
    if not os.path.isdir(os.environ['LPBS_HOME']):
        print >>sys.stderr, "LPBS_HOME must be a directory"
        return 1
    if not os.access(os.environ['LPBS_HOME'], os.W_OK):
        print >>sys.stderr, "LPBS_HOME must be writable"
        return 1
    configfile = os.path.join(os.environ['LPBS_HOME'], 'lpbs.cfg')
    if not os.path.isfile(configfile):
        configfile_fh = open(configfile, 'w')
        configfile_fh.write(DEFAULTS.getvalue())
        configfile_fh.close()
    return 0


def full_expand(path_string):
    """ Combination of os.path.expanduser and os.path.expandvars """
    return os.path.expanduser(os.path.expandvars(path_string))

