# -*- coding: utf-8 -*-
############################################################################
#    Copyright (C) 2015 by Michael Goerz                                   #
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

from ConfigParser import SafeConfigParser, ParsingError
from ConfigParser import Error as ConfigParserError
import os
import sys
import re
from StringIO import StringIO


DEFAULTS = StringIO("""\
[Server]

# Full hostname of submission server (hostname.domain). Will be made available
# to running job through the environment variable PBS_SERVER. Job IDs will end
# in the server hostname

hostname: localhost
domain: local


[Node]

# Full hostname of the execution node (hostname.domain). Will be made available
# to running job through the environment variable PBS_O_HOST. Since LPBS is
# designed to execute jobs locally, the settings here should in general be
# identical to those in the [Server] section

hostname: localhost
domain: local


[LPBS]

# Setting for job execution.
# If 'username_in_jobid' is enabled, the job IDs will have the form
# 'seqnr.user.hostname.domain' where 'user' is the username of the user
# submitting the job.
# The file given in 'sequence_file' is used for keeping track of the 'seqnr'
# appearing in the job ID.
# The file given in 'logfile' is used for logging all LPBS events. Both
# 'sequence_file' and 'logfile' are relative to $LPBS_HOME.

username_in_jobid: 0
sequence_file: sequence
logfile: lpbs.log


[Scratch]

# Settings for the scratch space provided to jobs. 'scratch_root' defines a
# location where jobs should write temporary data. If given as a relative path,
# it is relative to $LPBS_HOME. Environment variables will be expanded at the
# time of the job submission.
# If the value of # 'create_jobid_folder' is set to 1, a folder with the name of
# the full job ID is created inside scratch_root. This folder is automatically
# deleted when the job ends, unless 'keep_scratch' is set to 1. If the job
# failed, the scratch will not be deleted, unless 'delete_failed_scratch' is set
# to 1.

scratch_root: $SCRATCH_ROOT
create_jobid_folder: 0
keep_scratch: 0
delete_failed_scratch: 0


[Notification]

# Settings on how the user should be be notified about events such as the start
# and end of a job. If sent_mail is set to 1, emails will be sent for
# notifications depending on the value of the '-m' option to lqsub. If
# 'send_growl' is set to 1, Growl (http://growl.info) is used for notification
# on MacOS X. Notifications via Growl do not take into account the '-m' options
# during job submission.

send_mail: 0
send_growl: 0


[Mail]

# SMTP settings for email notifications. Notification emails will be sent from
# the address given by the 'from' option. The SMTP server given in 'smtp' is
# used for sending the emails, if 'authenticate' is set to 1, authentication is
# done with the given 'username' and 'password'. If 'tls' is 1, TLS encryption
# will be used.

from: nobody@example.org
smtp: smtp.example.com:587
username: user
password: secret
authenticate: 0
tls: 1


[Growl]

# Settings for Growl notifications. Notifications are sent to either localhost
# or a remote host via the GNTP protocol. The 'hostname' setting gives the
# address and port of the Growl server, the given 'password' is used for
# authentication (note that if sending to localhost, no authentication is
# necessary). If 'sticky' is set to 1, the Growl notifications will be sticky.
# It is possible to send notifications to more than one host. In this case, both
# 'hostname' and 'password' should be a comma-separated list of values, with
# each item corresponding to one host.

hostname: localhost:23053
password:
sticky: 0


[Log]

# 'logfile' gives the name of the central log file, relative to $LPBS_HOME.

logfile: lpbs.log
""")


def verify_config(config):
    """ Verify that a config data structure conains all valid entries. For those
        entries that are not valid, print an error message and reset them to a
        default
    """
    try:
        for (section, key) in [('LPBS', 'username_in_jobid'),
        ('Scratch', 'create_jobid_folder'), ('Scratch', 'keep_scratch'),
        ('Scratch', 'delete_failed_scratch'), ('Notification', 'send_mail'),
        ('Notification', 'send_growl'), ('Mail', 'authenticate'),
        ('Mail', 'tls'), ('Growl', 'sticky')]:
            try:
                config.getboolean(section, key)
            except ValueError, error:
                config.set(section, key, 'false')
                print >> sys.stderr, "Illegal value for %s in Section %s." \
                        % (section, key)
                print >> sys.stderr, str(error)
                print >> sys.stderr, "Set %s to False" % key
        hostname = config.get('Server', 'hostname')
        if not re.match(r'^[A-Za-z0-9\-]+$', hostname):
            print >> sys.stderr, "Server hostname was %s, " % hostname,
            print >> sys.stderr, "must match '^[A-Za-z0-9\\-]+$'. " \
                                 "Set to 'localhost'."
            config.set('Server', 'hostname', 'localhost')
        domain = config.get('Server', 'domain')
        if not re.match(r'^[A-Za-z0-9\-\.]+$', domain):
            print >> sys.stderr, "Server domain was %s, " % hostname,
            print >> sys.stderr, "must match '^[A-Za-z0-9\\-\\.]+$'. " \
                                 "Set to 'local'."
            config.set('Server', 'domain', 'local')
        hostname = config.get('Node', 'hostname')
        if not re.match(r'^[A-Za-z0-9\-]+$', hostname):
            print >> sys.stderr, "Node hostname was %s, " % hostname,
            print >> sys.stderr, "must match '^[A-Za-z0-9\\-]+$'. " \
                                 "Set to 'localhost'."
            config.set('Node', 'hostname', 'localhost')
        domain = config.get('Node', 'domain')
        if not re.match(r'^[A-Za-z0-9\-\.]+$', domain):
            print >> sys.stderr, "Node domain was %s, " % hostname,
            print >> sys.stderr, "must match '^[A-Za-z0-9\\-\\.]+$'. " \
                                 "Set to 'local'."
            config.set('Node', 'domain', 'local')
    except ConfigParserError, error:
        print >> sys.stderr, "Unrecoverable error in config data:"
        print >> sys.stderr, str(error)
        sys.exit(1)


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
    try:
        config.read(config_files)
    except ParsingError, error:
        print >> sys.stderr, str(error)

    verify_config(config)
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

