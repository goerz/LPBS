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

import shlex
import email
import subprocess
import os
from Config import full_expand

""" Notifications and Logging """

def notify(subject, job_id, message, options):
    """ Send notification
    """
    if options.config.getboolean("Notification", 'local_growl'):
        notify_local_growl(subject, job_id, message, options)


def notify_local_growl(subject, job_id, message, options):
    sticky = ''
    if options.config.getboolean("Growl", 'sticky'): sticky = '-s'
    p = subprocess.Popen([options.config.get("Growl", 'growlnotify'),
                          '-t', "LPBS: %s" % subject, sticky], 
                          stdin=subprocess.PIPE).stdin
    p.write(message)
    p.close()


def log(message, options):
    timestamp = email.Utils.formatdate(localtime=True)
    logfile = full_expand(os.path.join(os.environ['LPBS_HOME'], 
                                       options.config.get('LPBS', 'logfile')))
    try:
        log_fh = open(logfile, 'a')
        print >> log_fh, "%s  \t  %s" % (timestamp, message)
        log_fh.close()
    except IOError:
        pass
