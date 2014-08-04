########################################################################
#
# Predefined and dynamic variable list for the coNCePTuaL language
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2014, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2014).  Los Alamos National Security, LLC.  This software
# was produced under U.S. Government contract DE-AC52-06NA25396
# for Los Alamos National Laboratory (LANL), which is operated by
# Los Alamos National Security, LLC (LANS) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
# MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE. If software is modified to produce
# derivative works, such modified software should be clearly marked,
# so as not to confuse it with the version available from LANL.
# 
# Additionally, redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the
# following conditions are met:
# 
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer
#     in the documentation and/or other materials provided with the
#     distribution.
# 
#   * Neither the name of Los Alamos National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
#
########################################################################

import sys
import string
import getopt

class Variables:
    "List the variables that are special to the coNCePTuaL language."
    variables = {
        "bytes_sent"     : "Total number of bytes sent",
        "bytes_received" : "Total number of bytes received",
        "total_bytes"    : "Sum of bytes sent and bytes received",
        "msgs_sent"      : "Total number of messages sent",
        "msgs_received"  : "Total number of messages received",
        "total_msgs"     : "Sum of messages sent and messages received",
        "elapsed_usecs"  : "Elapsed time in microseconds",
        "bit_errors"     : "Total number of bit errors observed",
        "num_tasks"      : "Number of tasks running the program"
    }


# Enable an external script to dump a formatted version of the variable list.
if __name__ == '__main__':
    # Parse the command line.
    try:
        longopts = [
            "first=",
            "last="]
        opts, args = getopt.getopt(sys.argv[1:], "f:l:a:", longopts)
    except getopt.error:
        sys.stderr.write ("%s: bad option\n" % sys.argv[0])
        sys.exit(2)
    firstfmt = None
    lastfmt = None
    identity = lambda thing: thing
    if len(args) == 0:
        middlefmt = '%s\\n'
    else:
        middlefmt = args[0]
    for oneopt, onearg in opts:
        if oneopt in ("-f", "--first"):
            firstfmt = onearg
        if oneopt in ("-l", "--last"):
            lastfmt = onearg
    if not lastfmt:
        lastfmt = middlefmt
    if not firstfmt:
        firstfmt = middlefmt

    # Output a formatted variable list.
    sortedvars = Variables.variables.keys()
    sortedvars.sort()
    print eval('"%s"' % firstfmt) % (sortedvars[0], Variables.variables[sortedvars[0]]),
    for var in sortedvars[1:-1]:
        print eval('"%s"' % middlefmt) % (var, Variables.variables[var]),
    print eval('"%s"' % lastfmt) % (sortedvars[-1], Variables.variables[sortedvars[-1]]),
