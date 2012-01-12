#! /usr/bin/env python

########################################################################
#
# Visually replay trace data generated using the c_trace backend
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
# Copyright (C) 2012, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2012).  Los Alamos National Security, LLC.  This software
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
import os
import string
import re
import getopt
import curses

# Define some global variables
progname = os.path.basename(sys.argv[0]) # This program's name
tracefilename = None                     # File containing trace data
delayms = 0                              # Delay in msecs after screen updates
monitortask = 0                          # Physical task ID to monitor
breakpoint = -1                          # Line number at which to single-step
sourcefilename = None                    # File containing coNCePTuaL source

# Summarize program usage.
def usage(exitcode):
    "Provide a usage message."
    print "Usage: %s [--help] [--trace=<file>] [--delay=<msec>] [--monitor=<task ID>] [--breakpoint=<line#>] <source.ncptl>" % progname
    sys.exit(exitcode)

# Parse the command line.
try:
    longopts = [
        "help",
        "trace=",
        "delay=",
        "monitor=",
        "breakpoint="]
    opts, args = getopt.getopt(sys.argv[1:], "hT:D:M:P:", longopts)
except getopt.error:
    sys.stderr.write("%s: bad option\n" % progname)
    sys.exit(1)
try:
    for opt, optarg in opts:
        if opt in ("-h", "--help"):
            usage(0)
        elif opt in ("-T", "--trace"):
            tracefilename = optarg
        elif opt in ("-D", "--delay"):
            delayms = int(optarg)
        elif opt in ("-M", "--monitor"):
            monitortask = int(optarg)
        elif opt in ("-B", "--breakpoint"):
            breakpoint = int(optarg)
        else:
            usage(1)
    if delayms<0 or monitortask<0:
        raise ValueError
except ValueError:
    sys.stderr.write('%s: %s expects a nonnegative integer but was given "%s"\n' %
                     (progname, opt, optarg))
    sys.exit(1)
if (len(args) != 1):
    usage(1)
sourcefilename = args[0]

# Open all of our input files.
try:
    if (tracefilename):
        tracefile = open(tracefilename, "r")
    else:
        tracefile = sys.stdin
    sourcefile = open(sourcefilename, "r")
except IOError, errmsg:
    sys.stderr.write('%s: %s\n' % (progname, errmsg))
    sys.exit(1)
sourcecode = string.split(re.sub(r'\n+$', "", sourcefile.read()), "\n")

# Initialize curses.
win = curses.initscr()
curses.cbreak()
curses.noecho()
if hasattr(curses, "curs_set"):
    # The following call is not defined in Python 1.5.
    curses.curs_set(0)
if delayms > 25500:
    delayms = 25500
if delayms>0 and hasattr(curses, "halfdelay"):
    curses.halfdelay((delayms+99) / 100)
else:
    win.nodelay(1)
    delayms = 0
lines, cols = win.getmaxyx()
for cline in range(0, len(sourcecode)):
    if cline >= lines-1:
        break
    win.addstr(cline, 0, "%3d.  " % (cline+1), curses.A_BOLD)
    win.addstr(sourcecode[cline][:cols-6], curses.A_NORMAL)
win.refresh()

# Process the trace file line-by-line.
taskdigits = len(str(monitortask))
actionlen = 7
eventdigits = 1
prevfirstline = -1
win.addstr(lines-1, 0,
           "Phys: %s  Virt: %s  Action: %s  Event: %s %s" %
           (" "*taskdigits, " "*taskdigits,
            " "*actionlen,
            " "*eventdigits, " "*eventdigits),
           curses.A_BOLD)
win.refresh()
while 1:
    # Parse a line of the trace file.
    oneline = tracefile.readline()
    if oneline == "":
        break
    fields = re.match(r'\[TRACE\] phys: (\d+) \| virt: (\d+) \| action: (\w+) \| event: (\d+) / (\d+) \| lines: (\d+) - (\d+)',
                      oneline)
    if not fields:
        continue
    physrank_str, virtrank_str, action_str, eventnum_str, numevents_str, firstline_str, lastline_str = fields.groups()
    physrank = int(physrank_str)
    if physrank != monitortask:
        continue
    virtrank = int(virtrank_str)
    eventnum = int(eventnum_str)
    numevents = int(numevents_str)
    firstline = int(firstline_str) - 1
    lastline = int(lastline_str) - 1
    if taskdigits < len(physrank_str):
        taskdigits = len(physrank_str)
    if taskdigits < len(virtrank_str):
        taskdigits = len(virtrank_str)
    if actionlen < len(action_str):
        actionlen = len(action_str)
    if eventdigits < len(numevents_str):
        eventdigits = len(numevents_str)

    # Display the currently active line and update the status line.
    win.addstr(lines-1, 0,
               "Phys: %s  Virt: %s  Action: %s  Event: %s %s" %
               (" "*taskdigits, " "*taskdigits,
                " "*actionlen,
                " "*eventdigits, " "*eventdigits),
               curses.A_BOLD)
    win.addstr(lines-1, 6,
               ("%"+str(taskdigits)+"d") % monitortask)
    win.addstr(lines-1, 14+taskdigits,
               ("%"+str(taskdigits)+"d") % virtrank)
    win.addstr(lines-1, 24+2*taskdigits,
               ("%-"+str(actionlen)+"s") % action_str)
    win.addstr(lines-1, 33+2*taskdigits+actionlen,
               ("%"+str(eventdigits)+"d") % eventnum)
    win.addstr(lines-1, 33+2*taskdigits+actionlen+eventdigits,
               ("/%"+str(eventdigits)+"d") % numevents)
    if firstline != prevfirstline:
        if prevfirstline>=0 and prevfirstline<lines-1:
            win.addstr(prevfirstline, 6, sourcecode[prevfirstline][:cols-7])
        if firstline>=0 and firstline<lines-1:
            win.addstr(firstline, 6, sourcecode[firstline][:cols-7], curses.A_STANDOUT)
        prevfirstline = firstline
    win.refresh()

    # Process keyboard commands.
    if (eventnum==1 and breakpoint==0) or (breakpoint==firstline+1):
        # Enter single-stepping mode.
        curses.nocbreak()
        curses.cbreak()
        win.nodelay(0)
    onechar = win.getch()
    if onechar == -1:
        continue
    onechar = chr(onechar)
    if string.upper(onechar) == "S":
        # Enter single-stepping mode.
        curses.nocbreak()
        curses.cbreak()
        win.nodelay(0)
    elif onechar == ' ':
        # Restore normal execution mode.
        if delayms>0 and hasattr(curses, "halfdelay"):
            curses.halfdelay((delayms+99) / 100)
        else:
            win.nodelay(1)
    elif string.upper(onechar) == "D":
        # Delete the breakpoint.
        breakpoint = -1
    elif string.upper(onechar) == "Q":
        # Abort the program.
        break

# Finish up cleanly.
if (tracefilename):
    tracefile.close()
sourcefile.close()
curses.endwin()
