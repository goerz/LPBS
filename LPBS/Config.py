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

""" Manage Configuration """

from ConfigParser import SafeConfigParser
import os
import sys
from StringIO import StringIO


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
send_mail: 0
send_growl: 0

[Mail]
from: nobody@example.org
smtp: smtp.example.com:587
username: user
password: secret
authenticate: 0
tls: 1

[Growl]
sticky: 1
hostname: localhost:23053
password: secret

[Log]
logfile: lpbs.log
""")

def get_config(config_file):
    """ Return an instance of ConfigParser.SafeConfigParser, loaded with the
        data in
        a) $LPBS_HOME/lpbs.cfg
        b) $HOME/.lpbs.cfg
        c) the specified config_file
    """
    config = SafeConfigParser()
    # Defaults
    config.readfp(DEFAULTS)
    config_files = []
    # $LPBS_HOME/lpbs.cfg
    if os.environ.has_key('LPBS_HOME'):
        global_config_file = os.path.join(os.environ['LPBS_HOME'], 'lpbs.cfg')
        if os.path.isfile(global_config_file):
            config_files.append(global_config_file)
    # $HOME/.lpbs.cfg
    if os.environ.has_key('HOME'):
        user_config_file = os.path.join(os.environ['HOME'], '.lpbs.cfg')
        if os.path.isfile(user_config_file):
            config_files.append(user_config_file)
    # Specified Config File
    try:
        if os.path.isfile(config_file):
            config_files.append(config_file)
    except TypeError:
        pass
    config.read(config_files)
    return config


def verify_lpbs_home():
    """ Verify existence and writability of LPBS_HOME. Try to create files as
        necessary
    """
    if not os.environ.has_key('LPBS_HOME'):
        print >> sys.stderr, "LPBS_HOME must be defined"
        return 1
    if not os.path.isdir(os.environ['LPBS_HOME']):
        print >> sys.stderr, "LPBS_HOME must be a directory"
        return 1
    if not os.access(os.environ['LPBS_HOME'], os.W_OK):
        print >> sys.stderr, "LPBS_HOME must be writable"
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

