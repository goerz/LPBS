# LPBS

[http://github.com/goerz/LPBS](http://github.com/goerz/LPBS)

Author: [Michael Goerz](http://michaelgoerz.net)

Local Portable Batch System: Emulating PBS on a local workstation

This code is licensed under the [GPL](http://www.gnu.org/licenses/gpl.html)

[PBS][1]/[TORQUE][2] is a job scheduling system that is used on many high
performance computing clusters. The LPBS package provides tools to run PBS job
scripts on a local workstation. Specifically, LPBS provides the `lqsub` command
that takes the same options as the PBS `qsub` command and runs a job script
locally, in an environment virtually identical to one that PBS/TORQUE would
provide. The job will run in the background and be assigned a job ID.  Unlike
the PBS system, LPBS will not perform any scheduling, but will simply run the
job submitted to it. LPBS provides further tools to manage running jobs.

[1]: http://en.wikipedia.org/wiki/Portable_Batch_System
[2]: http://en.wikipedia.org/wiki/TORQUE_Resource_Manager


## Installation ##

LPBS can be install from PyPi, using

    pip install LPBS

Alternatively, the package can be installed from source with

    python setup.py install


## Configuration ##

LPBS stores all its configuration and runtime data in the folder given in the
environment variable `$LPBS_HOME`. This environment variable *must* be defined.
The configuration is in the file `lpbs.cfg` inside `$LPBS_HOME`. If this file
does not exist when any of the LPBS scripts are run, a configuration file with
the following default values will be created:

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

    # Settings for Growl notifications. Notifications are sent to either
    # localhost or a remote host via the GNTP protocol. The 'hostname' setting
    # gives the address and port of the Growl server, the given 'password' is
    # used for authentication (note that if sending to localhost, no
    # authentication is necessary, and the password should be empty). If
    # 'sticky' is set to 1, the Growl notifications will be sticky.  It is
    # possible to send notifications to more than one host. In this case, both
    # 'hostname' and 'password' should be a comma-separated list of values, with
    # each item corresponding to one host. E.g.
    # hostname: localhost, remotehost
    # password: , secret

    hostname: localhost:23053
    password:
    sticky: 0


    [Log]

    # 'logfile' gives the name of the central log file, relative to $LPBS_HOME.

    logfile: lpbs.log

Note that if the default config file is used, the environment variable
`$SCRATCH_ROOT` must be defined and the directory it points to should exist and
be writable to all users who might submit jobs.

For a system-wide installation, `/var/lpbs` is a suitable location for
`$LPBS_HOME`. The environment variable can be set in `/etc/bash.bashrc` for all
users. For an installation in user space, [virtualenv][3] is recommended.

After the main config file, the file `$HOME/.lpbs.cfg` will also be read. A user
can use this to override settings in the system configuration. Lastly, the
`qsub` command also has a `--config` option that allows to specify yet an
additional config file to be read.

[3]: http://pypi.python.org/pypi/virtualenv


## Usage ##

LPBS contains the scripts `lqsub`, `lqstat`, and `lqdel`, which emulate the
PBS/TORQUE commands `qsub`, `qstat`, and `lqdel`, respectively. The `lqsub`
command is used to submit jobs, `lqstat` is used to show information about
running jobs, and `lqdel` is used to abort running jobs. For example:

    goerz@localhost:~> lqsub job.pbs
    3.localhost.local

    goerz@localhost:~> lqstat
    Job id               Name            User            Walltime
    -------------------- --------------- --------------- ---------------
    3.localhost.local    pbstest         goerz           0:00:22

    goerz@localhost:~> lqstat -f 3.localhost.local
    Job Id: 3.localhost.local
        Job_Name = pbstest
        Job_Owner = goerz
        server = localhost.local
        exec_host = localhost.local
        PID = 14649
        Error_Path = STDERR
        Join_Path = True
        Mail_Points = n
        Output_Path = pbstest.out
        resources_used.walltime = 0:00:43

    goerz@localhost:~> lqdel 3.localhost.local

The `qsub` command is designed to understand all command line options of the
`qsub` command in TORQUE version 2.18, except that all options related to
scheduling are silently ignored. Hence, all PBS job script should be submittable
without change. For details, run `lqsub`, `lqstat`, and `lqdel` with the
`--help` option, and/or look at the [TORQUE manual][4].

[4]: http://www.clusterresources.com/torquedocs21/index.shtml


## An Example Job Script ##

The following is an example of a simple PBS job script that will print out the
full environment that the job sees. You may want to submit this job both with
LPBS and PBS/TORQUE to verify that with appropriate settings in `lpbs.cfg`, LPBS
provides an identical environment as LPBS.


    #!/bin/bash
    #PBS -N pbstest
    #PBS -j oe
    #PBS -l nodes=1:ppn=1
    #PBS -l walltime=00:00:10
    #PBS -l mem=10mb
    #PBS -o pbstest.out

    echo "####################################################"
    echo "User: $PBS_O_LOGNAME"
    echo "Batch job started on $PBS_O_HOST"
    echo "PBS job id: $PBS_JOBID"
    echo "PBS job name: $PBS_JOBNAME"
    echo "PBS working directory: $PBS_O_WORKDIR"
    echo "Job started on" `hostname` `date`
    echo "Current directory:" `pwd`
    echo "PBS environment: $PBS_ENVIRONMENT"
    echo "####################################################"

    echo "####################################################"
    echo "Full Environment:"
    printenv
    echo "####################################################"

    echo "The Job is being executed on the following node:"
    cat ${PBS_NODEFILE}
    echo "##########################################################"

    echo "Job Finished: " `date`
    exit 0

