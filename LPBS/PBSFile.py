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

""" Work with PBS script files """

import shlex
import logging

def set_options_from_pbs_script(arg_parser, options, pbs_script):
    """ Add directives in pbs_script to existing options, using arg_parser
    """
    opt_string = ''
    pbs_fh = open(pbs_script)
    for line in pbs_fh:
        if line.startswith('#!'):
            continue
        if line.strip() == (''):
            continue
        if not line.startswith('#PBS '):
            break
        opt_string += line.replace('#PBS', '', 1)
    pbs_fh.close()
    logging.debug("opt_string extracted from PBS file:\n%s", opt_string)
    argv = shlex.split(opt_string)
    options, args = arg_parser.parse_args(argv, options)

