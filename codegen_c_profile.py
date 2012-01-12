#! /usr/bin/env python

########################################################################
#
# Event-profiling module for the coNCePTuaL compiler:
# Profiles any module derived from codegen_c_generic
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
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
import re
import types
import new
from ncptl_error import NCPTL_Error

class NCPTL_CodeGen:
    def __init__(self, options):
        "Initialize the profiling module."
        self.backend_name = "c_profile"
        self.errmsg = NCPTL_Error(self.backend_name)

        # Process any arguments we were given.
        leftover_opts = []
        target_backend = ""
        for arg in range(0, len(options)):
            profile_match = re.match(r'--profile=(.*)', options[arg])
            if profile_match:
                target_backend = profile_match.group(1)
            elif options[arg] == "--help":
                # Utilize c_generic's help-string mechanism.
                import codegen_c_generic
                generic_self = codegen_c_generic.NCPTL_CodeGen()
                generic_self.backend_name = self.backend_name
                generic_self.cmdline_options.extend([
                    ("--profile=<string>", "Specify a backend to profile")])
                generic_self.show_help()
                raise SystemExit, 0
            else:
                leftover_opts.append(options[arg])
        if not target_backend:
            self.errmsg.error_fatal("a target backend must be specified using --profile")

        # Reparent ourselves to the profiled backend.
        try:
            exec("import codegen_%s" % target_backend)
            exec("immediate_ancestor = codegen_%s.NCPTL_CodeGen" %
                 target_backend)
        except:
            self.errmsg.error_fatal("Unable to initialize the %s backend" % target_backend)
        try:
            self.name2class[target_backend] = immediate_ancestor
        except AttributeError:
            self.name2class = {target_backend: immediate_ancestor}
        try:
            self.name2class["c_profile"].__bases__ = (immediate_ancestor,)
        except KeyError:
            # We're the top-level class.
            self.__class__.__bases__ = (immediate_ancestor,)
            self.name2class["c_profile"] = self.__class__
        self.c_profile_parent = self.name2class["c_profile"].__bases__[0]
        immediate_ancestor.__init__(self, leftover_opts)
        self.define_eventnames = 1
        self.backend_name = "c_profile + " + self.backend_name
        self.backend_desc = "event profiler atop " + self.backend_desc


    # ---------------------- #
    # (Re)implementation of  #
    # hook and other methods #
    # ---------------------- #

    def code_declare_globals_EXTRA(self, localvars):
        "Declare a few arrays to store profile data."
        newcode = self.invoke_hook("code_declare_globals_EXTRA", localvars,
                                   invoke_on=self.c_profile_parent)
        self.code_declare_var(name="profeventtimings", arraysize="EV_CODE+1",
                              type="static ncptl_int",
                              comment="Total time spent in each event",
                              stack=newcode)
        self.code_declare_var(name="profeventtallies", arraysize="EV_CODE+1",
                              type="static ncptl_int",
                              comment="Number of times each event was executed",
                              stack=newcode)
        return newcode

    def code_define_main_POST_INIT(self, localvars):
        "Initialize the profile data."
        newcode = self.invoke_hook("code_define_main_POST_INIT", localvars,
                                   invoke_on=self.c_profile_parent)
        self.push("memset ((void *)profeventtimings, 0, sizeof(ncptl_int)*(EV_CODE+1));", newcode);
        self.push("memset ((void *)profeventtallies, 0, sizeof(ncptl_int)*(EV_CODE+1));", newcode);
        return newcode

    def code_def_procev_EVENTS_DECL(self, localvars):
        "Declare a variable for storing an event starting time."
        newcode = self.invoke_hook("code_def_procev_EVENTS_DECL", localvars,
                                   invoke_on=self.c_profile_parent)
        self.code_declare_var(name="eventtype", rhs="thisev->type",
                              comment="Preserved copy of thisev->type in case EV_REPEAT alters thisev",
                              stack=newcode)
        self.code_declare_var(name="eventstarttime", rhs="ncptl_time()",
                              comment="Time at which the current event began executing",
                              stack=newcode)
        return newcode

    def code_def_procev_POST_SWITCH(self, localvars):
        "Accumulate the time taken by the current event."
        newcode = self.invoke_hook("code_def_procev_POST_SWITCH", localvars,
                                   invoke_on=self.c_profile_parent)
        self.push("profeventtimings[eventtype] += ncptl_time() - eventstarttime;",
                  stack=newcode)
        self.push("profeventtallies[eventtype]++;", stack=newcode)
        return newcode

    def code_def_finalize_DECL(self, localvars):
        "Allocate variables needed to write the profiling information."
        newcode = self.invoke_hook("code_def_finalize_DECL", localvars,
                                   invoke_on=self.c_profile_parent)
        if self.program_uses_log_file:
            self.code_declare_var(type="char", name="profilekey", arraysize="256",
                                  comment="Space to hold an event name",
                                  stack=newcode)
            self.code_declare_var(type="char", name="profilevalue", arraysize="256",
                                  comment="Space to hold a line of profile information",
                                  stack=newcode)
        self.profloopvar = self.code_declare_var(type="int", suffix="ev",
                                                 comment="Loop over event types",
                                                 stack=newcode)
        self.code_declare_var(name="numevents",
                              rhs="ncptl_queue_length (eventqueue)",
                              comment="Total number of events processed",
                              stack=newcode)
        return newcode

    def code_def_finalize_PRE(self, localvars):
        "Write profiling information to either stderr or a log file."
        newcode = self.invoke_hook("code_def_finalize_PRE", localvars,
                                   invoke_on=self.c_profile_parent)
        profloopvar = self.profloopvar
        if self.program_uses_log_file:
            # Write to the log file.
            self.pushmany([
                "for (%s=0; %s<NUM_EVS; %s++)" % ((profloopvar,) * 3),
                "if (profeventtallies[%s]) {" % profloopvar,
                'sprintf (profilekey, "Profile of %%s (microseconds, count, average)", eventnames[%s]);' % profloopvar,
                'sprintf (profilevalue, "%%" NICS " %%" NICS " %%.1f", profeventtimings[%s], profeventtallies[%s], (double)profeventtimings[%s]/(double)profeventtallies[%s]);' %
                ((profloopvar,) * 4),
                "ncptl_log_add_comment (profilekey, profilevalue);",
                "}",
                'strcpy (profilekey, "Profile of event memory");',
                'sprintf (profilevalue, "%" NICS " bytes (%" NICS " events * %" NICS " bytes/event)",'
                "numevents*sizeof(CONC_EVENT), numevents, (ncptl_int)sizeof(CONC_EVENT));",
                "ncptl_log_add_comment (profilekey, profilevalue);"],
                          stack=newcode)
        else:
            # Write to the standard error device.
            self.pushmany([
                "for (%s=0; %s<NUM_EVS; %s++)" % ((profloopvar,) * 3),
                "if (profeventtallies[%s]) {" % profloopvar,
                'fprintf (stderr, "%%d %%s %%" NICS " %%" NICS " %%.1f\\n", physrank, eventnames[%s], profeventtimings[%s], profeventtallies[%s], (double)profeventtimings[%s]/(double)profeventtallies[%s]);' %
                (profloopvar, profloopvar, profloopvar, profloopvar, profloopvar),
                "}",
                'fprintf (stderr, "%d event-memory %" NICS " %" NICS " %" NICS "\n",',
                "physrank, numevents*sizeof(CONC_EVENT), numevents, (ncptl_int)sizeof(CONC_EVENT));"],
                          stack=newcode)
        return newcode
