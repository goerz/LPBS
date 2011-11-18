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

""" Manage Job IDs """

import os
import sys
import signal
import logging
from glob import glob

def get_new_job_id(options):
    sequencefile = os.path.join(os.environ['LPBS_HOME'], 
                                options.config.get('LPBS', 'sequence_file'))
    # read previous sequence number and up-one
    try:
        sequencefile_fh = open(sequencefile, 'r')
        sequence = int(sequencefile_fh.read())
        sequencefile_fh.close()
    except IOError, e:
        print >> sys.stderr, "Could not read from %s:\n%s" % (sequencefile, e)
        return None
    sequence = sequence + 1
    # write new sequence number back to sequence file
    try:
        sequencefile_fh = open(sequencefile, 'w')
        sequencefile_fh.write(str(sequence))
        sequencefile_fh.close()
    except IOError, e:
        print >> sys.stderr, "Could not write to %s:\n%s" % (sequencefile, e)
        return None
    id_host = options.config.get("Server", 'hostname')
    id_domain = options.config.get("Server", 'domain')
    if options.config.getboolean('LPBS', 'username_in_jobid'):
        return "%s.%s.%s.%s" \
                % (sequence, id_host, id_domain, os.environ['USER'])
    else:
        return "%s.%s.%s" % (sequence, id_host, id_domain)


def set_lock(job_id, pid):
    lockfile = os.path.join(os.environ['LPBS_HOME'], "%s.lock" % job_id) 
    lock = open(lockfile, 'w')
    lock.write(str(pid))
    lock.close()


def release_lock(job_id):
    lockfile = os.path.join(os.environ['LPBS_HOME'], "%s.lock" % job_id) 
    try:
        os.unlink(lockfile)
    except OSError:
        pass


def pid_for_job_id(job_id):
    """ For a given Job_ID, return the process ID, or None if the given job id
        does not exist or is not accessible
    """
    lock_files = glob(os.path.join(os.environ['LPBS_HOME'], '*.lock'))
    for lock_file in lock_files:
        if os.path.basename(lock_file).startswith(job_id):
            try:
                fh = open(lock_file)
                pid = fh.read()
                fh.close()
                return(int(pid))
            except IOError:
                return None
    return None


def send_sig_to_job_id(job_id, sig=signal.SIGTERM):
    """ Send a sig to the given job id """
    pid = pid_for_job_id(job_id)
    if pid is not None:
        try:
            os.kill(pid, sig)
            logging.info("Sent signal %s to job %s (PID %s)"
                         % (sig, job_id, pid))
        except OSError:
            pass
