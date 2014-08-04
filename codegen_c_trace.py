########################################################################
#
# Execution-tracing module for the coNCePTuaL compiler:
# Traces any module derived from codegen_c_generic
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
import re
import types
import new
from ncptl_error import NCPTL_Error

class NCPTL_CodeGen:
    def __init__(self, options):
        "Initialize the execution-trace module."
        self.backend_name = "c_trace"
        self.errmsg = NCPTL_Error(self.backend_name)

        # Process any arguments we were given.
        leftover_opts = []
        target_backend = ""
        self.use_curses = 0
        for arg in range(0, len(options)):
            trace_match = re.match(r'--trace=(.*)', options[arg])
            if trace_match:
                target_backend = trace_match.group(1)
            elif options[arg] == "--curses":
                self.use_curses = 1
            elif options[arg] == "--help":
                # Utilize c_generic's help-string mechanism.
                import codegen_c_generic
                generic_self = codegen_c_generic.NCPTL_CodeGen()
                generic_self.backend_name = self.backend_name
                generic_self.cmdline_options.extend([
                    ("--trace=<string>", "Specify a backend to trace"),
                    ("--curses",
                     """Display the trace with curses instead of with
                                  fprintf()""")])
                generic_self.show_help()
                raise SystemExit, 0
            else:
                leftover_opts.append(options[arg])
        if not target_backend:
            self.errmsg.error_fatal("a target backend must be specified using --trace")

        # Reparent ourselves to the traced backend.
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
            self.name2class["c_trace"].__bases__ = (immediate_ancestor,)
        except KeyError:
            # We're the top-level class.
            self.__class__.__bases__ = (immediate_ancestor,)
            self.name2class["c_trace"] = self.__class__
        self.c_trace_parent = self.name2class["c_trace"].__bases__[0]
        immediate_ancestor.__init__(self, leftover_opts)
        self.intercept_node_funcs(self.name2class["c_trace"])
        if self.use_curses:
            self.set_param("LIBS", "prepend", "-lcurses")
        self.define_eventnames = 1
        self.backend_name = "c_trace + " + self.backend_name
        self.backend_desc = "event tracer atop " + self.backend_desc

        # Add a command-line option to specify which task should be monitored.
        if self.use_curses:
            self.base_global_parameters.extend([("NCPTL_TYPE_INT",
                                                 "cursestask",
                                                 "monitor",
                                                 "M",
                                                 "Processor to monitor",
                                                 "0"),
                                                ("NCPTL_TYPE_INT",
                                                 "cursesdelay",
                                                 "delay",
                                                 "D",
                                                 "Delay in milliseconds after each screen update (0=no delay)",
                                                 "0"),
                                                ("NCPTL_TYPE_INT",
                                                 "breakpoint",
                                                 "breakpoint",
                                                 "B",
                                                 "Source line at which to enter single-stepping mode (-1=none; 0=first event)",
                                                 "-1")])

    def intercept_node_funcs(self, someclass):
        """
           Modify all of the n_* methods (except hooks) in a class
           and all its parent classes so as to invoke store_node
           before doing anything else.
        """
        for baseclass in someclass.__bases__:
            self.intercept_node_funcs(baseclass)
        for method_name, method_body in someclass.__dict__.items():
            if self.__class__.__dict__.has_key(method_name):
                # The n_* methods defined in this file already do the
                # equivalent of store_node so there's no need to
                # modify them.
                continue
            if type(method_body)==types.FunctionType and re.match(r'n_[a-z_]+$', method_name):
                # Closure kludge -- work around Python's lack of true
                # closures (and lack of anything even remotely like a
                # closure in Python 1.5).
                class CloKlu:
                    def __init__(self, trueself, method_name, method_body):
                        self.trueself = trueself
                        self.method_name = method_name
                        self.method_body = method_body
                        setattr(trueself, method_name, self.store_node)

                    def store_node(self, node):
                        self.trueself.current_node = node
                        return self.method_body(self.trueself, node)
                CloKlu(self, method_name, method_body)


    # ---------------------- #
    # (Re)implementation of  #
    # hook and other methods #
    # ---------------------- #

    def code_specify_include_files_POST(self, localvars):
        "Specify extra header files needed by the c_trace backend."
        includefiles = self.invoke_hook("code_specify_include_files_POST",
                                        localvars, invoke_on=self.c_trace_parent)
        if self.use_curses:
            self.push("#include <curses.h>", includefiles)
        return includefiles

    def code_declare_datatypes_EXTRA_EVENT_STATE(self, localvars):
        "Declare some extra tracing state to attach to each event."
        newdecls = []
        self.code_declare_var(type="int", name="virtrank",
                              comment="Task's current virtual rank",
                              stack=newdecls)
        self.code_declare_var(type="int", name="firstline",
                              comment="First line of source code corresponding to this event",
                              stack=newdecls)
        self.code_declare_var(type="int", name="lastline",
                              comment="Last line of source code corresponding to this event",
                              stack=newdecls)
        newdecls = newdecls + self.invoke_hook("code_declare_datatypes_EXTRA_EVENT_STATE",
                                               localvars, invoke_on=self.c_trace_parent)
        return newdecls

    def code_def_alloc_event_POST(self, localvars):
        "Add some tracing data to every event."
        return ([
            "newevent->virtrank = virtrank;",
            "newevent->firstline = currentline[0];",
            "newevent->lastline = currentline[1];"] +
                self.invoke_hook("code_def_alloc_event_POST", localvars,
                                 invoke_on=self.c_trace_parent))

    def code_def_procev_EVENTS_DECL(self, localvars):
        "Declare extra variables needed within the main loop by the c_trace backend."
        newdecls = []
        if self.use_curses:
            self.code_declare_var(type="static int", name="prevsrcline", rhs="-1",
                                  comment="Previously executed source-code line",
                                  stack=newdecls)
        return newdecls + self.invoke_hook("code_def_procev_EVENTS_DECL",
                                           localvars, invoke_on=self.c_trace_parent)


    def code_define_main_PRE_EVENTS(self, localvars):
        "Prepare curses for the main event loop."
        newcode = self.invoke_hook("code_define_main_PRE_EVENTS",
                                   localvars, invoke_on=self.c_trace_parent)
        self.push("totalevents = numevents;", newcode);
        if self.use_curses:
            self.push("if (physrank == cursestask) {", newcode)
            self.code_declare_var(name="numevs",
                                  comment="Mutable version of numevents",
                                  stack=newcode)
            self.code_declare_var(name="numtasks",
                                  comment="Mutable version of var_num_tasks",
                                  stack=newcode)
            self.pushmany([
                "if (numevents)",
                "for (numevs=numevents, eventdigits=0; numevs; numevs/=10, eventdigits++)",
                ";",
                "for (numtasks=var_num_tasks-1, taskdigits=0; numtasks; numtasks/=10, taskdigits++)",
                ";",
                "(void) attrset (A_BOLD);",
                'mvprintw (LINES-1, 0, "Phys: %%*s  Virt: %%*s  Action: %%%ds  Event: %%-*s/%%-*s",' %
                self.event_string_len,
                'taskdigits, "", taskdigits, "", "", eventdigits, "", eventdigits, "");',
                "(void) attrset (A_NORMAL);",
                'mvprintw (LINES-1, 6, "%*d", taskdigits, physrank);',
                'mvprintw (LINES-1, %d+2*taskdigits+eventdigits, "/%%*" NICS, eventdigits, numevents);' %
                (33+self.event_string_len),
                "}"],
                          stack=newcode)
        return newcode

    def code_def_procev_PRE_SWITCH(self, localvars):
        "Output a trace message or update the screen before processing an event."
        newcode = []
        if self.use_curses:
            self.event_string_len = 0
            for evstr in self.events_used.keys():
                if self.event_string_len < len(evstr)-3:
                    self.event_string_len = len(evstr)-3
            self.pushmany([
                "if (physrank == cursestask) {",
                " /* Indicate which source-code line is currently active. */",
                "if (thisev->firstline-1 != prevsrcline) {",
                "mvchgat (prevsrcline, 6, -1, A_NORMAL, 0, NULL);",
                "(void) touchline (curseswin, prevsrcline, 1);",
                "if (thisev->firstline-1>=0 && thisev->firstline-1<LINES-1) {",
                "mvchgat (thisev->firstline-1, 6, -1, A_STANDOUT, 0, NULL);",
                "(void) touchline (curseswin, thisev->firstline-1, 1);",
                "}",
                "prevsrcline = thisev->firstline - 1;",
                "}",
                "",
                " /* Display other useful trace information. */",
                'mvprintw (LINES-1, 14+taskdigits, "%*d", taskdigits, thisev->virtrank);',
                'mvprintw (LINES-1, 24+2*taskdigits, "%%-%ds", eventnames[thisev->type]);' %
                self.event_string_len,
                'mvprintw (LINES-1, %d+2*taskdigits, "%%*" NICS, eventdigits, i+1);' %
                (33+self.event_string_len),
                "",
                " /* Update the screen and process keyboard commands. */",
                "(void) refresh ();",
                "if ((i==0 && breakpoint==0) || ((int)breakpoint==thisev->firstline)) {",
                " /* Enable single-stepping mode. */",
                "(void) nocbreak();",
                "(void) cbreak();",
                "(void) nodelay (curseswin, FALSE);",
                "}",
                "switch (getch()) {",
                "case 's':",
                "case 'S':",
                " /* Enable single-stepping mode. */",
                "(void) nocbreak();",
                "(void) cbreak();",
                "(void) nodelay (curseswin, FALSE);",
                "break;",
                "",
                "case ' ':",
                " /* Enable normal execution mode. */",
                "if (cursesdelay)",
                "(void) halfdelay ((int) ((cursesdelay + 99) / 100));",
                "else",
                "(void) nodelay (curseswin, TRUE);",
                "break;",
                "",
                "case 'd':",
                "case 'D':",
                " /* Delete the break point. */",
                "breakpoint = -1;",
                "break;",
                "",
                "case 'q':",
                "case 'Q':",
                " /* Quit the program. */",
                'ncptl_fatal ("User interactively entered \\"Q\\" to quit the program");',
                "break;",
                "",
                "default:",
                " /* No other keys do anything special. */",
                "break;",
                "}",
                "}"],
                          stack=newcode)
        else:
            self.pushmany([
                'fprintf (stderr, "[TRACE] phys: %d | virt: %d | action: %s | event: %" NICS " / %" NICS " | lines: %d - %d\\n",',
                "physrank, thisev->virtrank, eventnames[thisev->type], i+1, totalevents, thisev->firstline, thisev->lastline);"],
                          stack=newcode)
        newcode = newcode + self.invoke_hook("code_define_main_PRE_SWITCH",
                                             localvars, invoke_on=self.c_trace_parent)
        return newcode

    def code_declare_globals_EXTRA(self, localvars):
        "Declare additional C global variables needed by the c_trace backend."
        newvars = []
        self.code_declare_var(type="int", name="currentline", arraysize="2",
                              comment="Current lines of source code (beginning and ending)",
                              stack=newvars)
        self.code_declare_var(name="totalevents",
                              comment="Total # of events in the event list",
                              stack=newvars)
        if self.use_curses:
            self.code_declare_var(type="WINDOW *", name="curseswin",
                                  comment="Window to use for curses-based tracing",
                                  stack=newvars)
            self.code_declare_var(name="cursestask",
                                  comment="Task to trace using curses",
                                  stack=newvars)
            self.code_declare_var(name="cursesdelay",
                                  comment="Delay in milliseconds after each curses screen update",
                                  stack=newvars)
            self.code_declare_var(name="breakpoint",
                                  comment="Source line at which to enter single-stepping mode",
                                  stack=newvars)
            self.code_declare_var(type="int", name="eventdigits", rhs="1",
                                  comment="Number of digits in numevents",
                                  stack=newvars)
            self.code_declare_var(type="int", name="taskdigits", rhs="1",
                                  comment="Number of digits in var_num_tasks",
                                  stack=newvars)

        # Make all declarations static.
        static_newvars = []
        for var in newvars:
            static_newvars.append("static " + var)

        # Provide a hook for including more variables.
        static_newvars = static_newvars + self.invoke_hook("code_declare_globals_EXTRA",
                                                           localvars, invoke_on=self.c_trace_parent)
        return static_newvars

    def code_def_init_decls_POST(self, localvars):
        "Declare extra variables needed within conc_initialize()."
        newdecls = self.invoke_hook("code_def_init_decls_POST", localvars,
                                    invoke_on=self.c_trace_parent)
        if self.use_curses:
            self.srcloop = self.code_declare_var(type="int", suffix="loop",
                                                 comment="Loop over source-code lines",
                                                 stack=newdecls)
        return newdecls

    def code_define_functions_INIT_COMM_3(self, localvars):
        "Generate code to initialize the c_trace backend."
        initcode = self.invoke_hook("code_define_functions_INIT_COMM_3",
                                    localvars,
                                    invoke_on=self.c_trace_parent,
                                    after=[""])
        if self.use_curses:
            self.pushmany([
                "",
                " /* Initialize curses. */",
                "if (physrank == cursestask) {",
                "if (!(curseswin=initscr()))",
                'ncptl_fatal ("Unable to initialize the curses library");',
                "(void) cbreak();",
                "(void) noecho();",
                "(void) curs_set (0);",
                "if (cursesdelay)",
                "(void) halfdelay ((int)((cursesdelay+99)/100));",
                "else",
                "(void) nodelay (curseswin, TRUE);",
                "for (%s=0; %s<(int)(sizeof(sourcecode)/sizeof(char *))-1; %s++) {" %
                (self.srcloop, self.srcloop, self.srcloop),
                "if (%s >= LINES-1)" % self.srcloop,
                "break;",
                "(void) attrset (A_BOLD);",
                '(void) mvprintw (%s, 0, "%%3d.  ", %s+1);' %
                (self.srcloop, self.srcloop),
                "(void) attrset (A_NORMAL);",
                '(void) printw ("%%.*s", COLS, sourcecode[%s]);' % self.srcloop,
                "}",
                "(void) refresh();",
                "}"],
                          stack=initcode)
        return initcode

    # Completely redefine codegen_c_generic.py's code_allocate_event method.
    def code_allocate_event(self, event_type, stack=None,
                            declare="CONC_EVENT *thisev ="):
        "Push the code to allocate an event and keep track of used events."
        self.push("%s (currentline[0]=%d, currentline[1]=%d, conc_allocate_event (%s));" %
                  (declare,
                   self.current_node.lineno0, self.current_node.lineno1,
                   event_type),
                  stack)
        self.events_used[event_type] = 1

    def code_def_exit_handler_BODY(self, localvars):
        "Shut down curses if necessary."
        if self.use_curses:
            exitcode = ["if (physrank == cursestask)",
                        "(void) endwin();"]
        else:
            exitcode = []
        exitcode = exitcode + self.invoke_hook("code_def_exit_handler_BODY",
                                               localvars, invoke_on=self.c_trace_parent)
        return exitcode

    def n_outputs(self, node):
        "Write a message to standard out, but not if we're using curses."
        self.current_node = node
        self.c_trace_parent.n_outputs(self, node)
        if self.use_curses:
            self.arbitrary_code[-1] = []
