#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# Virtual base class for all C-based backends
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# Copyright (C) 2009, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2009).  Los Alamos National Security, LLC.  This software
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
########################################################################

import sys
import re
import string
import time
import types
import os
import tempfile
from ncptl_ast import AST
from ncptl_error import NCPTL_Error
from ncptl_variables import Variables
from ncptl_config import ncptl_config


class NCPTL_CodeGen:
    thisfile = globals()["__file__"]
    trivial_nodes = [
        "top_level_stmt_list",
        "header_decl_list",
        "header_decl",
        "simple_stmt",
        "source_task",
        "target_tasks",
        "touching_type",
        "byte_count",
        "restricted_ident",
        "rel_expr",
        "rel_primary_expr",
        "expr",
        "primary_expr",
        "item_count"]

    #---------------------#
    # Exported functions  #
    # (called from the    #
    # compiler front end) #
    #---------------------#

    def __init__(self, options=None):
        "Initialize the generic C code generation module."

        # Define a suffix for ncptl_int constants.  This is critical
        # when calling stdarg functions such as ncptl_func_min().
        self.ncptl_int_suffix = ncptl_config["NCPTL_INT_SUFFIX"]

        # Initialize the mappings from coNCePTuaL operators to C operators.
        self.binops = {'op_land'  : '&&',
                       'op_lor'   : '||',
                       'op_eq'    : '==',
                       'op_lt'    : '<',
                       'op_gt'    : '>',
                       'op_le'    : '<=',
                       'op_ge'    : '>=',
                       'op_ne'    : '!=',
                       'op_plus'  : '+',
                       'op_minus' : '-',
                       'op_or'    : '|',
                       'op_xor'   : '^',
                       'op_mult'  : '*',
                       'op_div'   : '/',
                       'op_and'   : '&'}
        self.unops = {'op_neg' : '-',
                      'op_pos' : '+',
                      'op_not' : '~'}

        # Create a placeholder error object.  Currently, this isn't used.
        self.errmsg = NCPTL_Error()

        # Define a set of variables to export to user programs.  These
        # variables are updated automatically at run time.
        self.exported_vars = {}
        for name, description in Variables.variables.items():
            self.exported_vars["var_%s" % name] = ("ncptl_int", description)

        # Define a set of command-line parameters that need to be
        # maintained outside of the run-time library
        self.base_global_parameters = []

        # Define a set of command-line parameters for the backend itself.
        self.cmdline_options = []

        # Enable a derived backend to indicate that the eventnames[]
        # array should be defined in the generated code.
        self.define_eventnames = 0

        # Set some default compilation parameters.
        self.compilation_parameters = {}
        exec_prefix = self.get_param("exec_prefix", "")
        prefix = self.get_param("prefix", "")
        includedir = self.get_param("includedir", "")
        includedir = string.replace(includedir, "${exec_prefix}", exec_prefix)
        includedir = string.replace(includedir, "${prefix}", prefix)
        if includedir:
            self.set_param("CPPFLAGS", "prepend", "-I%s" % includedir)
        libdir = self.get_param("libdir", "")
        libdir = string.replace(libdir, "${exec_prefix}", exec_prefix)
        libdir = string.replace(libdir, "${prefix}", prefix)
        if libdir:
            self.set_param("LDFLAGS", "prepend", "-L%s" % libdir)
        self.set_param("LIBS", "prepend", "-lncptl")

        # Point each method name in the trivial_nodes list to the
        # n_trivial_node method.
        for mname in self.trivial_nodes:
            setattr(self, "n_" + mname, self.n_trivial_node)

    def generate(self, ast, filesource='<stdin>', filetarget="-", sourcecode=None):
        "Compile an AST into a list of lines of C code."
        self.filesource = filesource       # Input file
        self.sourcecode = sourcecode       # coNCePTuaL source code
        self.codestack = []                # Stack of unprocessed metadata
        self.global_declarations = []      # Extra global variable declarations
        self.backend_declarations = []     # Declarations from BACKEND DECLARES statements
        self.init_elements = []            # Code to initialize the element list
        self.arbitrary_code = []           # Blocks of arbitrary EV_CODE statements
        self.extra_func_decls = []         # Additional functions to declare
        self.referenced_vars = {}          # Variables to store in the EV_CODE struct
        self.referenced_exported_vars = {} # Exported variables that need to be updated
        self.stores_restores_vars = 0      # 1=program STORES or RESTORES COUNTERS
        self.events_used = {}              # Set of EV_* events actually used
        self.program_uses_log_file = 0     # 1=program references log data; 0=it doesn't
        self.program_uses_touching = 0     # 1=need to touch data somewhere
        self.program_uses_randomness = 0   # 2=need to choose and broadcast a seed; 1=choose only; 0=no randomness
        self.program_uses_range_lists = 0  # 1=generate helper code for sequences
        self.logcolumn = 0                 # Current column in the log file
        self.nextvarnum = 0                # Next sequential variable number
        self.global_parameters = self.base_global_parameters
        self.errmsg = NCPTL_Error(filesource)

        # Walk the AST in postorder fashion.
        self.postorder_traversal(ast)
        if len(self.codestack) != 1:
            self.errmsg.error_internal("code stack contains %s" % str(self.codestack[0:-1]))
        return self.codestack[0]

    def compile_only(self, progfilename, codelines, outfilename, verbose, keepints):
        "Compile a list of lines of C code into a .o file."
        return self.do_compile(progfilename, codelines, outfilename, verbose, keepints, link=0)

    def compile_and_link(self, progfilename, codelines, outfilename, verbose, keepints):
        "Compile a list of lines of C code into an executable file."
        return self.do_compile(progfilename, codelines, outfilename, verbose, keepints, link=1)


    #-----------------------#
    # Utility functions     #
    # (non-code-generating) #
    #-----------------------#

    def show_help(self):
        "Output a help message."
        backend_match = re.match(r'(\w+)', self.backend_name)
        if not backend_match:
            self.errmsg.error_internal('Unable to parse backend_name "%s"' % self.backend_name)
        print "Usage: %s [OPTION...]" % backend_match.group(1)
        for opt, optdesc in self.cmdline_options:
            print "  %-31.31s %s" % (opt, optdesc)
        print
        print "Help options:"
        print "  --help                          Show this help message"

    def set_param(self, varname, disposition, value):
        """
             Specify how a compilation parameter is to be modified.
             Modifications are listed in FIFO order so that child
             backends can override parent backends.
        """
        if not self.compilation_parameters.has_key(varname):
            self.compilation_parameters[varname] = []
        self.compilation_parameters[varname].append((disposition, value))

    def get_param(self, varname, defaultval=""):
        """
             Look up variable VARNAME's value in the environment and
             return it if it's there.  If not, look in the coNCePTuaL
             configuration file and, if the value is still not found,
             use DEFAULTVAL.  Then, modify the value as specified by
             COMPILATION_PARAMETERS, which is a list of pairs, the
             first element of which is one of \"replace\",
             \"prepend\", or \"append\", and the second element of
             which is a string that will modify the value as
             specified.
        """

        # Determine an initial value to use.
        if os.environ.has_key(varname):
            # Environment variables override all backend modifications.
            return os.environ[varname]
        elif ncptl_config.has_key(varname):
            value = ncptl_config[varname]
        else:
            value = defaultval

        # Modify the value as specified by any derived backends.
        if self.compilation_parameters.has_key(varname):
            for disposition, selfvalue in self.compilation_parameters[varname]:
                if disposition == "prepend":
                    value = selfvalue + " " + value
                elif disposition == "append":
                    value = value + " " + selfvalue
                elif disposition == "replace":
                    value = selfvalue

        # Return the modified string.
        return value

    def push(self, value, stack=None):
        "Push a value onto the code (and metadata) stack or a given stack."
        if stack != None:
            stack.append(value)
        else:
            self.codestack.append(value)

    def pushmany(self, values, stack=None):
        "Push an array of values onto the code (and metadata) stack or a given stack."
        if stack != None:
            stack.extend(values)
        else:
            self.codestack.extend(values)

    def pop(self, stack=None):
        "Pop a value from the code (and metadata) stack or a given stack."
        if stack:
            value = stack[-1]
            del(stack[-1])
        else:
            value = self.codestack[-1]
            del(self.codestack[-1])
        return value

    def newvar(self, prefix="ivar", suffix=""):
        "Return the name of a new variable that we can use internally."
        while 1:
            self.nextvarnum = self.nextvarnum + 1
            num = self.nextvarnum
            stringnum = ""
            while 1:
                quot, rem = divmod (num, 27)
                stringnum = "_abcdefghijklmnopqrstuvwxyz"[rem] + stringnum
                if rem==0 or quot==0:
                    break
                num = quot
            if stringnum[-1] != '_':
                if suffix:
                    return prefix + "_" + stringnum + "_" + suffix
                else:
                    return prefix + "_" + stringnum

    def push_marker(self, stack=None):
        '''
           Push a marker symbol onto the stack in preparation for a
           call to combine_to_marker.
        '''
        self.push("#MARKER#", stack)

    def combine_to_marker(self, stack=None):
        '''
           Pop values from the code (and metadata) stack until we
           encounter a marker, then push the popped values as an array.
        '''
        poppedvals = []
        while 1:
            value = self.pop(stack)
            if value == "#MARKER#":
                break
            else:
                poppedvals.append(value)
        poppedvals.reverse()
        self.push(poppedvals, stack)

    def wrap_stack(self, leftcode, rightcode, stack=None):
        "Wrap the contents of a stack head within two blocks of code."
        if not stack:
            stack = self.init_elements
        stack[-1][0:0] = leftcode
        stack[-1].extend(rightcode)

    def invoke_hook(self, hookname, localvars, before=None, after=None,
                    alternatepy=None, alternate=None, invoke_on=None):
        """
           Invoke a hook method if it exists, passing it a dictionary
           of the current scope's local variables.  The hook function
           should return a list of code lines suitable for passing to
           self.pushmany.  This list will have BEFORE prepended and
           AFTER appended.  If the HOOKNAME method does not exist,
           evaluate ALTERNATEPY.  If ALTERNATEPY is not defined,
           return ALTERNATE.  The hook is invoked on SELF unless
           INVOKE_ON is specified in which case that class or object
           is used instead.
        """
        if not before:
            before = []
        if not after:
            after = []
        if not alternate:
            alternate = []
        if invoke_on:
            hookmethod = getattr(invoke_on, hookname, None)
            hookargs = (self, localvars)
        else:
            hookmethod = getattr(self, hookname, None)
            hookargs = (localvars,)
        if hookmethod:
            hookoutput = apply(hookmethod, hookargs)
            if hookoutput:
                return before + hookoutput + after
            else:
                return []
        elif alternatepy:
            return alternatepy(localvars)
        else:
            return alternate

    def do_compile(self, progfilename, codelines, outfilename, verbose=0, keepints=0, link=1):
        """
            Compile and optionally link a list of lines of C code into
            an object file or executable file.
        """
        exe_ext = self.get_param("EXEEXT", "")
        if exe_ext:
            exe_ext = "." + exe_ext
        obj_ext = self.get_param("OBJEXT", "o")
        if obj_ext:
            obj_ext = "." + obj_ext
        intermediates = []

        # Determine names for our output and intermediate files.
        if progfilename == "<command line>" or progfilename == "<stdin>":
            progfilename = "a.out.ncptl"
        if outfilename == "-":
            outfilename = os.path.splitext(progfilename)[0]
            if link:
                outfilename = outfilename + exe_ext
            else:
                outfilename = outfilename + obj_ext
        if keepints:
            # If we plan to keep the .c file, derive it's name from outfilename.
            if (link and exe_ext) or (not link and obj_ext):
                infilename = os.path.splitext(outfilename)[0]
            else:
                infilename = os.path.splitext(outfilename + ".bogus")[0]
            infilename = infilename + ".c"
        else:
            # If we plan to discard the .c file then give it a unique name.
            tempfile.tempdir = os.path.split(outfilename)[0]
            tempfile.template = re.sub(r'\W+', "_", self.backend_name + "_" + str(os.getpid()))
            while 1:
                fbase = tempfile.mktemp()
                try:
                    os.stat(fbase + ".c")
                    if link:
                        os.stat(fbase + obj_ext)
                except:
                    break
            infilename = fbase + ".c"
        intermediates.append(infilename)

        # Determine the compiler and compiler flags to use.
        CC = self.get_param("CC", "cc")
        CPPFLAGS = self.get_param("CPPFLAGS")
        CFLAGS = self.get_param("CFLAGS")
        LDFLAGS = self.get_param("LDFLAGS")
        LIBS = self.get_param("LIBS")

        # Define a shell command that invokes the C compiler.
        if link:
            compile_string = ("%s %s %s %s %s %s -o %s" %
                              (CC, CPPFLAGS, CFLAGS, infilename, LDFLAGS, LIBS, outfilename))
            objfilename = os.path.splitext(infilename)[0] + obj_ext
            intermediates.append(objfilename)
        else:
            compile_string = ("%s %s %s -c %s -o %s" %
                              (CC, CPPFLAGS, CFLAGS, infilename, outfilename))

        # Copy CODELINES to a .c file.
        try:
            infile = open(infilename, "w")
            for oneline in codelines:
                if string.find(oneline, "ncptl_log_open") != -1:
                    # Add an extra log-file prologue comment showing
                    # the ncptl command line.
                    ncptl_command = []
                    for arg in sys.argv:
                        clean_arg = arg
                        clean_arg = string.replace(clean_arg, "\\", "\\\\")
                        clean_arg = string.replace(clean_arg, '"', '\\"')
                        if string.find(clean_arg, " ") != -1:
                            clean_arg = string.replace(clean_arg, "'", "\\'")
                            clean_arg = "'%s'" % clean_arg
                        ncptl_command.append(clean_arg)
                    ncptl_command = string.join(ncptl_command, " ")
                    infile.write('ncptl_log_add_comment ("Front-end compilation command line", "%s");\n' % ncptl_command)

                    # Add an extra log-file prologue comment showing
                    # COMPILE_STRING.
                    clean_compile_string = string.replace(compile_string, "\\", "\\\\")
                    clean_compile_string = string.replace(clean_compile_string, '"', '\\"')
                    infile.write('ncptl_log_add_comment ("Back-end compilation command line", "%s");\n' % clean_compile_string)
                infile.write("%s\n" % oneline)
            infile.close()
        except IOError, (errno, strerror):
            self.errmsg.error_fatal("Unable to produce %s (%s)" % (infilename, strerror),
                                    filename=self.backend_name)

        # Indent the .c file for aesthetic purposes.
        indentcmd = self.get_param("INDENT", "no")
        if indentcmd != "no" and keepints:
            os.environ["VERSION_CONTROL"] = "simple"
            os.environ["SIMPLE_BACKUP_SUFFIX"] = ".BAK"
            indent_string = "%s %s" % (indentcmd, infilename)
            if verbose:
                sys.stderr.write("%s\n" % indent_string)
            if os.system(indent_string) != 0:
                self.errmsg.warning("The indentation command exited abnormally; continuing regardless")
            try:
                os.remove(infilename + ".BAK")
            except OSError:
                pass

        # Compile and optionally link the .c file, then optionally
        # delete it.  If we're linking then also optionally delete the
        # .o file.
        if verbose:
            sys.stderr.write("%s\n" % compile_string)
        if os.system(compile_string) != 0:
            self.errmsg.error_fatal("The C compiler exited abnormally; aborting coNCePTuaL")
        for deletable in intermediates:
            if os.path.isfile(deletable):
                if keepints:
                    if verbose:
                        sys.stderr.write("# Not deleting %s ...\n" % deletable)
                else:
                    if verbose:
                        sys.stderr.write("# Deleting %s ...\n" % deletable)
                    try:
                        os.unlink(deletable)
                    except OSError, errmsg:
                        sys.stderr.write("# --> %s\n" % errmsg)
        if verbose:
            sys.stderr.write("# Files generated: %s\n" % outfilename)
        return outfilename

    def postorder_traversal(self, node):
        "Perform a postorder traversal of an abstract syntax tree."
        for kid in node.kids:
            self.postorder_traversal(kid)
        try:
            func = getattr(self, "n_" + node.type)
            func(node)
        except AttributeError:
            self.errmsg.error_internal('I don\'t know how to process nodes of type "%s"' % node.type)

    def clean_comments(self, comment_str):
        'Replace "/*" with "/_*" and "*/" with "*_/" so as not to confuse C.'
        return string.replace(string.replace(comment_str, "/*", "/_*"), "*/", "*_/")

    def unquote_string(self, conc_str):
        '''
           Replace "\\<char>" with "<char>" in a given string to convert a
           string specified in a coNCePTuaL program to a C string.
        '''
        c_chars = []
        orig_num_chars = len(conc_str)
        c = 1
        while c < orig_num_chars-1:
            if conc_str[c] == '\\':
                c = c + 1
                nextchar = conc_str[c]
                if nextchar == 'n':
                    c_chars.append("\n")
                else:
                    c_chars.append(nextchar)
            else:
                c_chars.append(conc_str[c])
            c = c + 1
        return string.join(c_chars, "")

    def range_list_wrapper(self, rangelist):
        """
           Return header and trailer code that repeats a statement for
           each element in a list of sets.
        """
        # Acquire our parameters and preprocess the range list.
        self.program_uses_range_lists = 1
        orig_rangelist = rangelist
        rangelist = []
        for orig_range in orig_rangelist:
            # Canonicalize each entry into a tuple of {initial
            # value(s), final value} to avoid special cases later on.
            if orig_range[1] == None:
                for singleton in orig_range[0]:
                    rangelist.append(([singleton], singleton))
            else:
                rangelist.append(orig_range)

        # Begin a new scope.
        wrapper_code = []
        self.push_marker(wrapper_code)
        self.push("{", wrapper_code)

        # Figure out the pattern used in each range in RANGELIST and
        # convert each range to an element of a C struct.
        self.code_declare_var("LOOPBOUNDS",
                              name="loopbounds[%d]" % len(rangelist),
                              comment="List of range descriptions",
                              stack=wrapper_code)
        self.code_declare_var(name="rangenum",
                              comment="Current offset into loopbounds[]",
                              stack=wrapper_code)
        self.code_declare_var(name="initial_vals",
                              arraysize=max(map(lambda r: len(r[0]),
                                                rangelist)),
                              comment="Cache of the initial, enumerated values",
                              stack=wrapper_code)
        self.code_declare_var(name="final_val",
                              comment="Cache of the final value",
                              stack=wrapper_code)
        loopindex = 0
        for enumvals, finalval in rangelist:
            prefix = "loopbounds[%d]" % loopindex
            self.push("", wrapper_code)
            self.push(" /* Write range %d's loop bounds, \"next\" function, and termination function to %s. */" %
                      (loopindex, prefix),
                      wrapper_code)
            loopindex = loopindex + 1
            for i in range(0, len(enumvals)):
                self.push("initial_vals[%d] = %s;" % (i, enumvals[i]),
                          wrapper_code)
            self.pushmany([
                "final_val = %s;" % finalval,
                "%s.integral = 1;       /* Default to an integral sequence. */" % prefix,
                "%s.u.i.startval = initial_vals[0];" % prefix,
                "%s.u.i.endval = final_val;" % prefix],
                          wrapper_code)
            if len(enumvals) == 1:
                if enumvals[0] == finalval:
                    # Constant value: Generate a one-trip loop.
                    self.pushmany([
                        "%s.comparator = CONC_LEQ;" % prefix,
                        "%s.increment = CONC_ADD;" % prefix,
                        "%s.u.i.incval = 1;" % prefix],
                                  wrapper_code)
                else:
                    # Two element range: Increment is second minus first.
                    self.pushmany([
                        "%s.comparator = initial_vals[0]<=final_val ? CONC_LEQ : CONC_GEQ;" %
                        prefix,
                        "%s.increment = CONC_ADD;" % prefix,
                        "%s.u.i.incval = initial_vals[0]<=final_val ? 1 : -1;" %
                        prefix],
                                  wrapper_code)
            elif len(enumvals) == 2:
                # Two initial elements dictate an arithmetic progression.
                self.pushmany([
                    " /* Arithmetic progression */",
                    "%s.comparator = initial_vals[0]<=initial_vals[1] ? CONC_LEQ : CONC_GEQ;" %
                    prefix,
                    "%s.increment = CONC_ADD;" % prefix,
                    "%s.u.i.incval = initial_vals[1]-initial_vals[0];" % prefix,
                    "if (!%s.u.i.incval)" % prefix,
                    "%s.u.i.incval = 1;   /* Handle {x,x,x,...,x} case (constant value) */" %
                    prefix],
                              wrapper_code)
            else:
                # Range containing a few initial elements: Find the pattern.
                # First, look for an arithmetic progression.
                conditionals = []
                for e in range(len(enumvals)-2):
                    self.push("initial_vals[%d]-initial_vals[%d]==initial_vals[%d]-initial_vals[%d]" %
                              (e+1, e, e+2, e+1),
                              conditionals)
                self.pushmany([
                    "if (%s) {" % string.join(conditionals, " && "),
                    " /* Arithmetic progression */",
                    "%s.comparator = initial_vals[0]<=initial_vals[1] ? CONC_LEQ : CONC_GEQ;" %
                    prefix,
                    "%s.increment = CONC_ADD;" % prefix,
                    "%s.u.i.incval = initial_vals[1]-initial_vals[0];" % prefix,
                    "if (!%s.u.i.incval)" % prefix,
                    "%s.u.i.incval = 1;   /* Handle {x,x,x,...,x} case (constant value) */" %
                    prefix,
                    "}"],
                              wrapper_code)

                # Second, look for an increasing geometric progression.
                conditionals = []
                for e in range(len(enumvals)-1):
                    self.push("initial_vals[%d]" % e, conditionals)
                self.push("initial_vals[0]<initial_vals[1]", conditionals)
                for e in range(len(enumvals)-1):
                    self.push("initial_vals[%d]*(initial_vals[%d]/initial_vals[%d])==initial_vals[%d]" %
                              (e, e+1, e, e+1),
                              conditionals)
                for e in range(len(enumvals)-2):
                    self.push("initial_vals[%d]/initial_vals[%d]==initial_vals[%d]/initial_vals[%d]" %
                              (e+1, e, e+2, e+1),
                              conditionals)
                self.pushmany([
                    "else",
                    "if (%s) {" % string.join(conditionals, " && "),
                    " /* Geometric progression (increasing, integral multiplier) */",
                    "%s.comparator = CONC_LEQ;" % prefix,
                    "%s.increment = CONC_MULT;" % prefix,
                    "%s.u.i.incval = initial_vals[1]/initial_vals[0];" % prefix,
                    "}"],
                              wrapper_code)

                # Third, look for a decreasing geometric progression.
                conditionals = []
                for e in range(1, len(enumvals)):
                    self.push("initial_vals[%d]" % e, conditionals)
                self.push("initial_vals[0]>initial_vals[1]", conditionals)
                for e in range(len(enumvals)-1):
                    self.push("initial_vals[%d]*(initial_vals[%d]/initial_vals[%d])==initial_vals[%d]" %
                              (e+1, e, e+1, e),
                              conditionals)
                for e in range(len(enumvals)-2):
                    self.push("initial_vals[%d]/initial_vals[%d]==initial_vals[%d]/initial_vals[%d]" %
                              (e, e+1, e+1, e+2),
                              conditionals)
                self.pushmany([
                    "else",
                    "if (%s) {" % string.join(conditionals, " && "),
                    " /* Geometric progression (decreasing, integral multiplier) */",
                    "%s.comparator = CONC_GEQ;" % prefix,
                    "%s.increment = CONC_DIV;" % prefix,
                    "%s.u.i.incval = initial_vals[0]/initial_vals[1];" % prefix,
                    "}"],
                              wrapper_code)

                # Fourth, look for a geometric progression that
                # increases by a non-integral multiplier.
                conditionals = []
                for e in range(len(enumvals)-1):
                    self.push("initial_vals[%d]" % e, conditionals)
                self.pushmany([
                    "else",
                    "if (%s) {" % string.join(conditionals, " && ")],
                              wrapper_code)
                self.code_declare_var(type="double", name="initial_vals_d",
                                      arraysize=len(enumvals),
                                      comment="Cache of the initial, enumerated values, but in floating-point context",
                                      stack=wrapper_code)
                self.code_declare_var(type="double", name="avg_factor",
                                      comment="Average multiplier for terms in the sequence",
                                      stack=wrapper_code)
                for i in range(0, len(enumvals)):
                    self.push("initial_vals_d[%d] = %s;" %
                              (i, self.code_make_expression_fp(enumvals[i],
                                                               floating_context=1)),
                              wrapper_code)
                self.pushmany([
                    "avg_factor = (%s) / %d.0;" %
                    (string.join(map(lambda e: "initial_vals_d[%d]/initial_vals_d[%d]" % (e+1, e),
                                     range(0, len(enumvals)-1)),
                                 " + "),
                     len(enumvals)-1),
                    "if (%s) {" %
                    string.join(map(lambda e: "CONC_DBL2INT(initial_vals_d[%d]*avg_factor)==initial_vals[%d]" %
                                    (e, e+1),
                                    range(0, len(enumvals)-1)),
                                " && "),
                    " /* Geometric progression (decreasing or non-integral multiplier) */",
                    "%s.comparator = initial_vals[0]<initial_vals[1] ? CONC_LEQ : CONC_GEQ;" % prefix,
                    "%s.integral = 0;" % prefix,
                    "%s.increment = CONC_MULT;" % prefix,
                    "%s.u.d.startval = initial_vals_d[0];" % prefix,
                    "%s.u.d.endval = %s;" %
                    (prefix, self.code_make_expression_fp(finalval, floating_context=1)),
                    "%s.u.d.incval = avg_factor;" % prefix,
                    "}"],
                              wrapper_code)

                # Finally, issue an error message.  This code is
                # repeated because of the extra level of nesting
                # required for the floating-point geometric
                # progression case.
                no_pattern_error = 'ncptl_fatal ("Unable to find an arithmetic or geometric pattern to {%s..., %s}", %s);' % \
                                   ('%" NICS ", ' * len(enumvals), '%" NICS "',
                                    string.join(map(lambda e: "initial_vals[%d]" % e,
                                                    range(0, len(enumvals))),
                                                ", ") + ", final_val")
                self.pushmany([
                    "else",
                    no_pattern_error,
                    "}",
                    "else",
                    no_pattern_error],
                              wrapper_code)

        # For each range in LOOPBOUNDS iterate over each element
        # within that range.
        self.pushmany([
            "",
            " /* Now that we've defined all of our ranges we iterate over each range",
            "  * and each element within each range. */",
            "for (rangenum=0; rangenum<%d; rangenum++) {" % len(rangelist)],
                      wrapper_code)
        self.code_declare_var("LOOPBOUNDS *", name="thisrange",
                              rhs="&loopbounds[rangenum]",
                              comment="Current range",
                              stack=wrapper_code)
        self.pushmany([
            "if (conc_seq_nonempty (thisrange))",
            "for (conc_seq_init (thisrange);",
            "conc_seq_continue (thisrange);",
            "conc_seq_next (thisrange)) {"],
                      wrapper_code)
        self.combine_to_marker(wrapper_code)
        return (wrapper_code[0], ["}", "}", "}"])


    #------------------------------#
    # Utility functions            #
    # (code-generating, generic C) #
    #------------------------------#

    def code_begin_source_scope(self, source_task, stack=None):
        "Begin a new scope if source_task includes our task's rank."
        if source_task[0] == "task_all":
            if source_task[1]:
                self.pushmany([
                    "{    /* ALL TASKS %s */" % source_task[1],
                    "ncptl_int %s = virtrank;" % source_task[1]],
                              stack)
            else:
                self.push("{   /* ALL TASKS */", stack)
        elif source_task[0] == "task_expr":
            self.push("if ((%s) == virtrank) {" % source_task[1], stack)
        elif source_task[0] == "task_restricted":
            self.pushmany([
                "{",
                "ncptl_int %s = virtrank;" % source_task[1],
                "if (%s) {" % source_task[2]],
                          stack)
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        self.push(" /* The current coNCePTuaL statement applies to our task. */", stack)

    def code_end_source_scope(self, source_task, stack=None):
        "End the scope(s) created by code_begin_source_scope."
        if source_task[0] == "task_all":
            self.push("}", stack)
        elif source_task[0] == "task_expr":
            self.push("}", stack)
        elif source_task[0] == "task_restricted":
            self.push("}", stack)
            self.push("}", stack)
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])

    def code_begin_target_loop(self, source_task, target_tasks, stack=None):
        "Loop over all tasks, seeing if our task receives from each in turn."
        # Iterate over all potential source tasks.
        sourcevar = self.newvar(suffix="task")
        if source_task[0] == "task_all":
            if source_task[1]:
                rankvar = source_task[1]
            else:
                rankvar = self.newvar(suffix="loop")
            self.pushmany([
                "{",
                "ncptl_int %s;" % rankvar,
                " /* Loop over all tasks to see which will send to us. */",
                "for (%s=0; %s<var_num_tasks; %s++) {" % (rankvar, rankvar, rankvar)],
                          stack)
        elif source_task[0] == "task_expr":
            # Caveat: rankvar is being assigned an expression, not a variable.
            rankvar = source_task[1]
            self.push("if ((%s)>=0 && (%s)<var_num_tasks) {" % (rankvar, rankvar),
                      stack)
        elif source_task[0] == "task_restricted":
            rankvar = source_task[1]
            self.pushmany([
                "{",
                "ncptl_int %s;" % rankvar,
                " /* Loop over all tasks to see which will send to us. */",
                "for (%s=0; %s<var_num_tasks; %s++)" % (rankvar, rankvar, rankvar),
                "if (%s) {" % source_task[2]],
                          stack)
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        self.pushmany([
            " /* %s now represents one of the tasks that will send to us. */" % rankvar,
            "ncptl_int %s = %s;" % (sourcevar, rankvar)],
                  stack)

        # Create a scope for the target task(s).
        if target_tasks[0] == "all_others":
            self.push("if (virtrank != %s) {" % rankvar, stack)
        elif target_tasks[0] == "task_restricted":
            self.pushmany([
                "ncptl_int %s = virtrank;" % target_tasks[1],
                "if (%s) {" % target_tasks[2]],
                          stack)
        elif target_tasks[0] == "task_expr":
            self.push("if (virtrank == (%s)) {" % target_tasks[1], stack)
        else:
            self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        return sourcevar

    def code_end_target_loop(self, source_task, target_tasks, stack=None):
        "End the scope(s) created by code_begin_target_loop."
        if source_task[0] in ["task_all", "task_restricted"]:
            self.push("}", stack)
            self.push("}", stack)
        elif source_task[0] == "task_expr":
            self.push("}", stack)
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        if target_tasks[0] in ["all_others", "task_expr", "task_restricted"]:
            self.push("}", stack)
        else:
            self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])

    def code_declare_var(self, type="ncptl_int", name=None, suffix="",
                         arraysize="", rhs=None, comment="", stack=None):
        if name:
            newvar = name
        else:
            newvar = self.newvar(suffix=suffix)
        if arraysize:
            arraysize = "[%s]" % arraysize
        if comment:
            comment = "   /* %s */" % comment
        if rhs:
            self.push("%s %s%s = %s;%s" % (type, newvar, arraysize, rhs, comment), stack)
        else:
            self.push("%s %s%s;%s" % (type, newvar, arraysize, comment), stack)
        return newvar

    def code_allocate_event(self, event_type, stack=None,
                            declare="CONC_EVENT *thisev ="):
        "Push the code to allocate an event and keep track of used events."
        self.push("%s conc_allocate_event (%s);" % (declare, event_type),
                  stack)
        self.events_used[event_type] = 1

    def code_allocate_code_event(self, source_task, expressions, stack=None):
        "Push the code to allocate and fill in a code event."
        self.code_begin_source_scope(source_task, stack)
        self.code_allocate_event("EV_CODE", stack)
        self.push("thisev->s.code.number = %d;" % len(self.arbitrary_code),
                  stack)

        # Make all local variables point within the event structure.
        exprvars = {}
        for variable in re.findall(r'\bvar_\w+\b', expressions):
            if not self.exported_vars.has_key(variable):
                exprvars[variable] = 1
                self.referenced_vars[variable] = 1
        for variable in exprvars.keys():
            self.push("thisev->s.code.%s = %s;" % (variable, variable), stack)
        self.code_end_source_scope(source_task, stack)

    def code_make_expression_fp(self, expression, floating_context=0):
        '''
           Replace all non-special variable references with references
           to variables contained within the event structure.  Then,
           cast all variables to doubles and add ".0" to all integer
           constants to make them doubles.  Finally, replace each
           ncptl_func_* call with the corresponding ncptl_dfunc_*
           call.  If FLOATING_CONTEXT is true, then omit the
           event-structure modifications and prohibit bitwise
           operators.
        '''
        result = ""
        if re.search(r'[~^]|<<|>>',
                     string.replace(string.replace(expression, "&&", " AND "),
                                    "||", " OR ")):
            # Expression contains a bitwise operator -- cast only the
            # result to a double.
            if floating_context:
                self.errmsg.error_fatal("bitwise operators are prohibited in REAL context")
            for subexpr in re.split(r'\b(var_\w+)\b', expression):
                if string.find(subexpr, "var_") == 0:
                    if not self.exported_vars.has_key(subexpr):
                        result = result + "thisev->s.code."
                result = result + subexpr
            result = "(double) (%s)" % result
        else:
            # Cast all variables as doubles.
            for subexpr in re.split(r'\b(var_\w+)\b', expression):
                if string.find(subexpr, "var_") == 0:
                    result = result + "(double)"
                    if not self.exported_vars.has_key(subexpr) and not floating_context:
                        result = result + "thisev->s.code."
                result = result + subexpr
            # Express all constants as doubles.
            result = re.sub(r'\b(\d+)'+self.ncptl_int_suffix, r'\1.0', result)
            # Use the double version of each coNCePTuaL user function.
            result = re.sub(r'\bncptl_func_(\w+)\b', r'ncptl_dfunc_\1', result)
            result = re.sub(r'\bCONC_DBL2INT\b', "", result)
        return result

    def code_clock_control(self, command, stack=None):
        "Start and stop the various coNCePTuaL clocks."
        if command == "DECLARE":
            # Declare variables for storing the current time.
            self.code_declare_var(type="uint64_t",
                                  name="stop_elapsed_usecs",
                                  rhs="ncptl_time()",
                                  stack=stack)
        elif command == "STOP":
            # Stop the clock.
            self.push("var_elapsed_usecs = stop_elapsed_usecs - starttime;",
                      stack)
        elif command == "RESTART":
            # Restart a stopped clock.
            self.push("starttime += ncptl_time() - stop_elapsed_usecs;",
                      stack)
        else:
            self.errmsg.error_internal('unknown clock command "%s"' % command)

    def code_update_exported_vars(self, applicable_vars, struct, overrides={}, stack=None):
        "Update exported variables."
        update_var = {
            "var_bytes_sent":     " += thisev->s.%s.size",
            "var_bytes_received": " += thisev->s.%s.size",
            "var_total_bytes":    " += thisev->s.%s.size",
            "var_msgs_sent":      "++",
            "var_msgs_received":  "++",
            "var_total_msgs":     "++"}
        for variable, increment in overrides.items():
            update_var[variable] = increment
        for variable in applicable_vars:
            if self.referenced_exported_vars.has_key(variable):
                try:
                    self.push("%s%s;" % (variable, update_var[variable] % struct),
                              stack=stack)
                except TypeError:
                    self.push("%s%s;" % (variable, update_var[variable]),
                              stack=stack)

    def code_fill_in_comm_struct(self, struct, message_spec, attributes,
                                 targetvar, rankvar, stack=None,
                                 verification=1):
        "Fill in common fields of various communication-state structures."
        num_messages, uniqueness, message_size, alignment, misaligned, touching, buffer_num = message_spec

        # Fill in most of the fields.
        if rankvar != None and targetvar != None:
            self.push("%s.%s = ncptl_virtual_to_physical (procmap, %s);" % (struct, rankvar, targetvar), stack)
        if message_size != None:
            self.push("%s.size = %s;" % (struct, message_size), stack)
        if alignment != None:
            self.push("%s.alignment = %s;" % (struct, alignment), stack)
        if misaligned != None:
            self.push("%s.misaligned = %s;" % (struct, misaligned), stack)
        if touching != None:
            self.push("%s.touching = %d;" % (struct, int(touching=="touching")), stack)
            if verification:
                self.push("%s.verification = %d;" % (struct, int(touching=="verification")), stack)
        self.push("%s.pendingsends = pendingsends;" % struct, stack)
        self.push("%s.pendingrecvs = pendingrecvs;" % struct, stack)

        # The buffer_num field is assigned in one of many different ways.
        if buffer_num != None:
            if buffer_num != "default":
                self.push("if (%s < 0%s)" % (buffer_num, self.ncptl_int_suffix), stack)
            if "asynchronously" in attributes:
                self.push("%s.buffernum = pendingsends+pendingrecvs;" % struct, stack)
            elif verification:
                self.push("%s.buffernum = %s.verification ? pendingsends+pendingrecvs : 0;" %
                          (struct, struct),
                          stack)
            else:
                self.push("%s.buffernum = 0%s;" % (struct, self.ncptl_int_suffix), stack)
            if buffer_num != "default":
                self.pushmany([
                    "else",
                    "%s.buffernum = %s;" % (struct, buffer_num)],
                              stack)

        # Handle the buffer field differently based on whether the
        # message buffer is supposed to be unique.
        if None not in [uniqueness, message_size, alignment]:
            if uniqueness == "unique":
                if misaligned == 1:
                    self.push("%s.buffer = ncptl_malloc_misaligned (%s, %s);" %
                              (struct, message_size, alignment),
                              stack)
                else:
                    self.push("%s.buffer = ncptl_malloc (%s, %s);" %
                              (struct, message_size, alignment),
                              stack)
            else:
                self.pushmany([
                    "(void) ncptl_malloc_message (%s.size, %s.alignment, %s.buffernum, %s.misaligned);" %
                    (struct, struct, struct, struct),
                    "%s.buffer = NULL;" % struct],
                              stack)

    def code_in_range_list(self, node, expression, rangelist):
        'Return code for "expression IS IN {...}".'
        # Acquire a list of variables used in either the LHS or RHS.
        variables_used = {}
        for varname in re.findall(r'\b(var_\w+)\b', repr(expression) + " " + repr(rangelist)):
            variables_used[varname] = 1
        variables_used = variables_used.keys()

        # Map the printable version of the IS IN expression to a function name.
        must_define_helper = 0
        try:
            # Look for an existing name for this expression.
            funcname = self.is_in_to_func_name[node.printable]
        except AttributeError:
            # First function used -- create and populate the hash table.
            funcname = self.newvar(prefix="conc_IS_IN")
            self.is_in_to_func_name = {node.printable: funcname}
            must_define_helper = 1
        except KeyError:
            # First time this function is used -- add it to the hash table.
            funcname = self.newvar(prefix="conc_IS_IN")
            self.is_in_to_func_name[node.printable] = funcname
            must_define_helper = 1

        # Generate code for the helper function.
        if must_define_helper:
            helper_code = []
            self.push_marker(helper_code)
            if variables_used == []:
                formal_args = "void"
            else:
                formal_args = string.join(map(lambda vn: "ncptl_int " + vn, variables_used), ", ")
            self.push("/* Return 1 if %s; 0 if not. */" % node.printable, helper_code)
            self.push("int %s (%s)" % (funcname, formal_args), helper_code)
            self.push("{", helper_code)
            helper_main, helper_after = self.range_list_wrapper(rangelist)
            self.pushmany(helper_main, helper_code)
            self.pushmany(["if ((%s) == (thisrange->integral ? thisrange->u.i.loopvar : CONC_DBL2INT(thisrange->u.d.loopvar)))" % expression,
                           "return 1;"],
                          stack=helper_code)
            self.pushmany(helper_after, helper_code)
            self.pushmany(["return 0;",
                           "}"],
                          stack=helper_code)
            self.combine_to_marker(helper_code)
            self.extra_func_decls.append(helper_code[0])

        # Return an invocation of the helper function.
        if variables_used == []:
            actual_args = ""
        else:
            actual_args = string.join(variables_used, ", ")
        return "%s(%s)" % (funcname, actual_args)


    #-------#
    # Atoms #
    #-------#

    def n_integer(self, node):
        longval = str(node.attr)
        if longval[-1] == "L":
            longval = longval[:-1]
        self.push(longval + self.ncptl_int_suffix)

    def n_string(self, node):
        cstring = node.attr
        cstring = string.replace(cstring, '\\', '\\\\')
        cstring = string.replace(cstring, '"', '\\"')
        cstring = string.replace(cstring, '\n', '\\n')
        self.push('"%s"' % cstring)

    def n_ident(self, node):
        variable = "var_" + re.sub(r'\W', '_', node.attr)
        self.push(variable)
        if self.exported_vars.has_key(variable):
            self.referenced_exported_vars[variable] = 1


    #--------------#
    # Helper rules #
    #--------------#

    def n_task_expr(self, node):
        "Push a {task type, variable, condition} tuple onto the stack."
        if node.attr == "task_all":
            # ALL TASKS or ALL TASKS <var>
            if node.kids == []:
                self.push(("task_all", None, None))
            else:
                self.push(("task_all", self.pop(), None))
        elif node.attr == "expr":
            # TASK <expr>
            self.push(("task_expr", self.pop(), None))
        elif node.attr == "such_that":
            # TASK <var> SUCH THAT <rel_expr>
            condition = self.pop()
            variable = self.pop()
            self.push(("task_restricted", variable, condition))
        elif node.attr == "all_others":
            # ALL OTHER TASKS
            self.push(("all_others", None, None))
        else:
            self.errmsg.error_internal('Unknown task_expr type "%s"' % node.attr)

    def n_range_list(self, node):
        "Push a list of ranges."
        range_list = []
        for r in range(node.attr):
            range_list.insert(0, self.pop())
        self.push(range_list)

    def n_range(self, node):
        "Push an {initial values, final value} tuple on the stack."
        if node.attr == "ellipsis":
            # A, B, C, ..., G
            expr = self.pop()
            expr_list = self.pop()
            self.push((expr_list, expr))
        else:
            # A, B, C, D, E, F, G
            expr_list = self.pop()
            self.push((expr_list, None))

    def n_expr_list(self, node):
        """Gather a number of expressions from the stack and re-push
        them as a list."""
        expr_list = []
        for e in range(node.attr):
            expr_list.insert(0, self.pop())
        self.push(expr_list)

    def n_an(self, node):
        self.push("1%s" % self.ncptl_int_suffix)

    def n_data_multiplier(self, node):
        # Multiply an expression by a number of bytes.
        baseexpr = self.pop()
        nis = self.ncptl_int_suffix
        kilo = "1024%s" % nis
        multipliers = {
          "bits"        : "(%s)/8%s+(%s%%8!=0)" % (baseexpr, nis, baseexpr),
          "bytes"       : baseexpr,
          "kilobyte"    : "(%s)*%s" % (baseexpr, kilo),
          "megabyte"    : "(%s)*%s*%s" % (baseexpr, kilo, kilo),
          "gigabyte"    : "(%s)*%s*%s*%s" % (baseexpr, kilo, kilo, kilo),
          "halfwords"   : "(%s)*2%s" % (baseexpr, nis),
          "words"       : "(%s)*4%s" % (baseexpr, nis),
          "integers"    : "(%s)*sizeof(int)" % baseexpr,
          "doublewords" : "(%s)*8%s" % (baseexpr, nis),
          "quadwords"   : "(%s)*16%s" % (baseexpr, nis),
          "pages"       : "(%s)*ncptl_pagesize" % baseexpr
        }
        try:
            self.push(multipliers[node.attr])
        except KeyError:
            self.errmsg.error_internal('Unknown data multiplier "%s"' % node.attr)

    def n_data_type(self, node):
        nis = self.ncptl_int_suffix
        data_types = {
            "default"     : "0%s" % nis,
            "bytes"       : "1%s" % nis,
            "halfwords"   : "2%s" % nis,
            "words"       : "4%s" % nis,
            "integers"    : "sizeof(int)",
            "doublewords" : "8%s" % nis,
            "quadwords"   : "16%s" % nis,
            "pages"       : "ncptl_pagesize"
        }
        try:
            self.push(data_types[node.attr])
        except KeyError:
            self.errmsg.error_internal('Unknown data type "%s"' % node.attr)

    def n_item_size(self, node):
        # There should already be a valid number on the stack.  If
        # not, then push 0 (bytes).
        if len(node.kids) == 0:
            self.push("0%s" % self.ncptl_int_suffix)

    def n_message_alignment(self, node):
        '''If the stack does not already contain a message alignment,
        push the number zero, which represents the default alignment.'''
        if node.kids == []:
            self.push("0%s" % self.ncptl_int_suffix)

    def n_stride(self, node):
        "Determine the stride needed by a TOUCHES statement."
        if node.attr == "specified":
            datatype = self.pop()
            count = self.pop()
            self.push((node.attr, count, datatype))
        else:
            self.push((node.attr,))

    def n_unique(self, node):
        if node.attr:
            self.push(node.type)
        else:
            self.push("not_unique")

    def n_verification(self, node):
        self.push(node.type)
        self.program_uses_touching = 1

    def n_touching(self, node):
        self.push(node.type)
        self.program_uses_touching = 1

    def n_touch_repeat_count(self, node):
        "Specify the number of times a memory region should be touched."
        # If the program specified an expression, it's already on the
        # stack, If not, we use 1.
        if node.kids == []:
            self.push("1L")

    def n_no_touching(self, node):
        self.push("no_touching")

    def n_buffer_number(self, node):
        if node.kids:
            # An <expr> was already pushed on the stack.
            pass
        else:
            self.push("default")

    def n_recv_buffer_number(self, node):
        if node.kids:
            # An <expr> was already pushed on the stack.
            pass
        else:
            self.push("default")

    def n_message_spec(self, node):
        # Store all message-specification parameters in a single tuple.
        buffer_num = self.pop()
        touching = self.pop()
        alignment = self.pop()
        message_size = self.pop()
        uniqueness = self.pop()
        num_messages = self.pop()
        misaligned = node.attr
        self.push((num_messages, uniqueness, message_size,
                   alignment, misaligned, touching, buffer_num))

    def n_reduce_message_spec(self, node):
        # Store all message-specification parameters in a single tuple.
        buffer_num = self.pop()
        touching = self.pop()
        data_type = self.pop()
        alignment = self.pop()
        uniqueness = self.pop()
        item_count = self.pop()
        misaligned = node.attr
        self.push((item_count, uniqueness, data_type,
                   alignment, misaligned, touching, buffer_num))

    def n_send_attrs(self, node):
        self.push(node.attr)

    def n_receive_attrs(self, node):
        self.push(node.attr)

    def n_time_unit(self, node):
        # Push a multiplier that converts to microseconds.
        if node.attr == "microseconds":
            self.push("1")
        elif node.attr == "milliseconds":
            self.push("1000")
        elif node.attr == "seconds":
            self.push("1000*1000")
        elif node.attr == "minutes":
            self.push("60*1000*1000")
        elif node.attr == "hours":
            self.push("60*60*1000*1000")
        elif node.attr == "days":
            self.push("24*60*60*1000*1000")
        else:
            self.errmsg.error_internal('unknown time unit "%s"' % node.attr)

    def n_string_or_log_comment(self, node):
        "Push either a literal string or a call to ncptl_log_lookup_string()."
        literal = self.pop()
        if node.attr == "string":
            self.push(literal)
        elif node.attr == "value_of":
            self.program_uses_log_file = 1
            self.push('ncptl_log_lookup_string(logstate, %s)' % literal)
        else:
            self.errmsg.error_internal("Unknown string_or_log_comment %s" % repr(node.attr))

    def n_string_or_expr_list(self, node):
        "Push a list of {type, value} pairs."
        if node.attr:
            itemvalues = []
            for itemtype in node.attr:
                itemvalues = [self.pop()] + itemvalues
            typevaluepairs = []
            for offset in range(0, len(node.attr)):
                typevaluepairs.append((node.attr[offset], itemvalues[offset]))
            self.push(typevaluepairs)

    def n_log_expr_list(self, node):
        "Push a list of {description, value} pairs."
        log_expr_list = []
        for elt in range(node.attr):
            log_expr_list.insert(0, self.pop())
        self.push(log_expr_list)

    def n_log_expr_list_elt(self, node):
        "Push a {description, expression, aggregate} tuple."
        description = self.pop()
        expression = self.pop()
        aggregate = self.pop()
        self.push((description, expression, aggregate))

    def n_aggregate_func(self, node):
        self.push(node.attr)

    def n_let_binding(self, node):
        "Push an {ident, expr} pair."
        if node.attr != None:
            # We're binding to A RANDOM TASK.
            lowerbound = "0" + self.ncptl_int_suffix
            upperbound = "var_num_tasks-1" + self.ncptl_int_suffix
            exception = "-1" + self.ncptl_int_suffix
            for et in range(len(node.attr)-1, -1, -1):
                exprtype = node.attr[et]
                if exprtype == "E":
                    exception = self.pop()
                elif exprtype == "L":
                    lowerbound = self.pop()
                elif exprtype == "U":
                    upperbound = self.pop()
                elif exprtype == "l":
                    lowerbound = "(%s)+1%s" % (self.pop(), self.ncptl_int_suffix)
                elif exprtype == "u":
                    upperbound = "(%s)-1%s" % (self.pop(), self.ncptl_int_suffix)
            variable = self.pop()
            self.push((variable,
                       "ncptl_random_task(ncptl_func_max(2%s, 0%s, %s), ncptl_func_min(2%s, var_num_tasks-1%s, %s), %s)" %
                       (self.ncptl_int_suffix, self.ncptl_int_suffix, lowerbound,
                        self.ncptl_int_suffix, self.ncptl_int_suffix, upperbound,
                        exception)))
            self.program_uses_randomness = max(self.program_uses_randomness, 2)
        else:
            # We're not binding to A RANDOM TASK.
            expression = self.pop()
            identifier = self.pop()
            self.push((identifier, expression))

    def n_let_binding_list(self, node):
        "Push the number of {ident, expr} pairs we expect to see."
        if node.attr:
            self.push(node.attr)


    #------------------------#
    # Relational expressions #
    #------------------------#

    def n_eq_expr(self, node):
        "Compare two expressions for equality."
        # Process unary tests.
        if node.attr == "op_even":
            self.push("((%s)&1)==0" % self.pop())
            return
        elif node.attr == "op_odd":
            self.push("((%s)&1)==1" % self.pop())
            return

        # Process binary tests.
        right = self.pop()
        left = self.pop()
        try:
            self.push("(%s)%s(%s)" % (left, self.binops[node.attr], right))
        except KeyError:
            def in_range(expression, bound1, bound2):
                'Return code for "expression IS IN [bound1, bound2]".'
                return "((%s)<=(%s) && (%s)<=(%s)) || ((%s)<=(%s) && (%s)<=(%s))" % \
                       (bound1, expression, expression, bound2,
                        bound2, expression, expression, bound1)
            if node.attr == "op_divides":
                self.push("ncptl_func_modulo(%s, %s)==0" % (right, left))
            elif node.attr == "op_in_range":
                expression = self.pop()
                self.push(in_range(expression, left, right))
            elif node.attr == "op_not_in_range":
                expression = self.pop()
                self.push("!(%s)" % in_range(expression, left, right))
            elif node.attr == "op_in_range_list":
                self.push(self.code_in_range_list(node, left, right))
            elif node.attr == "op_not_in_range_list":
                self.push("!%s" % self.code_in_range_list(node, left, right))
            else:
                self.errmsg.error_internal('Unknown eq_expr "%s"' % node.attr)

    def n_rel_conj_expr(self, node):
        "Return true if and only if two expressions are both true."
        if len(node.kids) == 1:
            return
        right = self.pop()
        left = self.pop()
        self.push("(%s) && (%s)" % (left, right))

    def n_rel_disj_expr(self, node):
        "Return false if and only if two expressions are both false."
        if len(node.kids) == 1:
            return
        right = self.pop()
        left = self.pop()
        self.push("(%s) || (%s)" % (left, right))


    #-------------#
    # Expressions #
    #-------------#

    def n_power_expr(self, node):
        "Raise one expression to the power of another."
        if len(node.kids) == 1:
            return
        exponent = self.pop()
        base = self.pop()
        self.push("ncptl_func_power (%s, %s)" % (base, exponent))

    def n_unary_expr(self, node):
        "Apply a unary operator to a expression."
        if node.attr == None:
            return
        try:
            self.push("%s(%s)" % (self.unops[node.attr], self.pop()))
        except KeyError:
            self.errmsg.error_internal('Unknown unary_expr "%s"' % node.attr)

    def n_mult_expr(self, node):
        "Combine two expressions using a multiplicative operator."
        if len(node.kids) == 1:
            return
        right = self.pop()
        left = self.pop()
        try:
            self.push("(%s)%s(%s)" % (left, self.binops[node.attr], right))
        except KeyError:
            if node.attr == "op_mod":
                self.push("ncptl_func_modulo(%s,%s)" % (left, right))
            elif node.attr == "op_shl":
                self.push("ncptl_func_shift_left (%s, %s)" % (left, right))
            elif node.attr == "op_shr":
                self.push("ncptl_func_shift_left (%s, -(%s))" % (left, right))
            else:
                self.errmsg.error_internal('Unknown mult_expr "%s"' % node.attr)

    def n_add_expr(self, node):
        "Combine two expressions using an additive operator."
        if len(node.kids) == 1:
            return
        right = self.pop()
        left = self.pop()
        try:
            self.push("(%s)%s(%s)" % (left, self.binops[node.attr], right))
        except KeyError:
            self.errmsg.error_internal('Unknown add_expr "%s"' % node.attr)

    def n_ifelse_expr(self, node):
        "Return one of two expressions based on a condition."
        if len(node.kids) == 1:
            return
        else_expr = self.pop()
        condition = self.pop()
        if_expr = self.pop()
        self.push("(%s) ? (%s) : (%s)" % (condition, if_expr, else_expr))

    def n_func_call(self, node):
        "Push a call to a function that takes one or more arguments."
        func_name = node.attr
        arguments = self.pop()
        num_args = len(arguments)

        # MIN and MAX are special in that they take an arbitrary
        # number of arguments.
        if func_name in ["MIN", "MAX"]:
            self.push("ncptl_func_%s(%d%s, %s)" %
                      (string.lower(func_name),
                       num_args,
                       self.ncptl_int_suffix,
                       string.join(arguments, ",")))
            return

        # Ensure we have the correct number of arguments.
        function_arguments = {
            "ABS":              [1],
            "BITS":             [1],
            "CBRT":             [1],
            "CEILING":          [1],
            "FACTOR10":         [1],
            "FLOOR":            [1],
            "LOG10":            [1],
            "ROUND":            [1],
            "SQRT":             [1],
            "ROOT":             [2],
            "RANDOM_UNIFORM":   [2],
            "RANDOM_GAUSSIAN":  [2],
            "RANDOM_POISSON":   [1],
            "TREE_PARENT":      [1, 2],
            "TREE_CHILD":       [2, 3],
            "MESH_NEIGHBOR":    [3, 5, 7],
            "TORUS_NEIGHBOR":   [3, 5, 7],
            "MESH_COORDINATE":  [3, 4, 5],
            "TORUS_COORDINATE": [3, 4, 5],
            "KNOMIAL_PARENT":   [1, 2, 3],
            "KNOMIAL_CHILD":    [2, 3, 4],
            "KNOMIAL_CHILDREN": [1, 2, 3]
        }
        try:
            valid_num_args = function_arguments[func_name]
            if num_args not in valid_num_args:
                if len(valid_num_args) == 1:
                    expected_args = "%d argument(s)" % valid_num_args
                else:
                    expected_args = string.join(map(str, valid_num_args[:-1]), ", ") + \
                                    " or %d arguments" % valid_num_args[-1]
                self.errmsg.error_fatal("%s expects %s but was given %d" %
                                        (func_name, expected_args, num_args))
        except KeyError:
            self.errmsg.error_internal("unknown number of arguments to %s" % func_name)

        # All of the mesh and torus neighbor functions map to the same
        # library call.  Patch the argument list accordingly.
        if func_name in ["MESH_NEIGHBOR", "TORUS_NEIGHBOR"]:
            gtask = arguments[0]
            gtorus = str(int(func_name=="TORUS_NEIGHBOR"))
            gwidth = arguments[1]
            gheight = "1"
            gdepth = "1"
            gdeltax = arguments[2]
            gdeltay = "0"
            gdeltaz = "0"
            if num_args >= 5:
                gheight = arguments[3]
                gdeltay = arguments[4]
            if num_args >= 7:
                gdepth = arguments[5]
                gdeltaz = arguments[6]
            func_name = "GRID_NEIGHBOR"
            arguments = [gtask, gtorus,
                         gwidth, gheight, gdepth,
                         gdeltax, gdeltay, gdeltaz]
        # All of the mesh and torus coordinate functions map to the same
        # library call.  Patch the argument list accordingly.
        elif func_name in ["MESH_COORDINATE", "TORUS_COORDINATE"]:
            gtask = arguments[0]
            gcoord = arguments[1]
            gwidth = arguments[2]
            gheight = "1"
            gdepth = "1"
            if num_args >= 4:
                gheight = arguments[3]
            if num_args >= 5:
                gdepth = arguments[4]
            func_name = "GRID_COORD"
            arguments = [gtask, gcoord,
                         gwidth, gheight, gdepth]
        # Tree arity defaults to 2.
        elif func_name in ["TREE_PARENT", "TREE_CHILD"]:
            if num_args == valid_num_args[0]:
                arguments.append("2")
        # k defaults to 2 in k-nomial tree and the number of tasks
        # defaults to num_tasks.
        elif func_name[:8] == "KNOMIAL_":
            if num_args < valid_num_args[-2]:
                arguments.append("2")
            if num_args < valid_num_args[-1]:
                arguments.append("var_num_tasks")
            if func_name == "KNOMIAL_CHILD":
                arguments.append("0")
            elif func_name == "KNOMIAL_CHILDREN":
                arguments.insert(1, "0")
                arguments.append("1")
                func_name = "KNOMIAL_CHILD"
        # Keep track of our use of random numbers.
        elif func_name[:7] == "RANDOM_":
            self.program_uses_randomness = max(self.program_uses_randomness, 1)

        # Return a C function call.
        self.push("ncptl_func_%s(%s)" %
                  (string.lower(func_name), string.join(arguments, ",")))

    def n_real(self, node):
        "Evaluate an expression in floating-point context."
        expression = self.pop()
        self.push("CONC_DBL2INT(%s)" %
                  self.code_make_expression_fp(expression, floating_context=1))

    def n_aggregate_expr(self, node):
        aggr_expr = self.pop()
        if node.attr == "no_aggregate":
            aggr_func = None
        else:
            aggr_func = self.pop()
        self.push(aggr_func)
        self.push(aggr_expr)


    #----------------------------#
    # Top-level task and related #
    # code-generating functions  #
    #----------------------------#

    def code_counter_stmt(self, operation, node):
        "Push, pop, or resume all of the var_total_* variables."
        if operation == "STORE" or operation == "RESTORE":
            self.stores_restores_vars = 1
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS %s THEIR COUNTERS */" % operation, istack)
        else:
            self.push(" /* TASKS %s %s THEIR COUNTERS */" % (source_task[1], operation),
                      istack)
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_%s" % operation, declare="(void)", stack=istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def code_output_header_comments(self, node):
        "Output some boilerplate header text."
        if self.filesource == "<command line>":
            inputfile = "the source program"
        else:
            inputfile = os.path.abspath(self.filesource)
        self.pushmany([
            "/" + "*" * 70,
            " * This file was generated by coNCePTuaL on %s" %
            time.asctime(time.localtime(time.time())),
            " * using the %s backend (%s)." %
            (self.backend_name, self.backend_desc),
            " * Do not modify this file; modify %s instead." % inputfile] +
                      self.invoke_hook("code_output_header_comments_EXTRA", locals()))
        if self.sourcecode:
            self.pushmany([
                " *",
                " * Entire source program",
                " * ---------------------"])
            for oneline in string.split(string.strip(self.sourcecode), "\n"):
                self.push(" *   %s" % self.clean_comments(oneline))
        self.push(" " + "*" * 70 + "/")

    def code_specify_include_files(self, node):
        "Load all of the C header files the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/*****************",
            " * Include files *",
            " *****************/",
            ""])

        # Enable hooks both before and after the common includes.
        self.pushmany(self.invoke_hook("code_specify_include_files_PRE", locals(),
                                       before=[
            "/* Header files specific to the %s backend */" % self.backend_name],
                                       after=[""]))
        self.pushmany([
            "/* Header files needed by all C-based backends */",
            "#include <stdio.h>",
            "#include <string.h>",
            "#include <ncptl/ncptl.h>"])
        self.pushmany(self.invoke_hook("code_specify_include_files_POST", locals(),
                                       before=[
            "",
            "/* Header files specific to the %s backend */" % self.backend_name]))

    def code_define_macros(self, node):
        "Define all of the C macros the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/**********",
            " * Macros *",
            " **********/",
            ""])

        # Enable hooks both before and after the common macros.
        self.pushmany(self.invoke_hook("code_define_macros_PRE", locals(),
                                       after=[""]))
        self.pushmany([
            "/* Define the maximum loop trip count that we're willing to unroll fully. */",
            "#define CONC_MAX_UNROLL 5",
            "",
            "/* Specify the number of trial iterations in each FOR <time> loop. */",
            "#define CONC_FOR_TIME_TRIALS 10",
            "",
            "/* Define a macro that rounds a double to a ncptl_int. */",
            "#define CONC_DBL2INT(D) ((ncptl_int)((D)+0.5))"])
        self.pushmany(self.invoke_hook("code_define_macros_POST", locals(),
                                       before=[""]))

    def code_declare_datatypes(self, node):
        "Declare all of the C datatypes the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/*********************",
            " * Type declarations *",
            " *********************/",
            ""])
        self.pushmany(self.invoke_hook("code_declare_datatypes_PRE", locals(),
                                       after=[""]))

        # Enumerate all of the event types we plan to use.
        self.pushmany([
            "/* Define the type of event to perform. */",
            "typedef enum {",
            "EV_SEND,     /* Synchronous send */",
            "EV_ASEND,    /* Asynchronous send */",
            "EV_RECV,     /* Synchronous receive */",
            "EV_ARECV,    /* Asynchronous receive */",
            "EV_WAIT,     /* Wait for all asynchronous sends/receives to complete */",
            "EV_DELAY,    /* Spin or sleep */",
            "EV_TOUCH,    /* Touch a region of memory */",
            "EV_SYNC,     /* Barrier synchronization */",
            "EV_RESET,    /* Reset counters */",
            "EV_STORE,    /* Store all counters' current values */",
            "EV_RESTORE,  /* Restore the previously pushed counter values */",
            "EV_FLUSH,    /* Compute aggregate functions for log-file columns */",
            "EV_MCAST,    /* Synchronous multicast */",
            "EV_REDUCE,   /* Reduction with or without a subsequent multicast */",
            "EV_BTIME,    /* Beginning of a timed loop */",
            "EV_ETIME,    /* Ending of a timed loop */",
            "EV_REPEAT,   /* Repeatedly process the next N events */",
            "EV_SUPPRESS, /* Suppress writing to the log and standard output */",
            "EV_NEWSTMT,  /* Beginning of a new top-level statement */",
            "EV_CODE,     /* None of the above */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_EXTRA_EVS", locals()))
        self.pushmany([
            "NUM_EVS      /* Number of event types in CONC_EVENT_TYPE */",
            "} CONC_EVENT_TYPE;",
            ""])

        # Declare each event type in turn.  Note that derived classes
        # can easily insert backend-specific elements into any
        # datatype.
        self.pushmany([
            "/* Describe a synchronous or asynchronous send event. */",
            "typedef struct {",
            "ncptl_int dest;         /* Destination task */",
            "ncptl_int size;         /* Number of bytes to send */",
            "ncptl_int alignment;    /* Message alignment (in bytes) */",
            "ncptl_int pendingsends; /* # of outstanding sends */",
            "ncptl_int pendingrecvs; /* # of outstanding receives */",
            "ncptl_int buffernum;    /* Buffer # to send from */",
            "int misaligned;         /* 1=misaligned from a page; 0=align as specified */",
            "int touching;           /* 1=touch every word before sending */",
            "int verification;       /* 1=fill message buffer with known contents */",
            "void *buffer;           /* Pointer to message memory */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_SEND_STATE", locals()))
        self.pushmany([
            "} CONC_SEND_EVENT;",
            "",
            "/* Describe a synchronous or asynchronous receive event. */",
            "typedef struct {",
            "ncptl_int source;       /* Source task */",
            "ncptl_int size;         /* Number of bytes to receive */",
            "ncptl_int alignment;    /* Message alignment (in bytes) */",
            "ncptl_int pendingsends; /* # of outstanding sends */",
            "ncptl_int pendingrecvs; /* # of outstanding receives */",
            "ncptl_int buffernum;    /* Buffer # to receive into */",
            "int misaligned;         /* 1=misaligned from a page; 0=align as specified */",
            "int touching;           /* 1=touch every word after reception */",
            "int verification;       /* 1=verify that all bits are correct */",
            "void *buffer;           /* Pointer to message memory */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_RECV_STATE", locals()))
        self.pushmany([
            "} CONC_RECV_EVENT;",
            "",
            "/* Describe a wait-for-asynchronous-completions event. */",
            "typedef struct {",
            "ncptl_int numsends;     /* # of sends we expect to complete. */",
            "ncptl_int numrecvs;     /* # of receives we expect to complete. */",
            "ncptl_int numrecvbytes; /* # of bytes we expect to receive-complete */",
            "ncptl_int *touchedlist;    /* List of receives that need to be touched */",
            "ncptl_int numtouches;         /* # of elements in the above */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_WAIT_STATE", locals()))
        self.pushmany([
            "} CONC_WAIT_EVENT;",
            "",
            "/* Describe a spin or sleep delay. */",
            "typedef struct {",
            "uint64_t microseconds;  /* Length of delay in microseconds */",
            "int spin0sleep1;        /* 0=spin; 1=sleep */",
            "} CONC_DELAY_EVENT;",
            "",
            "/* Describe a barrier synchronization event. */",
            "typedef struct {"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_SYNC_STATE", locals(),
                                       alternate=["int notused;            /* Ensure we don't define an empty struct. */"]))
        self.pushmany([
            "} CONC_SYNC_EVENT;",
            "",
            "/* Describe a walk over a memory-region. */",
            "typedef struct {",
            "ncptl_int regionbytes;  /* Size in bytes of the region to touch */",
            "ncptl_int bytestride;   /* Stride in bytes to touch */",
            "ncptl_int numaccesses;  /* Number of words to touch */",
            "ncptl_int wordsize;     /* Size in bytes of each touch */",
            "ncptl_int firstbyte;    /* Byte offset of the first byte to touch */",
            "} CONC_TOUCH_EVENT;",
            "",
            "/* Describe a synchronous multicast event. */",
            "typedef struct {",
            "ncptl_int source;       /* Source task */",
            "ncptl_int size;         /* Number of bytes to send */",
            "ncptl_int alignment;    /* Message alignment (in bytes) */",
            "ncptl_int pendingsends; /* # of outstanding sends */",
            "ncptl_int pendingrecvs; /* # of outstanding receives */",
            "ncptl_int buffernum;    /* Buffer # to send/receive from */",
            "int misaligned;         /* 1=misaligned from a page; 0=align as specified */",
            "int touching;           /* 1=touch every word before sending */",
            "int verification;       /* 1=verify that all bits are correct */",
            "void *buffer;           /* Pointer to message memory */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_MCAST_STATE", locals()))
        self.pushmany([
            "} CONC_MCAST_EVENT;",
            "",
            "/* Describe a reduction event. */",
            "typedef struct {",
            "ncptl_int numitems;     /* # of items to reduce */",
            "ncptl_int itemsize;     /* # of bytes per item */",
            "ncptl_int alignment;    /* Message alignment (in bytes) */",
            "ncptl_int pendingsends; /* # of outstanding sends */",
            "ncptl_int pendingrecvs; /* # of outstanding receives */",
            "ncptl_int buffernum;    /* Buffer # to send/receive from */",
            "int misaligned;         /* 1=misaligned from a page; 0=align as specified */",
            "int touching;           /* 1=touch every word before sending/after receiving */",
            "int sending;            /* 1=we're a sender */",
            "int receiving;          /* 1=we're a receiver */",
            "void *buffer;           /* Pointer to message memory */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_REDUCE_STATE", locals()))
        self.pushmany([
            "} CONC_REDUCE_EVENT;",
            "",
            "/* Describe an event representing the beginning of a timed loop. */",
            "typedef struct {",
            "uint64_t usecs;         /* Requested loop duration */",
            "uint64_t starttime;     /* Time at which the loop state last changed */",
            "uint64_t itersleft;     /* # of iterations remaining */",
            "uint64_t previters;     /* # of iterations we performed last time */",
            "int prev_quiet;         /* Previous value of suppress_output */",
            "int timing_trial;       /* 1=performing a timing trial; 0=running for real */",
            "volatile int finished;  /* 1=time has expired; 0=still ticking */"])
        for var in self.referenced_exported_vars.keys():
            if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                self.push("ncptl_int %s;   /* Cached copy of %s to restore after the trial runs */" %
                          (var, var))
        self.pushmany([
            "} CONC_BTIME_EVENT;",
            "",
            "/* Describe an event representing the end of a timed loop. */",
            "typedef struct {",
            "ncptl_int begin_event;  /* Index into eventlist[] of the corresponding BTIME event */",
            "} CONC_ETIME_EVENT;",
            "",
            "/* Describe an event representing repetitions of subsequent events. */",
            "typedef struct {",
            "ncptl_int end_event;    /* Index into eventlist[] of the last event to repeat */",
            "ncptl_int numreps;      /* # of repetitions to perform */",
            "} CONC_REPEAT_EVENT;",
            "",
            "/* Describe an event representing output suppression (either on or off). */",
            "typedef struct conc_suppress_event {",
            "int quiet;              /* 0=allow output; 1=suppress it */",
            "int prev_quiet;         /* Previous value of suppress_output */",
            'ncptl_int matching_event;  /* Event ID of the "suppression on" event */'])
        for var in self.referenced_exported_vars.keys():
            if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                self.push("ncptl_int %s;   /* Cached copy of %s to restore after re-enabling output */" %
                          (var, var))
        if self.referenced_exported_vars.has_key("var_elapsed_usecs"):
            self.push("uint64_t stop_elapsed_usecs;   /* Time at which we suppressed output */")
        self.pushmany([
            "} CONC_SUPPRESS_EVENT;",
            "",
            "/* Describe an event representing arbitrary code to execute at run time. */",
            "typedef struct {",
            "ncptl_int number;       /* Unique number corresponding to a specific piece of code */"])
        for var in self.referenced_vars.keys():
            self.push("ncptl_int %s;   /* Copy of %s to use within a piece of code */" %
                      (var, var))
        self.pushmany([
            "} CONC_CODE_EVENT;",
            ""])

        # Declare a datatype representing an arbitrary event.
        self.pushmany([
            "/* Describe an arbitrary coNCePTuaL event. */",
            "typedef struct {",
            "CONC_EVENT_TYPE type;          /* Type of event */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_EXTRA_EVENT_STATE", locals()))
        self.pushmany([
            "union {",
            "CONC_SEND_EVENT send;          /* Send state */",
            "CONC_RECV_EVENT recv;          /* Receive state */",
            "CONC_WAIT_EVENT wait;          /* Wait-for-completions state */",
            "CONC_DELAY_EVENT delay;        /* State for spins and sleeps */",
            "CONC_TOUCH_EVENT touch;        /* State for memory touching */",
            "CONC_SYNC_EVENT sync;          /* Synchronization state */",
            "CONC_MCAST_EVENT mcast;        /* Multicast state */",
            "CONC_REDUCE_EVENT reduce;      /* Reduction state */",
            "CONC_BTIME_EVENT btime;        /* Timed-loop state */",
            "CONC_ETIME_EVENT etime;        /* Additional timed-loop state */",
            "CONC_REPEAT_EVENT rep;         /* Repeated-events state */",
            "CONC_SUPPRESS_EVENT suppress;  /* State for suppressing output */",
            "CONC_CODE_EVENT code;          /* State for arbitrary code */"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_EXTRA_EVENTS", locals()))
        self.pushmany([
            "} s;",
            "} CONC_EVENT;",
            ""])

        # Optionally declare a type that holds all referenced exported
        # variables.
        if self.stores_restores_vars:
            self.pushmany([
                    "/* Provide storage to hold copies of all exported variables",
                    " * used -- except var_num_tasks, which never changes. */",
                    "typedef struct {"])
            self.code_declare_var(type="uint64_t",
                                  name="store_time",
                                  comment="Time at which these variables were stored")
            self.code_declare_var(type="uint64_t",
                                  name="starttime",
                                  comment="Time of last clock reset before store_time")
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.code_declare_var(name=var[4:],
                                          comment=self.exported_vars[var][1])
            self.push("} EXPORTED_VARS;")
            self.push("")

        # Declare all of the other datatypes the generated code may need.
        self.pushmany([
            "/* Fully specify an arbitrary for() loop (used by FOR EACH). */",
            "typedef struct {",
            "int integral;        /* 1=integral values; 0=floating-point values */",
            "enum {               /* Comparison of loop variable to end variable */",
            "CONC_LEQ,                /* Increasing progression */",
            "CONC_GEQ                 /* Decreasing progression */",
            "} comparator;",
            "enum {               /* How to increment the loop variable */",
            "CONC_ADD,                /* Arithmetically */",
            "CONC_MULT,               /* Geometrically increasing */",
            "CONC_DIV                 /* Geometrically decreasing */",
            "} increment;",
            "union {",
            "struct {",
            "ncptl_int loopvar;   /* Loop variable */",
            "ncptl_int prev_loopvar; /* Previous value of loop variable */",
            "ncptl_int startval;  /* Initial value of loop variable */",
            "ncptl_int endval;    /* Value not to exceed */",
            "ncptl_int incval;    /* Loop-variable increment */",
            "} i;",
            "struct {",
            "double loopvar;      /* Loop variable */",
            "double prev_loopvar; /* Previous value of loop variable */",
            "double startval;     /* Initial value of loop variable */",
            "double endval;       /* Value not to exceed */",
            "double incval;       /* Loop-variable increment */",
            "} d;",
            "} u;",
            "} LOOPBOUNDS;"])
        self.pushmany(self.invoke_hook("code_declare_datatypes_POST", locals(),
                                       before=[""]))

    def code_declare_globals(self, node):
        "Declare all of the C global variables the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/********************",
            " * Global variables *",
            " ********************/",
            ""])

        # Declare all of the exported variables, which are maintained
        # automatically by the code generator.
        self.push("/* Variables exported to coNCePTuaL programs */")
        for variable, meaning in self.exported_vars.items():
            self.push("static %s %s = %d;   /* %s */" %
                      (meaning[0], variable, int(variable=="var_num_tasks"), meaning[1]))
        self.push("")

        # Create a dummy variable to help silence whiny compilers.
        self.push("/* Dummy variable to help mark other variables as used */")
        self.pushmany([
            "union {",
            "ncptl_int ni;",
            "int i;",
            "void *vp;"])
        self.pushmany(self.invoke_hook("code_declare_globals_DUMMY_VAR", locals()))
        self.pushmany([
            "} conc_dummy_var;",
            ""])

        # Declare all of the boilerplate variables, both generic C and
        # backend-specific.
        self.pushmany([
            "/* Variables used internally by boilerplate code */",
            "static uint64_t starttime;   /* Time the clock was last reset (microseconds) */",
            "static ncptl_int pendingrecvs = 0;   /* Current # of outstanding receives */",
            "static ncptl_int pendingrecvbytes = 0; /* Current # of bytes in outstanding receives */",
            "static NCPTL_QUEUE *touchedqueue;      /* Queue of asynchronous receives to touch */",
            "static ncptl_int pendingsends = 0;   /* Current # of outstanding sends */",
            "static NCPTL_QUEUE *eventqueue;   /* List of coNCePTuaL events to perform */",
            "static int within_time_loop = 0;   /* 1=we're within a FOR <time> loop */",
            "static int suppress_output = 0;    /* 1=suppress output to stdout and the log file */",
            "static void *touch_region = NULL;   /* Memory region to touch */",
            "static ncptl_int touch_region_size = 0;   /* # of bytes in the above */",
            "static int virtrank;    /* This task's virtual rank in the computation */",
            "static int physrank;    /* This task's physical rank in the computation */",
            "static NCPTL_VIRT_PHYS_MAP *procmap;  /* Virtual to physical rank mapping */"])
        if self.program_uses_randomness >= 1:
            self.push("static ncptl_int random_seed;   /* Seed for the random-number generator */")
        if self.program_uses_log_file:
            self.pushmany([
                "static NCPTL_LOG_FILE_STATE *logstate;   /* Opaque object representing all log-file state */",
                "static char *logfile_uuid;   /* Execution UUID to write to every log file */"])
        if self.stores_restores_vars:
            self.push("static NCPTL_QUEUE *expvarstack;   /* Stack of exported-variable values */")
        self.pushmany([
            "static char *logfiletmpl;   /* Template for the log file's name */",
            "static char *logfiletmpl_default;   /* Default value of the above */"])
        if self.define_eventnames:
            self.push("static char *eventnames[NUM_EVS];   /* Name of each event */")
        self.pushmany(self.invoke_hook("code_declare_globals_EXTRA", locals(),
                                       before=[
            "",
            "/* Global variables specific to the %s backend */" % self.backend_name]))

        # Declare variables corresponding to those in the user's code.
        if self.global_declarations:
            self.push("")
            self.push("/* Program-specific variables */")
            for decl in self.global_declarations:
                self.push(decl)

        # Declare variables and functions provided as literal code by one
        # or more BACKEND DECLARES statements.
        if self.backend_declarations:
            self.pushmany(["",
                           "/************************************",
                           " * Variables and functions declared *",
                           " * using BACKEND DECLARES           *",
                           " ************************************/",
                           ""])
            for decl in self.backend_declarations:
                self.push(decl)

    def code_def_small_funcs(self, node):
        "Declare various small functions we know we'll need."

        self.pushmany(self.invoke_hook("code_def_small_funcs_PRE", locals(),
                                       after=[""]))
        if self.program_uses_range_lists:
            self.pushmany([
                "/* Return 1 if a sequence loop will take at least one trip. */",
                "static int conc_seq_nonempty (LOOPBOUNDS *seq)",
                "{"])
            self.code_declare_var(name="startval",
                                  comment="Integer version of seq's startval element")
            self.code_declare_var(name="endval",
                                  comment="Integer version of seq's endval element")
            self.pushmany([
                "",
                "if (seq->integral) {",
                "startval = seq->u.i.startval;",
                "endval = seq->u.i.endval;",
                "}",
                "else {",
                "startval = CONC_DBL2INT (seq->u.d.startval);",
                "endval = CONC_DBL2INT (seq->u.d.endval);",
                "}",
                "switch (seq->comparator) {",
                "case CONC_LEQ:",
                "return startval <= endval;",
                "",
                "case CONC_GEQ:",
                "return startval >= endval;",
                "",
                "default:",
                'ncptl_fatal ("Internal error -- unknown comparator");',
                "}",
                "return -1;     /* Appease idiotic compilers. */",
                "}",
                "",
                "/* Initialize a sequence loop. */",
                "static void conc_seq_init (LOOPBOUNDS *seq)",
                "{",
                "if (seq->integral) {",
                "seq->u.i.loopvar = seq->u.i.startval;",
                "seq->u.i.prev_loopvar = seq->u.i.loopvar - 1;",
                "}",
                "else {",
                "seq->u.d.loopvar = seq->u.d.startval;",
                "seq->u.d.prev_loopvar = seq->u.d.loopvar - 1.0;",
                "}",
                "}",
                "",
                "/* Return 1 if a sequence loop should continue, 0 when finished. */",
                "static int conc_seq_continue (LOOPBOUNDS *seq)",
                "{"])
            self.code_declare_var(type="LOOPBOUNDS", name="seq_int",
                                  comment="Integer equivalent of *seq")
            self.pushmany([
                "if (seq->integral)",
                "seq_int = *seq;",
                "else {",
                "seq_int.u.i.loopvar = CONC_DBL2INT (seq->u.d.loopvar);",
                "seq_int.u.i.prev_loopvar = CONC_DBL2INT (seq->u.d.prev_loopvar);",
                "seq_int.u.i.endval = CONC_DBL2INT (seq->u.d.endval);",
                "}",
                "",
                "if (seq_int.u.i.loopvar == seq_int.u.i.prev_loopvar)",
                "return 0;",
                "switch (seq->comparator) {",
                "case CONC_LEQ:",
                "return seq_int.u.i.loopvar <= seq_int.u.i.endval;",
                "",
                "case CONC_GEQ:",
                "return seq_int.u.i.loopvar >= seq_int.u.i.endval;",
                "",
                "default:",
                'ncptl_fatal ("Internal error -- unknown comparator");',
                "}",
                "return -1;     /* Appease idiotic compilers. */",
                "}",
                "",
                "/* Proceed to the next iteration of a sequence loop. */",
                "static void conc_seq_next (LOOPBOUNDS *seq)",
                "{",
                "if (seq->integral) {",
                "seq->u.i.prev_loopvar = seq->u.i.loopvar;",
                "switch (seq->increment) {",
                "case CONC_ADD:",
                "seq->u.i.loopvar += seq->u.i.incval;",
                "break;",
                "",
                "case CONC_MULT:",
                "seq->u.i.loopvar *= seq->u.i.incval;",
                "break;",
                "",
                "case CONC_DIV:",
                "seq->u.i.loopvar /= seq->u.i.incval;",
                "break;",
                "",
                "default:",
                'ncptl_fatal ("Internal error -- unknown incrementer");',
                "}",
                "}",
                "else {",
                "seq->u.d.prev_loopvar = seq->u.d.loopvar;",
                "switch (seq->increment) {",
                "case CONC_ADD:",
                "seq->u.d.loopvar += seq->u.d.incval;",
                "break;",
                "",
                "case CONC_MULT:",
                "seq->u.d.loopvar *= seq->u.d.incval;",
                "break;",
                "",
                "case CONC_DIV:",
                "seq->u.d.loopvar /= seq->u.d.incval;",
                "break;",
                "",
                "default:",
                'ncptl_fatal ("Internal error -- unknown incrementer");',
                "}",
                "}",
                "}"])
        self.pushmany(self.invoke_hook("code_def_small_funcs_POST", locals(),
                                       before=[""]))

    def code_def_mark_used(self, node):
        "Declare a function to mark various variables as used."
        self.pushmany([
            "/* Inhibit the compiler from complaining that",
            " * certain variables are defined but not used.",
            " * This function should never be called. */",
            "void conc_mark_variables_used (void)",
            "{"])
        self.pushmany(self.invoke_hook("code_def_mark_used_PRE", locals()))
        for ni_var in self.exported_vars.keys() + ["pendingrecvbytes", "touch_region_size"]:
            self.push("conc_dummy_var.ni = %s;" % ni_var)
        self.pushmany([
            "conc_dummy_var.vp = touch_region;",
            "conc_dummy_var.i  = within_time_loop;",
            "conc_dummy_var.i  = suppress_output;"])
        self.pushmany(self.invoke_hook("code_def_mark_used_POST", locals()))
        self.push("}")

    def code_def_alloc_event(self, node):
        "Declare a function to allocate a new event."
        self.pushmany([
            "/* Allocate a new event of a given type and return a pointer to it. */",
            "static CONC_EVENT *conc_allocate_event (CONC_EVENT_TYPE type)",
            "{",
            "CONC_EVENT *newevent = (CONC_EVENT *) ncptl_queue_allocate (eventqueue);"])
        self.pushmany(self.invoke_hook("code_def_alloc_event_DECLS", locals()))
        self.push("")
        self.pushmany(self.invoke_hook("code_def_alloc_event_PRE", locals()))
        self.push("newevent->type = type;")
        self.pushmany(self.invoke_hook("code_def_alloc_event_POST", locals()))
        self.push("return newevent;")
        self.push("}")

    def code_def_exit_handler(self, node):
        "Declare an exit handler that gets called by exit()."
        self.pushmany([
            "/* Declare an exit handler that gets called automatically when the",
            " * program terminates, whether successfully or not. */",
            "static void conc_exit_handler (void)",
            "{"])
        self.pushmany(self.invoke_hook("code_def_exit_handler_BODY", locals()))
        self.push("}")

    def code_def_extra_funcs(self, node):
        "Declare any additional functions needed by the program."
        if self.extra_func_decls == []:
            return
        self.pushmany(self.extra_func_decls[0])
        for extra_func in self.extra_func_decls[1:]:
            self.push("")
            self.pushmany(extra_func)

    def code_def_init_decls(self,node):
        "Define a conc_initialize() function and declare function-local variables."

        # Start by declaring the function and the function-local variables.
        self.pushmany([
            "/* Initialize coNCePTuaL, the messaging layer, and this program itself. */",
            "static void conc_initialize (int argc, char *argv[])",
            "{",
            " /* Variables needed by all C-based backends */"])
        self.code_declare_var(type="CONC_EVENT *", name="eventlist",
                              comment="List of events to execute")
        self.code_declare_var(name="numevents", comment="Number of entries in eventlist[]")
        self.code_declare_var(type="int", name="help_only", rhs="0",
                              comment="1=User specified --help; save time by skipping ncptl_init()")
        self.code_declare_var(type="char *", name="argv0",
                              rhs="strrchr(argv[0], '/') ? strrchr(argv[0], '/')+1 : argv[0]",
                              comment="Base name of the executable program")
        if self.define_eventnames:
            self.code_declare_var(name="evdigits", rhs="ncptl_func_log10((ncptl_int)NUM_EVS)",
                                  comment="Number of digits in NUM_EVS")
        self.code_declare_var(type="int", name="i",
                              comment="Generic loop variable")
        self.pushmany(self.invoke_hook("code_def_init_decls_PRE", locals(),
                                       before=[
            "",
            " /* Variables specific to the %s backend */" % self.backend_name]))
        self.push("")

        # Declare all of our command-line arguments.
        self.push(" /* Declare all of our command-line arguments. */")
        self.push("NCPTL_CMDLINE arguments[] = {")
        for param in self.global_parameters[:-1]:
            vartype, ident, longform, shortform, description, defvalue = param
            self.push('{ %s, NULL, "%s", \'%s\', "%s", {0}},' %
                       (vartype, longform, shortform, description))
        vartype, ident, longform, shortform, description, defvalue = \
                 self.global_parameters[-1]
        self.push('{ %s, NULL, "%s", \'%s\', "%s", {0}}' %
                   (vartype, longform, shortform, description))
        self.push("};")

        # Prepare to output the coNCePTuaL source code as a C array.
        self.pushmany([
            "",
            " /* Incorporate the complete coNCePTuaL source code as an array",
            "  * for use by ncptl_log_write_prologue(). */"])
        if self.sourcecode:
            self.push("char *sourcecode[] = {")
            for oneline in string.split(string.strip(self.sourcecode), "\n"):
                self.push('"%s",' %
                          string.replace(string.replace(oneline, "\\", "\\\\"),
                                         '"', '\\"'))
            self.push("NULL")
            self.push("};")
        else:
            self.push("char **sourcecode = NULL;")
        self.pushmany(self.invoke_hook("code_def_init_decls_POST", locals(),
                                       before=[
            "",
            " /* Variables specific to the %s backend */" % self.backend_name]))

    def code_def_init_init(self,code):
        "Initialize the coNCePTuaL run-time library."

        self.pushmany([
            " /* As a special case, if the command line contains --help, then skip",
            "  * the coNCePTuaL initialization step. */",
            "for (i=1; i<argc; i++)",
            'if (!strcmp(argv[i], "--"))',
            "break;",
            "else",
            'if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-?")) {',
            'argv[1] = "-?";   /* Guaranteed to work, even with getopt() */',
            "help_only = 1;",
            "break;",
            "}"])
        self.pushmany(self.invoke_hook("code_def_init_init_PRE", locals(),
                                       before=[
            "",
            " /* Perform various initializations specific to the %s backend. */" % self.backend_name]))
        self.pushmany([
            "",
            " /* Initialize the coNCePTuaL run-time library. */",
            "if (!help_only)",
            "ncptl_init (NCPTL_RUN_TIME_VERSION, argv[0]);",
            "(void) atexit (conc_exit_handler);"])
        self.pushmany(self.invoke_hook("code_def_init_init_POST", locals()))

    def code_def_init_seed(self, node):
        "Choose an initial seed for the random-task-number generator."
        self.push(" /* Seed the random-task-number generator. */")
        self.pushmany(self.invoke_hook("code_def_init_seed_PRE", locals()))
        self.push("random_seed = ncptl_seed_random_task(random_seed, 0);")
        self.push("arguments[0].defaultvalue.intval = random_seed;")
        self.pushmany(self.invoke_hook("code_def_init_seed_POST", locals()))

    def code_def_init_cmd_line(self, node):
        "Parse the command line."

        # Prepare to parse the command line.
        self.push(" /* Plug variables and default values into the NCPTL_CMDLINE structure. */")
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_PRE_ARGS", locals()))
        short2index = {}
        for paramnum in range(0, len(self.global_parameters)):
            vartype, ident, longform, shortform, description, defvalue = \
                     self.global_parameters[paramnum]
            short2index[shortform] = paramnum
            self.push("arguments[%d].variable = (CMDLINE_VALUE *) &%s;" %
                       (paramnum, ident))
            if vartype == "NCPTL_TYPE_INT":
                self.push('arguments[%d].defaultvalue.intval = %s;' %
                           (paramnum, defvalue))
            elif vartype == "NCPTL_TYPE_STRING":
                if defvalue != "OVERWRITTEN":
                    self.push('arguments[%d].defaultvalue.stringval = "%s";' %
                              (paramnum, defvalue))
            else:
                self.errmsg.error_internal('command-line parameter is "%s"' %
                                           (self.thisfile, str(defvalue)))
        if short2index.has_key("L"):
            # The -L (or --logfile) option must be handled specially.
            # For consistency from the user's perspective, we *always*
            # accept this option, even if the program does not write
            # data to the log file, access the log-file database, or
            # compute aggregates.
            self.pushmany([
                "logfiletmpl_default = (char *) ncptl_malloc (strlen(argv0) + 15, 0);",
                'sprintf (logfiletmpl_default, "%s-%%p.log", argv0);',
                "arguments[%d].defaultvalue.stringval = logfiletmpl_default;" %
                short2index["L"]])
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_POST_ARGS", locals()))
        self.push("")

        # Parse the command line.
        self.push(" /* Parse the command line. */")
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_PRE_PARSE", locals()))
        self.pushmany([
            "ncptl_parse_command_line (argc, argv, arguments, sizeof(arguments)/sizeof(NCPTL_CMDLINE));",
            "if (help_only)",
            'ncptl_fatal ("Internal error in the c_generic backend: failed to exit after giving help");'])
        self.pushmany(self.invoke_hook("code_def_init_cmd_line_POST_PARSE", locals()))

    def code_def_init_eventnames(self, node):
        "Define a list of event names as strings."
        self.pushmany([
            " /* Store the name of every event we plan to execute. */",
            "for (i=0; i<NUM_EVS; i++)",
            "eventnames[i] = NULL;"])
        for event_name in self.events_used.keys():
            self.push('eventnames[%s] = "%s";' % (event_name, event_name[3:]))
        self.pushmany([
            "for (i=0; i<NUM_EVS; i++)",
            "if (!eventnames[i]) {",
            "eventnames[i] = ncptl_malloc (4+evdigits, 0);",
            'sprintf (eventnames[i], "?%d?", i);',
            "}"])

    def code_def_init_reseed(self, node):
        """
           Have task 0 broadcast the random-number seed to all of the
           other tasks.  All backends need to define
           code_def_init_reseed_BCAST in order to support random-task
           generation.  If program_uses_randomness indicates that
           broadcasts are not necessary, then we simply reseed locally
           using the current random-number seed.
        """
        if self.program_uses_randomness >= 2:
            self.push(" /* Broadcast the random-task-number generator's seed. */")
            self.pushmany(self.invoke_hook("code_def_init_reseed_BCAST", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_internal("the %s backend does not support A RANDOM TASK or A RANDOM PROCESSOR" %
                                                                             loc["self"].backend_name)))
        self.push("(void) ncptl_seed_random_task(random_seed, (ncptl_int)physrank);")

    def code_def_init_uuid(self, node):
        """
           Have task 0 generate and broadcast a log-file UUID to all
           of the other tasks.  All backends need to define
           code_def_init_uuid_BCAST in order to support log-file
           generation.
        """
        self.push(" /* Generate and broadcast a UUID. */")
        self.push("logfile_uuid = ncptl_log_generate_uuid();")
        self.pushmany(self.invoke_hook("code_def_init_uuid_BCAST", locals(),
                                       alternatepy=lambda loc:
                                       loc["self"].errmsg.error_internal("the %s backend does not support log-file generation" %
                                                                         loc["self"].backend_name)))

    def code_def_init_misc(self, node):
        "Initialize miscellaneous things."

        # Allocate memory for the virtual<-->physical rank mappings.
        self.pushmany([
            " /* Establish a mapping from (virtual) task IDs to (physical) ranks. */",
            "procmap = ncptl_allocate_task_map (var_num_tasks);",
            "virtrank = ncptl_physical_to_virtual (procmap, physrank);",
            ""])

        # Give the backend one last chance to call
        # ncptl_log_add_comment() before we invoke ncptl_log_open().
        self.pushmany(self.invoke_hook("code_def_init_misc_PRE_LOG_OPEN",
                                       locals(),
                                       before=[
            " /* Perform initializations specific to the %s backend. */" %
            self.backend_name],
                                       after=[""]))

        # Open the log file and write some prologue information.
        if self.program_uses_log_file:
            self.pushmany([
                " /* Open the log file and write some standard prologue information to it. */",
                "logstate = ncptl_log_open (logfiletmpl, physrank);",
                'ncptl_log_write_prologue (logstate, argv[0], logfile_uuid, "%s", "%s",' %
                (self.backend_name, self.backend_desc),
                "var_num_tasks,",
                "arguments, sizeof(arguments)/sizeof(NCPTL_CMDLINE),",
                "sourcecode);",
                "ncptl_free (logfile_uuid);",
                ""])

        # Allocate initial memory for some arrays.
        self.pushmany([
                " /* Allocate a variety of dynamically growing queues. */",
                "eventqueue = ncptl_queue_init (sizeof (CONC_EVENT));",
                "touchedqueue = ncptl_queue_init (sizeof (ncptl_int));"])
        if self.stores_restores_vars:
            self.push("expvarstack = ncptl_queue_init (sizeof (EXPORTED_VARS));")
        self.push("")

        # Allocate anything else that needs allocating.
        self.pushmany(self.invoke_hook("code_def_init_misc_EXTRA", locals(),
                                       before=[
            " /* Perform initializations specific to the %s backend. */" %
            self.backend_name],
                                       after=[""]))

        # Perform program-specific initialization.
        self.pushmany([
            " /****************************************************",
            "  * Generated, program-specific initialization code. *",
            "  ****************************************************/",
            ""])
        for icode in self.init_elements:
            self.pushmany(icode)


    def code_def_init_check_pending(self, node):
        "Abort the program if it will terminate with pending messages."

        self.pushmany([
            " /*************************",
            "  * More boilerplate code *",
            "  *************************/",
            "",
            " /* Abort if the program will terminate with pending messages. */"])
        self.pushmany(self.invoke_hook("code_def_init_check_pending_PRE", locals()))
        self.pushmany([
            "if (pendingsends && pendingrecvs)",
            'ncptl_fatal("Neglected to await the completion of %" NICS " asynchronous %s and %" NICS " asynchronous %s",',
            'pendingsends, pendingsends==1%s ? "send" : "sends",' % self.ncptl_int_suffix,
            'pendingrecvs, pendingrecvs==1%s ? "receive" : "receives");' % self.ncptl_int_suffix,
            "else",
            "if (pendingsends)",
            'ncptl_fatal("Neglected to await the completion of %" NICS " asynchronous %s",',
            'pendingsends, pendingsends==1%s ? "send" : "sends");' % self.ncptl_int_suffix,
            "else",
            "if (pendingrecvs)",
            'ncptl_fatal("Neglected to await the completion of %" NICS " asynchronous %s",',
            'pendingrecvs, pendingrecvs==1%s ? "receive" : "receives");' % self.ncptl_int_suffix])
        self.pushmany(self.invoke_hook("code_def_init_check_pending_POST", locals()))


    def code_def_init_msg_mem(self, node):
        "Allocate memory for message buffers."

        # Allocate message memory.
        msg_events = {"EV_SEND":   "send",
                      "EV_ASEND":  "send",
                      "EV_RECV":   "recv",
                      "EV_ARECV":  "recv",
                      "EV_MCAST":  "mcast",
                      "EV_REDUCE": "reduce"}
        self.pushmany([
            " /* Allocate memory for non-unique messages and asynchronous",
            "  * message handles now that we know how much memory we need",
            "  * to allocate. */",
            "eventlist = (CONC_EVENT *) ncptl_queue_contents (eventqueue, 0);",
            "numevents = ncptl_queue_length (eventqueue);"])
        self.pushmany(self.invoke_hook("code_def_init_msg_mem_PRE", locals()))
        self.pushmany([
            "for (i=0; i<numevents; i++) {",
            "CONC_EVENT *thisev = &eventlist[i];   /* Cache of the current event */",
            "switch (thisev->type) {"])
        for tag, field in msg_events.items():
            if self.events_used.has_key(tag):
                struct = "thisev->s.%s" % field
                if tag == "EV_REDUCE":
                    sizefield = "%s.numitems * %s.itemsize" % (struct, struct)
                else:
                    sizefield = "%s.size" % struct
                self.pushmany([
                    "case %s:" % tag,
                    "if (!%s.buffer)" % struct,
                    "%s.buffer = ncptl_malloc_message (%s," % (struct, sizefield),
                    "%s.alignment," % struct,
                    "%s.buffernum," % struct,
                    "%s.misaligned);" % struct])
                if tag != "EV_REDUCE":
                    self.pushmany([
                        "if (%s.verification)" % struct,
                        "ncptl_fill_buffer (%s.buffer, %s, -1);" % (struct, sizefield)])
                self.pushmany(self.invoke_hook("code_def_init_msg_mem_EACH_TAG", locals()))
                self.push("break;")
                self.push("")
        self.pushmany([
            "default:",
            "break;",
            "}",
            "}"])
        self.pushmany(self.invoke_hook("code_def_init_msg_mem_POST", locals(),
                                       before=[""]))
        self.push("}")

    def code_def_procev(self, node):
        "Define a conc_process_events function."

        self.pushmany([
            "/* Process a subset of the events in a given event list. */",
            "static void conc_process_events (CONC_EVENT *eventlist,",
            "ncptl_int firstev, ncptl_int lastev, ncptl_int numreps)",
            "{"])
        self.code_declare_var(type="CONC_EVENT *", name="thisev",
                              comment="Cache of the current event")
        self.code_declare_var(type="CONC_EVENT *", name="thisev_first",
                              rhs="&eventlist[firstev]",
                              comment="Cache of the first event")
        self.code_declare_var(name="i", comment="Iterate over events.")
        self.code_declare_var(name="j", comment="Iterate over repetitions.")
        self.pushmany(self.invoke_hook("code_def_procev_DECL", locals(),
                                       before=[
            "",
            " /* Declarations specific to the %s backend */" % self.backend_name]))
        self.pushmany(self.invoke_hook("code_def_procev_PRE", locals(),
                                       before=[
            "",
            " /* Event-processing code specific to the %s backend */" % self.backend_name]))
        self.pushmany([
            "",
            " /* Process from event firstev to event lastev (both inclusive). */",
            "for (j=numreps; j>0; j--)",
            "for (i=firstev, thisev=thisev_first; i<=lastev; i++, thisev++) {",
            " /* Declare variables needed by all C-based backends. */"])
        self.pushmany(self.invoke_hook("code_def_procev_EVENTS_DECL", locals(),
                                       before=[
            "",
            " /* Declare variables that are specific to the %s backend. */" %
            self.backend_name]))
        self.pushmany(self.invoke_hook("code_def_procev_PRE_SWITCH", locals(),
                                       before=[
            "",
            " /* Execute code specific to the %s backend. */" %
            self.backend_name]))
        self.pushmany([
            "",
            " /* Process a single event. */",
            "switch (thisev->type) {"])
        self.code_def_procev_send(node)
        self.code_def_procev_asend(node)
        self.code_def_procev_recv(node)
        self.code_def_procev_arecv(node)
        self.code_def_procev_wait(node)
        self.code_def_procev_sync(node)
        self.code_def_procev_mcast(node)
        self.code_def_procev_reduce(node)
        self.code_def_procev_delay(node)
        self.code_def_procev_touch(node)
        self.code_def_procev_reset(node)
        self.code_def_procev_store(node)
        self.code_def_procev_restore(node)
        self.code_def_procev_flush(node)
        self.code_def_procev_btime(node)
        self.code_def_procev_etime(node)
        self.code_def_procev_suppress(node)
        self.code_def_procev_repeat(node)
        self.code_def_procev_newstmt(node)
        self.pushmany(self.invoke_hook("code_def_procev_EXTRA_EVENTS", locals()))
        self.code_def_procev_code(node)
        self.pushmany([
            "default:",
            " /* The c_generic backend or the %s backend must be broken. */" %
            self.backend_name,
            'ncptl_fatal ("Internal error: unknown event type %d", thisev->type);',
            "break;",
            "}"])

        self.pushmany(self.invoke_hook("code_def_procev_POST_SWITCH", locals(),
                                       before=[
            "",
            " /* Execute code specific to the %s backend. */" %
            self.backend_name]))
        self.push("}")
        self.pushmany(self.invoke_hook("code_def_procev_POST", locals(),
                                       before=[
            " /* Event-processing code specific to the %s backend */" % self.backend_name],
                                       after=[""]))
        self.push("}")

    def code_def_finalize(self, node):
        "Define a conc_finalize function."

        self.pushmany([
            "/* Finish up cleanly and return a status code. */",
            "static int conc_finalize (void)",
            "{"])
        self.code_declare_var(type="int", name="exitcode", rhs="0",
                              comment="Program exit code (to pass to exit())")
        self.pushmany(self.invoke_hook("code_def_finalize_DECL", locals(),
                                       before=[
            "",
            " /* Declarations specific to the %s backend */" % self.backend_name],
                                       after=[""]))
        self.pushmany(self.invoke_hook("code_def_finalize_PRE", locals(),
                                       before=[
            " /* Finalization code specific to the %s backend */" % self.backend_name],
                                       after=[""]))
        if self.program_uses_log_file:
            self.pushmany([
                " /* Write a standard epilogue to the log file. */",
                "ncptl_log_commit_data (logstate);",
                "ncptl_log_write_epilogue (logstate);",
                "ncptl_log_close (logstate);",
                ""])
        self.pushmany([
            " /* Inform the run-time library that it's no longer needed. */",
            "ncptl_queue_empty (eventqueue);",
            "ncptl_free (eventqueue);",
            "ncptl_finalize();",
            ""])
        self.pushmany(self.invoke_hook("code_def_finalize_POST", locals(),
                                       before=[
            " /* Finalization code specific to the %s backend */" % self.backend_name],
                                       after=[""]))
        self.pushmany([
            " /* Return an exit status code. */",
            "return exitcode;",
            "}"])

    def code_define_functions(self, node):
        "Declare all of the C functions the generated code may need."

        # Output a section comment.
        self.pushmany([
            "/*************************",
            " * Function declarations *",
            " *************************/",
            ""])
        self.pushmany(self.invoke_hook("code_define_functions_PRE", locals(),
                                       after=[""]))

        # Declare various small functions we know we'll need.
        self.code_def_small_funcs(node)
        self.push("")
        self.code_def_mark_used(node)
        self.push("")
        self.code_def_alloc_event(node)
        self.push("")
        self.code_def_exit_handler(node)
        self.push("")

        # Declare some additional, program-specific functions if any.
        self.code_def_extra_funcs(node)
        self.push("")

        # Declare a great, big conc_initialize() function (with
        # abundant hooks for the backend) that initializes everything
        # that needs to be initialized.  Note that we provide three
        # locations in which to initialize the specific backend as
        # different backends may find different locations more
        # convenient.
        self.code_def_init_decls(node)
        self.push("")
        self.code_def_init_init(node)
        self.push("")
        self.pushmany(self.invoke_hook("code_define_functions_INIT_COMM_1", locals(),
                                       before=[
            " /* Initialize the communication routines needed by the %s backend. */" %
            self.backend_name],
                                       after=[""]))
        if self.program_uses_randomness >= 1:
            self.code_def_init_seed(node)
            self.push("")
        if self.program_uses_log_file:
            self.code_def_init_uuid(node)
            self.push("")
        self.pushmany(self.invoke_hook("code_define_functions_INIT_COMM_2", locals(),
                                       before=[
            " /* Initialize the communication routines needed by the %s backend. */" %
            self.backend_name],
                                       after=[""]))
        self.code_def_init_cmd_line(node)
        self.push("")
        if self.define_eventnames:
            self.code_def_init_eventnames(node)
            self.push("")
        self.pushmany(self.invoke_hook("code_define_functions_INIT_COMM_3", locals(),
                                       before=[
            " /* Initialize the communication routines needed by the %s backend. */" %
            self.backend_name],
                                       after=[""]))
        if self.program_uses_randomness >= 1:
            self.code_def_init_reseed(node)
            self.push("")
        self.code_def_init_misc(node)
        self.push("")
        self.code_def_init_check_pending(node)
        self.push("")
        self.code_def_init_msg_mem(node)
        self.push("")

        # Define a conc_process_events() function.
        self.code_def_procev(node)
        self.push("")

        # Define a conc_finalize() function.
        self.code_def_finalize(node)
        self.push("")
        self.pushmany(self.invoke_hook("code_define_functions_POST", locals(),
                                       after=[""]))

    def code_def_procev_send(self, node):
        "Process an EV_SEND event."
        if self.events_used.has_key("EV_SEND"):
            self.pushmany([
                "case EV_SEND:",
                " /* Synchronous send */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.send.touching)",
                    "ncptl_touch_data (thisev->s.send.buffer, thisev->s.send.size);",
                    "else",
                    "if (thisev->s.send.verification)",
                    "ncptl_fill_buffer (thisev->s.send.buffer, thisev->s.send.size, 1);"])
            self.pushmany(self.invoke_hook("code_def_procev_send_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support SENDS" %
                                                                          loc["self"].backend_name)))
            self.code_update_exported_vars(["var_bytes_sent",
                                            "var_total_bytes",
                                            "var_msgs_sent",
                                            "var_total_msgs"],
                                           "send")
            self.pushmany(["break;", ""])

    def code_def_procev_asend(self, node):
        "Process an EV_ASEND event."
        if self.events_used.has_key("EV_ASEND"):
            self.pushmany([
                "case EV_ASEND:",
                " /* Asynchronous send */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.send.touching)",
                    "ncptl_touch_data (thisev->s.send.buffer, thisev->s.send.size);",
                    "else",
                    "if (thisev->s.send.verification)",
                    "ncptl_fill_buffer (thisev->s.send.buffer, thisev->s.send.size, 1);"])
            self.pushmany(self.invoke_hook("code_def_procev_asend_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support ASYNCHRONOUSLY SENDS" %
                                                                          loc["self"].backend_name)))
            self.code_update_exported_vars(["var_bytes_sent",
                                            "var_total_bytes",
                                            "var_msgs_sent",
                                            "var_total_msgs"],
                                           "send")
            self.pushmany(["break;", ""])

    def code_def_procev_recv(self, node):
        "Process an EV_RECV event."
        if self.events_used.has_key("EV_RECV"):
            self.pushmany([
                "case EV_RECV:",
                " /* Synchronous receive */"])
            self.pushmany(self.invoke_hook("code_def_procev_recv_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support RECEIVES" %
                                                                          loc["self"].backend_name)))
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.recv.touching)",
                    "ncptl_touch_data (thisev->s.recv.buffer, thisev->s.recv.size);",
                    "else",
                    "if (thisev->s.recv.verification)",
                    "var_bit_errors += ncptl_verify (thisev->s.recv.buffer, thisev->s.recv.size);"])
            self.code_update_exported_vars(["var_bytes_received",
                                            "var_total_bytes",
                                            "var_msgs_received",
                                            "var_total_msgs"],
                                           "recv")
            self.pushmany(["break;", ""])

    def code_def_procev_arecv(self, node):
        "Process an EV_ARECV event."
        if self.events_used.has_key("EV_ARECV"):
            self.pushmany([
                "case EV_ARECV:",
                " /* Asynchronous receive */"])
            self.pushmany(self.invoke_hook("code_def_procev_arecv_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support ASYNCHRONOUSLY RECEIVES" %
                                                                          loc["self"].backend_name)))
            self.pushmany(["break;", ""])

    def code_def_procev_wait(self, node):
        "Process an EV_WAIT event."
        if self.events_used.has_key("EV_WAIT"):
            self.pushmany([
                "case EV_WAIT:",
                " /* Wait for completion of all asynchronous events */",
                "if (thisev->s.wait.numsends) {"])
            self.pushmany(self.invoke_hook("code_def_procev_wait_BODY_SENDS", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support WAITS" %
                                                                          loc["self"].backend_name)))
            self.push("}")
            self.push("if (thisev->s.wait.numrecvs) {")
            if self.program_uses_touching:
                self.code_declare_var(name="touchev", comment="Event number")
                self.code_declare_var("ncptl_int *", name="touchedlist",
                                      rhs="thisev->s.wait.touchedlist")
                self.code_declare_var(name="numtouches",
                                      rhs="thisev->s.wait.numtouches")
            wait_overrides = {
                "var_bytes_received": "+= thisev->s.wait.numrecvbytes",
                "var_total_bytes":    "+= thisev->s.wait.numrecvbytes",
                "var_msgs_received":  "+= thisev->s.wait.numrecvs",
                "var_total_msgs":     "+= thisev->s.wait.numrecvs"
            }
            self.code_update_exported_vars(["var_bytes_received",
                                            "var_total_bytes",
                                            "var_msgs_received",
                                            "var_total_msgs"],
                                           "recv",
                                           overrides=wait_overrides)
            self.pushmany(self.invoke_hook("code_def_procev_wait_BODY_RECVS", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support WAITS" %
                                                                          loc["self"].backend_name)))
            if self.program_uses_touching:
                self.pushmany([
                    "for (touchev=0; touchev<numtouches; touchev++) {",
                    "CONC_RECV_EVENT *thisrecv = (CONC_RECV_EVENT *) &eventlist[touchedlist[touchev]].s.recv;",
                    "if (thisrecv->touching)",
                    "ncptl_touch_data (thisrecv->buffer, thisrecv->size);",
                    "else if (thisrecv->verification)",
                    "var_bit_errors += ncptl_verify (thisrecv->buffer, thisrecv->size);",
                    "else",
                    'ncptl_fatal ("Internal error: non-touch data was found on the touch list");',
                    "}"])
            self.pushmany([
                "}",
                "break;",
                ""])

    def code_def_procev_sync(self, node):
        "Process an EV_SYNC event."
        if self.events_used.has_key("EV_SYNC"):
            self.pushmany([
                "case EV_SYNC:",
                " /* Synchronize a subset of the tasks. */"])
            self.pushmany(self.invoke_hook("code_def_procev_sync_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support SYNCHRONIZE" %
                                                                          loc["self"].backend_name)))
            self.pushmany(["break;", ""])

    def code_def_procev_mcast(self, node):
        "Process an EV_MCAST event."
        if self.events_used.has_key("EV_MCAST"):
            self.pushmany([
                "case EV_MCAST:",
                " /* Synchronous multicast */"])
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.mcast.source == physrank) {",
                    " /* We're the sender */",
                    "if (thisev->s.mcast.touching)",
                    "ncptl_touch_data (thisev->s.mcast.buffer, thisev->s.mcast.size);",
                    "else",
                    "if (thisev->s.mcast.verification)",
                    "ncptl_fill_buffer (thisev->s.mcast.buffer, thisev->s.mcast.size, 1);",
                    "}"])
            self.pushmany(self.invoke_hook("code_def_procev_mcast_BODY", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support MULTICASTS" %
                                                                          loc["self"].backend_name)))
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.mcast.source != physrank) {",
                    " /* We're a receiver */",
                    "if (thisev->s.mcast.touching)",
                    "ncptl_touch_data (thisev->s.mcast.buffer, thisev->s.mcast.size);",
                    "else",
                    "if (thisev->s.mcast.verification)",
                    "var_bit_errors += ncptl_verify (thisev->s.mcast.buffer, thisev->s.mcast.size);",
                    "}"])
            self.push("break;")
            self.push("")

    def code_def_procev_reduce(self, node):
        "Process an EV_REDUCE event."
        if self.events_used.has_key("EV_REDUCE"):
            self.pushmany([
                "case EV_REDUCE:",
                " /* Data reduction */"])
            # The use of msgbuffer here is a hack to enable the c_mpi
            # backend to change the message buffer that gets touched
            # on the receive side.
            msgbuffer = "thisev->s.reduce.buffer"
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.reduce.sending)",
                    " /* We're a sender */",
                    "if (thisev->s.reduce.touching)",
                    "ncptl_touch_data (%s, thisev->s.reduce.numitems*thisev->s.reduce.itemsize);" % msgbuffer])
            localvars = locals()
            self.pushmany(self.invoke_hook("code_def_procev_reduce_BODY", localvars,
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support REDUCE" %
                                                                          loc["self"].backend_name)))
            msgbuffer = localvars["msgbuffer"]
            if self.program_uses_touching:
                self.pushmany([
                    "if (thisev->s.reduce.receiving)",
                    " /* We're a receiver */",
                    "if (thisev->s.reduce.touching)",
                    "ncptl_touch_data (%s, thisev->s.reduce.numitems*thisev->s.reduce.itemsize);" % msgbuffer])
            self.push("break;")
            self.push("")

    def code_def_procev_delay(self, node):
        "Process an EV_DELAY event."
        if self.events_used.has_key("EV_DELAY"):
            self.pushmany([
                "case EV_DELAY:",
                " /* Do nothing for a prescribed length of time. */",
                "ncptl_udelay (thisev->s.delay.microseconds, thisev->s.delay.spin0sleep1);",
                "break;",
                ""])

    def code_def_procev_touch(self, node):
        "Process an EV_TOUCH event."
        if self.events_used.has_key("EV_TOUCH"):
            self.pushmany([
                "case EV_TOUCH:",
                " /* Touch a set of bytes within a memory region. */",
                "ncptl_touch_memory (touch_region,",
                "thisev->s.touch.regionbytes,",
                "thisev->s.touch.wordsize,",
                "thisev->s.touch.firstbyte,",
                "thisev->s.touch.numaccesses,",
                "thisev->s.touch.bytestride);",
                "break;",
                ""])

    def code_def_procev_reset(self, node):
        "Process an EV_RESET event."
        if self.events_used.has_key("EV_RESET"):
            self.pushmany([
                "case EV_RESET:",
                " /* Reset all of the counters exported to coNCePTuaL programs. */"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("%s = 0;" % var)
            self.pushmany([
                "starttime = ncptl_time();",
                "break;",
                ""])

    def code_def_procev_store(self, node):
        "Process an EV_STORE event."
        if self.events_used.has_key("EV_STORE"):
            self.pushmany([
                "case EV_STORE:",
                " /* Push all of the counters exported to coNCePTuaL programs. */",
                "{"])
            self.code_clock_control("DECLARE")
            self.code_declare_var(type="EXPORTED_VARS *",
                                  name="saved_vars",
                                  rhs="(EXPORTED_VARS *) ncptl_queue_allocate (expvarstack)")
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("saved_vars->%s = %s;" % (var[4:], var))
            self.pushmany([
                    "saved_vars->starttime = starttime;",
                    "saved_vars->store_time = ncptl_time();",
                    "starttime += saved_vars->store_time - stop_elapsed_usecs;",
                    "}",
                    "break;",
                    ""])

    def code_def_procev_restore(self, node):
        "Process an EV_RESTORE event."
        if self.events_used.has_key("EV_RESTORE"):
            self.pushmany([
                "case EV_RESTORE:",
                " /* Pop all of the counters exported to coNCePTuaL programs. */",
                "{"])
            self.code_declare_var(type="EXPORTED_VARS *",
                                  name="saved_vars",
                                  rhs="(EXPORTED_VARS *) ncptl_queue_pop_tail (expvarstack)")
            self.pushmany([
                    "if (!saved_vars)",
                    'ncptl_fatal ("Task %d restored more counters than it stored", virtrank);'])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("%s = saved_vars->%s ;" % (var, var[4:]))
            self.pushmany([
                    "starttime = ncptl_time() - saved_vars->store_time + saved_vars->starttime;",
                    "}",
                    "break;",
                    ""])

    def code_def_procev_flush(self, node):
        "Process an EV_FLUSH event."
        if self.events_used.has_key("EV_FLUSH"):
            self.pushmany([
                "case EV_FLUSH:",
                " /* Force all aggregate functions to produce a result. */",
                "if (!suppress_output) {"])
            self.code_clock_control("DECLARE")
            self.code_clock_control("STOP")
            self.push("ncptl_log_compute_aggregates (logstate);"),
            self.code_clock_control("RESTART")
            self.pushmany([
                "}",
                "break;",
                ""])

    def code_def_procev_btime(self, node):
        "Process an EV_BTIME event."
        if self.events_used.has_key("EV_BTIME"):
            self.pushmany([
                "case EV_BTIME:",
                " /* Begin timed loop */",
                "{"])
            self.code_declare_var("CONC_BTIME_EVENT *", name="beginev",
                                  rhs="&thisev->s.btime",
                                  comment="Cache of the loop-begin event")
            self.pushmany([
                " /* Perform CONC_FOR_TIME_TRIALS training iterations. */",
                "beginev->previters = CONC_FOR_TIME_TRIALS;",
                "beginev->itersleft = CONC_FOR_TIME_TRIALS;",
                "beginev->timing_trial = 1;",
                "beginev->prev_quiet = suppress_output;",
                "suppress_output = 1;"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("beginev->%s = %s;" % (var, var))
            self.pushmany([
                "beginev->starttime = ncptl_time();",
                "}",
                "break;",
                ""])

    def code_def_procev_etime(self, node):
        "Process an EV_ETIME event."
        if self.events_used.has_key("EV_ETIME"):
            self.pushmany([
                "case EV_ETIME:",
                " /* End timed loop */",
                "{"])
            self.code_declare_var("CONC_BTIME_EVENT *", name="beginev",
                                  comment="Cache of the loop-begin event")
            self.pushmany([
                "",
                "beginev = &eventlist[thisev->s.etime.begin_event].s.btime;",
                "if (beginev->timing_trial) {",
                " /* We're currently performing some trial runs. */",
                "if (!--beginev->itersleft) {",
                " /* We just finished our trial runs. */"])
            self.code_declare_var("uint64_t", name="elapsedtime",
                                  rhs="ncptl_time() - beginev->starttime",
                                  comment="Time taken to perform the trial iterations")
            self.code_declare_var("uint64_t", name="minelapsedtime",
                                  comment="Minimum value of elapsedtime across all tasks")
            self.push("")
            self.push(" /* Acquire global agreement on the # of iterations that each task will execute. */")

            # The following hook needs to reduce all tasks'
            # elapsedtime to the global minimum across all tasks and
            # store the result in minelapsedtime.
            self.pushmany(self.invoke_hook("code_def_procev_etime_REDUCE_MIN", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support FOR <time>" %
                                                                          loc["self"].backend_name)))
            self.pushmany([
                "beginev->itersleft = (minelapsedtime<=0) ? 1 : (beginev->usecs*beginev->previters)/minelapsedtime;",
                "beginev->itersleft += beginev->itersleft/4 + 1;   /* Add a 25% fudge factor. */",
                "",
                " /* Determine if we need to perform another set of trial iterations. */",
                "if (minelapsedtime < beginev->usecs/100) {",
                " /* itersleft doesn't correspond to at least 1% of the desired execution",
                "  * time.  We therefore try again using 10X the number of iterations. */"])
            self.code_declare_var("uint64_t", name="now",
                                  comment="Current time in microseconds")
            self.pushmany([
                "beginev->previters *= 10;",
                "beginev->itersleft = beginev->previters;",
                "now = ncptl_time();",
                "starttime += now - beginev->starttime;",
                "beginev->starttime = now;",
                "}",
                "else {",
                " /* The trial iterations lasted for at least 1% of the desired execution",
                "  * time.  It's now safe to begin the timed iterations. */",
                "beginev->previters = beginev->itersleft;"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("%s = beginev->%s;" % (var, var))
            self.pushmany([
                "suppress_output = beginev->prev_quiet;",
                "beginev->timing_trial = 0;",
                "beginev->finished = 0;",
                "ncptl_set_flag_after_usecs (&beginev->finished, beginev->usecs);",
                "starttime += ncptl_time() - beginev->starttime;",
                "}",
                "}",
                "i = thisev->s.etime.begin_event;   /* Go to the beginning of the loop. */",
                "thisev = &eventlist[i];",
                "}",
                "else {",
                " /* Not training; running for real */",
                "if (!--beginev->itersleft && !beginev->finished)",
                " /* This is bad: we ran out of iterations before we ran out of time. */",
                "beginev->finished = 1;   /* Force time to expire. */",
                "if (beginev->finished == 1) {",
                " /* Time just expired -- save our state and continue. */",
                "beginev->starttime = ncptl_time();"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("beginev->%s = %s;" % (var, var))
            self.pushmany([
                "beginev->finished = 2;",
                "}",
                "if (beginev->itersleft) {",
                "i = thisev->s.etime.begin_event;   /* Do more iterations. */",
                "thisev = &eventlist[i];",
                "}",
                "else {",
                " /* All finished -- restore the counter state to what it was when time ran out. */"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("%s = beginev->%s;" % (var, var))
            self.pushmany([
                "starttime += ncptl_time() - beginev->starttime;",
                "}",
                "}",
                "}",
                "break;",
                ""])

    def code_def_procev_suppress(self, node):
        "Process an EV_SUPPRESS event."
        if self.events_used.has_key("EV_SUPPRESS"):
            self.pushmany([
                "case EV_SUPPRESS:",
                " /* Turn logging and outputting on or off. */",
                "if (thisev->s.suppress.quiet) {",
                " /* Suppress output. */",
                "thisev->s.suppress.prev_quiet = suppress_output;",
                "suppress_output = 1;"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("thisev->s.suppress.%s = %s;" % (var, var))
            if self.referenced_exported_vars.has_key("var_elapsed_usecs"):
                self.push("thisev->s.suppress.stop_elapsed_usecs = ncptl_time();")
            self.pushmany([
                "}",
                "else {",
                " /* Restore suppression to its previous state. */"])
            self.code_declare_var(type="CONC_SUPPRESS_EVENT *", name="matchev",
                                  rhs="&eventlist[thisev->s.suppress.matching_event].s.suppress",
                                  comment="Matching suppression event")
            self.pushmany([
                "suppress_output = matchev->prev_quiet;",
                "if (!suppress_output) {"])
            for var in self.referenced_exported_vars.keys():
                if var not in ["var_num_tasks", "var_elapsed_usecs"]:
                    self.push("%s = matchev->%s;" % (var, var))
            if self.referenced_exported_vars.has_key("var_elapsed_usecs"):
                self.push("starttime += ncptl_time() - matchev->stop_elapsed_usecs;")
            self.pushmany([
                "}",
                "}",
                "break;",
                ""])

    def code_def_procev_repeat(self, node):
        "Process an EV_REPEAT event."
        if self.events_used.has_key("EV_REPEAT"):
            self.push("case EV_REPEAT:")
            self.pushmany(self.invoke_hook("code_def_procev_repeat_BODY", locals(),
                                           before=[
                " /* Repeat-event code specific to the %s backend */" % self.backend_name],
                                           after=[""]))
            self.pushmany([
                " /* Repeatedly perform the next batch of events. */",
                "conc_process_events (eventlist, i+1, thisev->s.rep.end_event, thisev->s.rep.numreps);",
                "i = thisev->s.rep.end_event;",
                "thisev = &eventlist[i];",
                "break;",
                ""])

    def code_def_procev_newstmt(self, node):
        "Process an EV_NEWSTMT event."
        if self.events_used.has_key("EV_NEWSTMT"):
            self.push("case EV_NEWSTMT:")
            self.pushmany(self.invoke_hook("code_def_procev_newstmt_BODY", locals(),
                                           before=[
                " /* New-statement code specific to the %s backend */" % self.backend_name],
                                           after=[""]))
            self.pushmany([
                " /* Begin a new table in the log file. */",
                "if (!suppress_output) {"])
            self.code_clock_control("DECLARE")
            self.code_clock_control("STOP")
            self.push("ncptl_log_commit_data (logstate);"),
            self.code_clock_control("RESTART")
            self.pushmany([
                "}",
                "break;",
                ""])

    def code_def_procev_code(self, node):
        "Process an EV_CODE event."
        if self.events_used.has_key("EV_CODE"):
            self.pushmany([
                "case EV_CODE:",
                " /* Execute an arbitrary piece of code. */",
                "switch (thisev->s.code.number) {"])
            for chunknum in range(0, len(self.arbitrary_code)):
                self.push("case %d:" % chunknum)
                self.pushmany(self.arbitrary_code[chunknum])
                self.push("break;")
                self.push("")
            self.pushmany([
                "default:",
                " /* The C code generation module must be broken. */",
                'ncptl_fatal ("Internal error: unknown EV_CODE block %" NICS, thisev->s.code.number);',
                "break;",
                "}",
                "break;",
                ""])

    def code_define_main(self, node):
        "Declare a main() function for the generated code."

        # Output a section comment up to the opening curly brace.
        self.pushmany([
            "/" + "*"*73 + "/",
            "/" + "*"*29 + " MAIN ROUTINE " + "*"*30 + "/",
            "/" + "*"*73 + "/",
            "",
            "/* Program execution starts here. */",
            "int main (int argc, char *argv[])",
            "{"])

        # Declare all of the variables we might need within main().
        self.push(" /* Declare variables needed by all C-based backends. */")
        self.code_declare_var(type="CONC_EVENT *", name="eventlist",
                              comment="List of events to execute")
        self.code_declare_var(name="numevents", comment="Number of entries in eventlist[]")
        self.pushmany(self.invoke_hook("code_define_main_DECL", locals(),
                                       before=[
            "",
            " /* Declare variables that are specific to the %s backend. */" %
            self.backend_name]))
        self.push("")

        # Initialize the program.
        self.push(" /* ----- Initialization ----- */")
        self.pushmany(self.invoke_hook("code_define_main_PRE_INIT", locals()))
        self.push("conc_initialize (argc, argv);")
        self.push("eventlist = (CONC_EVENT *) ncptl_queue_contents (eventqueue, 0);")
        self.push("numevents = ncptl_queue_length (eventqueue);")
        self.pushmany(self.invoke_hook("code_define_main_POST_INIT", locals()))
        self.push("starttime = ncptl_time();")
        self.push("")

        # Process every event in the event list but include only the
        # cases we actually require.  All backends will need to define
        # the various code_def_*_BODY functions.
        self.push(" /* ----- Event-list processing ----- */")
        self.pushmany(self.invoke_hook("code_define_main_PRE_EVENTS", locals()))
        self.push("conc_process_events (eventlist, 0, numevents-1, 1);")
        self.pushmany(self.invoke_hook("code_define_main_POST_EVENTS", locals(),
                                       before=[""]))
        self.push("")

        # Finish up cleanly.
        self.pushmany([
            " /* ----- Finalization ----- */",
            "return conc_finalize();",
            "}"])

    def n_program(self, node):
        "Output a valid C program."

        # Sanity-check the code stack.
        if self.codestack:
            self.errmsg.error_internal("code stack is nonempty (contents: " +
                                       repr(self.codestack) + ")")
        self.push_marker()

        # Finalize the parameter list before we output code.
        self.global_parameters.insert(0, ("NCPTL_TYPE_STRING",
                                          "logfiletmpl", "logfile", "L",
                                          "Log-file template",
                                          "OVERWRITTEN"))
        if self.program_uses_randomness >= 1:
            self.global_parameters.insert(0, ("NCPTL_TYPE_INT",
                                              "random_seed", "seed", "S",
                                              "Seed for the random-number generator",
                                              "random_seed"))

        # Ensure we don't have any duplicate parameters.
        longname_list = {}
        for longname in map(lambda p: p[2], self.global_parameters) + ["comment", "no-trap"]:
            if longname_list.has_key(longname):
                self.errmsg.error_fatal("The --%s option is predefined and therefore not available to programs" % longname)
            longname_list[longname] = 1

        # Output some boilerplate header text.
        self.code_output_header_comments(node)
        self.push("")

        # Load all of the C include files we might need
        self.code_specify_include_files(node)
        self.push("")

        # Define various C helper macros.
        self.code_define_macros(node)
        self.push("")

        # Declare all of the C datatypes we might need.
        self.code_declare_datatypes(node)
        self.push("")

        # Declare all of our boilerplate global variables.
        self.code_declare_globals(node)
        self.push("")

        # Define all of the generic C and backend-specific functions
        # we might need.
        self.code_define_functions(node)

        # Begin a main() function.
        self.code_define_main(node)

        # Output everything we've accumulated so far.
        self.combine_to_marker()

    def n_version_decl(self, node):
        "Pop our version number off the stack."
        self.pop()

    def n_param_decl(self, node):
        "Specify that a variable originates from a command-line argument."
        defvalue = self.pop()
        shortform = self.pop()
        longform = self.pop()
        description = self.pop()
        ident = self.pop()
        self.code_declare_var("ncptl_int", name=ident,
                              comment="%s (command-line argument)" %
                              self.clean_comments(description[1:-1]),
                              stack=self.global_declarations)
        self.push(("NCPTL_TYPE_INT", ident, longform[3:-1], shortform[2],
                   description[1:-1], defvalue),
                  self.global_parameters)

    def n_backend_decl(self, node):
        """
             Inject literal C code (typically variable or function
             definitions) into the output file.
        """
        c_code = self.unquote_string(self.pop())
        self.pushmany(string.split(c_code, "\n"),
                      stack=self.backend_declarations)


    #--------------------#
    # Complex statements #
    #--------------------#

    def n_simple_stmt_list(self, node):
        "Perform a set of statements back-to-back but in separate scopes."
        istack = self.init_elements
        stmt_list = []
        for s in range(node.attr):
            stmt_list.insert(0, self.pop(istack))
        self.push(reduce(lambda s1, s2: s1 + [" /* THEN... */"] + s2, stmt_list), istack)

    def n_top_level_stmt(self, node):
        "Begin a new top-level statement by starting a new table in the log file."
        if self.program_uses_log_file:
            istack = self.init_elements
            self.push_marker(istack)
            self.push(" /* Begin a new top-level statement. */", istack)
            self.code_allocate_event("EV_NEWSTMT", declare="(void)",
                                     stack=istack)
            self.combine_to_marker(istack)
            self.logcolumn = 0

    def n_let_stmt(self, node):
        "Let-bind values to variables while performing a statement."
        numbindings = self.pop()
        bindlist = []
        for binding in range(numbindings):
            bindlist.insert(0, self.pop())

        # Define a new scope for each let-binding.
        wrapper_code = []
        self.push_marker(wrapper_code)
        opencurlies = 0
        for lval, rval in bindlist:
            # Because LET is evaluated at initialization time, none of
            # the dynamic variables have been assigned yet.  Until we
            # find a way to deal with dynamic variables in LET
            # statements we just won't allow them.  In addition,
            # dynamic variables may not be assigned to as that's just
            # too weird to deal with.
            for variable in self.exported_vars.keys():
                if re.search(r'\b%s\b' % variable, rval) and variable != "var_num_tasks":
                    self.errmsg.error_fatal("%s cannot be accessed from a LET statement" %
                                            variable[4:],
                                            lineno0=node.lineno0, lineno1=node.lineno1)
                if lval == variable:
                    self.errmsg.error_fatal("%s is a read-only variable" %
                                            variable[4:],
                                            lineno0=node.lineno0, lineno1=node.lineno1)
            # Wrap the initialization code within a let-binding.  One
            # tricky case we need to handle is when a variable is
            # let-bound to a function of its previous value.
            self.pushmany([
                "{",
                " /* LET %s BE %s WHILE... */" % (lval, rval)],
                          wrapper_code)
            if re.search(r'\b%s\b' % lval, rval):
                # Evil case: lval is defined in terms of itself; employ a
                # temporary variable to help out.
                temprvalvar = self.code_declare_var("ncptl_int",
                                                    rhs=rval,
                                                    suffix="expr",
                                                    stack=wrapper_code)
                self.code_declare_var("ncptl_int", name=lval, rhs=temprvalvar,
                                      stack=wrapper_code)
            else:
                # Easy case: lval is not defined in terms of itself.
                self.code_declare_var("ncptl_int", name=lval, rhs=rval,
                                      stack=wrapper_code)
            opencurlies = opencurlies + 1
        self.push("", wrapper_code)
        self.combine_to_marker(wrapper_code)
        self.wrap_stack(wrapper_code[0], ["}"]*opencurlies)

    # All derived backends will need to define n_for_count_SYNC_ALL
    # (to initialize thisev->sync) in order to support the PLUS A
    # SYNCHRONIZATION clause.
    def n_for_count(self, node):
        "Repeat a set of statements a given number of times."
        synchronize_afterwards = 0
        if len(node.kids) > 2:
            if node.attr == "synchronized":
                synchronize_afterwards = 1
            warmups = self.pop()
            count = self.pop()
        else:
            warmups = None
            count = self.pop()
        wrapper_code = []
        self.push_marker(wrapper_code)
        self.push(" /* FOR %s REPETITIONS... */" % count, wrapper_code)
        self.push("{", wrapper_code)

        # If the loop body uses the UNIQUE keyword or any form of
        # randomness we can't use REPEAT events; we have to fully
        # unroll the loop.  Otherwise, we'd get the same buffer or
        # random number every iteration, which is not what a user
        # would expect.
        eligible_to_unroll = not (hasattr(node, "sem_up_unique_messages")
                                  or hasattr(node, "sem_up_random_calls")
                                  or hasattr(node, "sem_up_random_task"))

        # Loop twice, once for warmups and once for the main repetitions.
        if warmups:
            self.code_declare_var(name="loopnum",
                                  comment="0=warmup repetitions; 1=main repetitions",
                                  stack=wrapper_code)
            self.push("", wrapper_code)
            self.push("for (loopnum=0%s; loopnum<2%s; loopnum++) {" %
                      (self.ncptl_int_suffix, self.ncptl_int_suffix),
                      wrapper_code)

        # Prepare to store a repeat event.
        if warmups:
            thiscount = "loopnum==0%s ? (%s) : (%s)" % (self.ncptl_int_suffix, warmups, count)
        else:
            thiscount = count
        self.code_declare_var(name="numreps", rhs=thiscount,
                              comment="Total # of repetitions to perform",
                              stack=wrapper_code)
        self.code_declare_var(type="int", name="unroll_loop",
                              rhs="numreps <= CONC_MAX_UNROLL",
                              comment="1=unroll loop; 0=use a REPEAT event",
                              stack=wrapper_code)
        self.code_declare_var(name="repnum",
                              comment="Current repetition number",
                              stack=wrapper_code)
        if eligible_to_unroll:
            self.code_declare_var(type="CONC_EVENT *", name="repevent", rhs="NULL",
                                  comment="Event designating repetition",
                                  stack=wrapper_code)
            self.code_declare_var(name="repeventnum", rhs="-1%s" % self.ncptl_int_suffix,
                                  comment="Event number corresponding to repevent",
                                  stack=wrapper_code)

        # Prepare to perform a given number of warmup repetitions.
        if warmups:
            self.code_declare_var (name="on_event", rhs="-1",
                                   comment='Event ID of the "suppression on" event',
                                   stack=wrapper_code)
            self.push("", wrapper_code)
            self.push(" /* Suppress output at the start of the warmup repetitions. */", wrapper_code)
            self.push("if (numreps > 0%s && loopnum == 0%s) {" %
                      (self.ncptl_int_suffix, self.ncptl_int_suffix),
                      wrapper_code)
            self.code_declare_var (name="thisev_on", type="CONC_EVENT *",
                                   comment="Output-suppression event",
                                   stack=wrapper_code)
            self.code_allocate_event("EV_SUPPRESS", declare="thisev_on = ",
                                     stack=wrapper_code)
            self.pushmany([
                "thisev_on->s.suppress.quiet = 1;",
                "on_event = ncptl_queue_length(eventqueue) - 1;",
                "}",
                ""],
                          stack=wrapper_code)

        # Start the repetitions.
        if not eligible_to_unroll:
            # Perform the given number of repetitions.
            self.pushmany([
                " /* Perform numreps repetitions of the loop body. */",
                "for (repnum=0; repnum<numreps; repnum++) {"],
                          stack=wrapper_code)
        else:
            # Specify the number of repetitions to perform.
            self.pushmany([
                " /* Conditionally unroll the loop. */",
                "for (repnum=0; repnum<(unroll_loop?numreps:1); repnum++) {"
                "",
                " /* Allocate a repeat event if we have more than one repetition. */",
                "if (!unroll_loop && numreps > 1%s) {" % self.ncptl_int_suffix,
                "repeventnum = ncptl_queue_length (eventqueue);"],
                          stack=wrapper_code)
            self.code_allocate_event("EV_REPEAT", declare="repevent = ",
                                     stack=wrapper_code)
            self.pushmany([
                "repevent->s.rep.numreps = numreps;",
                "}",
                "",
                " /* Output a loop body if we have at least one repetition. */",
                "if (unroll_loop || numreps > 0%s) {" % self.ncptl_int_suffix],
                          stack=wrapper_code)

        # End the repetitions
        wrapper_end_code = []
        self.push_marker(wrapper_end_code)

        # Modify the repeat event now that we know how many new events
        # we allocated.
        if eligible_to_unroll:
            self.pushmany([
                "}",
                "}",
                "",
                " /* Assign the number of events to repeat, now that we know that number. */",
                "if (!unroll_loop && numreps > 1%s) {" % self.ncptl_int_suffix,
                "repevent = repeventnum + (CONC_EVENT *) ncptl_queue_contents (eventqueue, 0);",
                "repevent->s.rep.end_event = ncptl_queue_length (eventqueue) - 1;",
                "}"],
                          stack=wrapper_end_code)
        else:
            self.push("}", wrapper_end_code)

        # If requested, synchronize at tne end of the warmup
        # repetitions.  The tricky thing here is that we need to
        # synchronize even if we're performing 0 warmup repetitions.
        if warmups and synchronize_afterwards:
            self.pushmany([
                "",
                " /* After the warmups are finished, synchronize all tasks. */",
                "if (loopnum == 0%s) {" % self.ncptl_int_suffix],
                          stack=wrapper_end_code)
            self.code_declare_var (name="thisev_sync", type="CONC_EVENT *",
                                   comment="Barrier-synchronization event",
                                   stack=wrapper_end_code)
            self.push("", wrapper_end_code)
            self.code_allocate_event("EV_SYNC", declare="thisev_sync = ",
                                     stack=wrapper_end_code)
            self.pushmany(self.invoke_hook("n_for_count_SYNC_ALL", locals(),
                                           alternatepy=lambda loc:
                                           loc["self"].errmsg.error_fatal("the %s backend does not support SYNCHRONIZATION after WARMUP REPETITIONS" %
                                                                          loc["self"].backend_name)),
                          stack=wrapper_end_code)
            self.push("}", wrapper_end_code)

        # Re-enable output at tne end of the warmup repetitions.
        if warmups:
            self.pushmany([
                "",
                " /* After the warmups are finished, resume outputting. */",
                "if (numreps > 0%s && loopnum == 0%s) {" %
                (self.ncptl_int_suffix, self.ncptl_int_suffix)],
                          stack=wrapper_end_code)
            self.code_declare_var (name="thisev_off", type="CONC_EVENT *",
                                   comment="Output un-suppression event",
                                   stack=wrapper_end_code)
            self.push("", wrapper_end_code)
            self.code_allocate_event("EV_SUPPRESS", declare="thisev_off = ",
                                     stack=wrapper_end_code)
            self.pushmany([
                "thisev_off->s.suppress.quiet = 0;",
                "thisev_off->s.suppress.matching_event = on_event;",
                "}"],
                          wrapper_end_code)

        # Close any remaining scopes.
        if warmups:
            self.push("}", wrapper_end_code)
        self.push("}", wrapper_end_code)

        # Wrap the stack top within the loop code.
        self.combine_to_marker(wrapper_code)
        self.combine_to_marker(wrapper_end_code)
        self.wrap_stack(wrapper_code[0], wrapper_end_code[0])

    def n_for_each(self, node):
        "Repeat a statement for each element in a list of sets."
        rangelist = self.pop()
        ident = self.pop()
        wrapper_main, wrapper_after = self.range_list_wrapper(rangelist)
        wrapper_before = []
        self.push_marker(wrapper_before)
        self.push(" /* FOR EACH %s IN %s... */" % (ident, rangelist), wrapper_before)
        self.pushmany(wrapper_main, stack=wrapper_before)
        self.code_declare_var("ncptl_int", name=ident,
                              rhs="thisrange->integral ? thisrange->u.i.loopvar : CONC_DBL2INT(thisrange->u.d.loopvar)",
                              stack=wrapper_before)
        self.push("{", wrapper_before)
        self.combine_to_marker(wrapper_before)
        self.wrap_stack(wrapper_before[0], wrapper_after + ["}"])

    def n_for_time(self, node):
        "Repeat a statement for a given length of time."
        multiplier = self.pop()
        expression = self.pop()
        if node.lineno0 == node.lineno1:
            lineno_msg = "line %d" % node.lineno0
        else:
            lineno_msg = "lines %d-%d" % (node.lineno0, node.lineno1)

        # Prepare the loop header.
        bwrap_code = []
        self.push_marker(bwrap_code)
        self.pushmany([
            " /* FOR %s*%s MICROSECONDS... */" % (expression, multiplier),
            "if (within_time_loop)",
            'ncptl_fatal ("FOR <time> loops cannot be nested (source-code %s)");' % lineno_msg,
            "else {"],
                      bwrap_code)
        self.code_declare_var("int", name="within_time_loop", rhs="1",
                              comment="Keep track of our being within a FOR <time> loop.",
                              stack=bwrap_code)
        self.code_declare_var("int", name="prev_pendingsends",
                              rhs="pendingsends",
                              comment="Help keep track of the number of leaked sends",
                              stack=bwrap_code)
        self.code_declare_var("int", name="prev_pendingrecvs",
                              rhs="pendingrecvs",
                              comment="Help keep track of the number of leaked receives",
                              stack=bwrap_code)
        self.code_declare_var("ncptl_int", name="begin_event",
                              rhs="ncptl_queue_length (eventqueue)",
                              comment="Store the offset of the following EV_BTIME event.",
                              stack=bwrap_code)
        self.code_allocate_event("EV_BTIME", bwrap_code)
        self.pushmany([
            "thisev->s.btime.usecs = (uint64_t)(%s) * (uint64_t)%s;" %
            (expression, multiplier),
            'within_time_loop = 1;   /* Trick various compilers into suppressing a "variable not used" warning. */',
            ""],
                      bwrap_code)
        self.combine_to_marker(bwrap_code)

        # Prepare the loop epilogue.
        ewrap_code = []
        self.push_marker(ewrap_code)
        self.pushmany([
            "",
            " /* Complete the FOR %s*%s MICROSECONDS loop. */" % (expression, multiplier)],
                      ewrap_code)
        self.code_allocate_event("EV_ETIME", declare="thisev =", stack=ewrap_code)
        self.pushmany([
            "thisev->s.etime.begin_event = begin_event;",
            "if (pendingsends - prev_pendingsends)",
            'ncptl_fatal ("The FOR loop in source-code %s leaks %%ld asynchronous send(s) per iteration", (long)(pendingsends-prev_pendingsends));' %
            lineno_msg,
            "if (pendingrecvs - prev_pendingrecvs)",
            'ncptl_fatal ("The FOR loop in source-code %s leaks %%ld asynchronous receive(s) per iteration", (long)(pendingrecvs-prev_pendingrecvs));' %
            lineno_msg,
            "}",
            ""],
                      ewrap_code)
        self.combine_to_marker(ewrap_code)

        # Wrap the initialization stack within the loop code.
        self.wrap_stack(bwrap_code[0], ewrap_code[0])


    def n_if_stmt(self, node):
        "Process an IF...THEN...OTHERWISE statement."
        if len(node.kids) == 3:
            elsestmt = self.pop(self.init_elements)
        else:
            elsestmt = None
        thenstmt = self.pop(self.init_elements)
        ifexpr = self.pop()

        # Prepare the initial IF...THEN code.
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* IF %s THEN... */" % ifexpr, istack)
        self.push("if (%s) {" % ifexpr, istack)
        self.pushmany(thenstmt, stack=istack)
        self.push("}", istack)

        # Prepare the optional OTHERWISE code and finish up.
        if elsestmt:
            self.push(" /* OTHERWISE (i.e., %s is false)... */" % ifexpr, istack)
            self.push("else {", istack)
            self.pushmany(elsestmt, stack=istack)
            self.push("}", istack)
        self.combine_to_marker(istack)


    #-------------------#
    # Simple statements #
    #-------------------#

    def n_empty_stmt(self, node):
        "Do nothing."
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* Empty statement */", istack)
        self.combine_to_marker(istack)

    def n_send_stmt(self, node):
        "Send a set of point-to-point messages."
        # Gather all information about the communication.
        recv_attributes = self.pop()
        recv_message_spec = self.pop()
        target_tasks = self.pop()
        attributes = self.pop()
        message_spec = self.pop()
        source_task = self.pop()
        num_messages, uniqueness, message_size, alignment, misaligned, touching, buffer_num = message_spec

        # Blocking all-to-all communication currently deadlocks.
        if "asynchronously" not in attributes and \
           "unsuspecting" not in attributes and \
           source_task[0] == "task_all" and \
           target_tasks[0] == "all_others":
            self.errmsg.error_fatal("ALL TASKS cannot send a blocking message to ALL OTHER TASKS without deadlocking")

        # Receive the corresponding message unless explicitly
        # instructed not to.
        istack = self.init_elements
        self.push_marker(istack)
        if "unsuspecting" not in attributes:
            self.push(target_tasks)
            self.push(recv_message_spec)
            self.push(source_task)
            self.push(recv_attributes)
            self.n_receive_stmt(node)
            self.pushmany(self.pop(istack), istack)

        # Determine the set of tasks we're sending to.
        if target_tasks[0] == "all_others":
            self.push(" /* SEND...TO ALL OTHERS */", istack)
        else:
            self.push(" /* SEND...TO %s */" % str(target_tasks[1]), istack)
        self.code_begin_source_scope(source_task, istack)
        if target_tasks[0] == "all_others":
            targetvar = self.code_declare_var(suffix="loop", stack=istack)
            self.pushmany([
                "for (%s=0; %s<var_num_tasks; %s++)" % (targetvar, targetvar, targetvar),
                "if (%s != virtrank) {" % targetvar],
                          istack)
        elif target_tasks[0] == "task_expr":
            targetvar = target_tasks[1]
            self.code_declare_var(name="virtdest", rhs=targetvar, stack=istack)
            self.push("if (virtdest>=0 && virtdest<var_num_tasks) {",
                      stack=istack)
        elif target_tasks[0] == "task_restricted":
            targetvar = self.code_declare_var(name=target_tasks[1], stack=istack)
            self.pushmany([
                "for (%s=0; %s<var_num_tasks; %s++)" % (targetvar, targetvar, targetvar),
                "if (%s) {" % target_tasks[2]],
                          istack)
        else:
            self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        self.push(" /* In this scope, %s represents a single receiver. */" % targetvar,
                  istack)

        # Send the correct number of messages.
        if num_messages != "1":
            self.push(" /* Prepare to send %s messages. */" % num_messages,
                      istack)
            self.code_declare_var(name="numreps", rhs=num_messages,
                                  comment="Number of messages",
                                  stack=istack)
            if "asynchronously" in attributes or uniqueness == "unique":
                # If we need to do something different each iteration
                # then we can't simply use a REPEAT event.
                loopvar = self.code_declare_var(suffix="loop", stack=istack)
                self.push("for (%s=0; %s<numreps; %s++) {" %
                          (loopvar, loopvar, loopvar),
                          istack)
            else:
                # If every iteration is the same, use a REPEAT event.
                self.push("if (numreps > 1%s) {" % self.ncptl_int_suffix, istack)
                self.code_declare_var(type="CONC_EVENT *", name="repeatev",
                                      comment="Event specifying the number of repetitions to perform",
                                      stack=istack)
                self.code_allocate_event("EV_REPEAT", declare="repeatev =", stack=istack)
                self.pushmany([
                    "repeatev->s.rep.end_event = ncptl_queue_length(eventqueue);",
                    "repeatev->s.rep.numreps = numreps;",
                    "}",
                    "",
                    " /* Ensure we have at least one message to send. */",
                    "if (numreps > 0%s) {" % self.ncptl_int_suffix],
                              stack=istack)

        # Fill in the send-event data structure.
        if "asynchronously" in attributes:
            self.code_allocate_event("EV_ASEND", stack=istack)
            self.push("pendingsends++;", istack)
        else:
            if node.lineno0 == node.lineno1:
                lineno_msg = "line %d" % node.lineno0
            else:
                lineno_msg = "lines %d-%d" % (node.lineno0, node.lineno1)
            self.code_allocate_event("EV_SEND", stack=istack)
            self.pushmany([
                "if (virtrank == (%s))" % targetvar,
                'ncptl_fatal ("Send-to-self deadlock encountered on task %%d in %s of the source code", virtrank);' % lineno_msg],
                          istack)
        self.push("", istack)
        struct = "thisev->s.send"
        self.push(" /* Fill in all of the fields of a send-event structure. */",
                  istack)
        self.code_fill_in_comm_struct(struct, message_spec, attributes,
                                      targetvar, "dest", istack)
        self.pushmany(self.invoke_hook("n_send_stmt_BODY", locals()), istack)

        # Close the scope(s) begun earlier in this method.
        if num_messages != "1":
            self.push("}", istack)
        self.push("}", istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)


    def n_receive_stmt(self, node):
        "Receive a set of point-to-point messages."
        # Gather all information about the communication.
        attributes = self.pop()
        source_task = self.pop()
        message_spec = self.pop()
        target_tasks = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* RECEIVE...FROM ALL TASKS */", istack)
        else:
            self.push(" /* RECEIVE...FROM %s */" % str(source_task[1]), istack)
        num_messages, uniqueness, message_size, alignment, misaligned, touching, buffer_num = message_spec

        # Determine the set of tasks we're receiving from.
        sourcevar = self.code_begin_target_loop(source_task, target_tasks, istack)
        self.push(" /* In this scope, we must be a message recipient. */", istack)
        if "asynchronously" not in attributes:
            if node.lineno0 == node.lineno1:
                lineno_msg = "line %d" % node.lineno0
            else:
                lineno_msg = "lines %d-%d" % (node.lineno0, node.lineno1)

        # Receive the correct number of messages.
        # CAVEAT: num_messages is evaluated in target scope, not source scope.
        if num_messages != "1":
            self.push(" /* Prepare to receive %s messages. */" % num_messages,
                      istack)
            self.code_declare_var(name="numreps", rhs=num_messages,
                                  comment="Number of messages",
                                  stack=istack)
            if "asynchronously" in attributes or uniqueness == "unique":
                # If we need to do something different each iteration
                # then we can't simply use a REPEAT event.
                loopvar = self.code_declare_var(suffix="loop", stack=istack)
                self.push("for (%s=0; %s<numreps; %s++) {" %
                          (loopvar, loopvar, loopvar),
                          istack)
            else:
                # If every iteration is the same, use a REPEAT event.
                self.push("if (numreps > 1%s) {" % self.ncptl_int_suffix, istack)
                self.code_declare_var(type="CONC_EVENT *", name="repeatev",
                                      comment="Event specifying the number of repetitions to perform",
                                      stack=istack)
                self.code_allocate_event("EV_REPEAT", declare="repeatev =", stack=istack)
                self.pushmany([
                    "repeatev->s.rep.end_event = ncptl_queue_length(eventqueue);",
                    "repeatev->s.rep.numreps = numreps;",
                    "}",
                    "",
                    " /* Ensure we have at least one message to receive. */",
                    "if (numreps > 0%s) {" % self.ncptl_int_suffix],
                              stack=istack)

        # Fill in the receive-event data structure.
        if "asynchronously" in attributes:
            self.code_allocate_event("EV_ARECV", istack)
            self.push("pendingrecvs++;", istack)
            self.push("", istack)
        else:
            self.code_allocate_event("EV_RECV", istack)
        struct = "thisev->s.recv"
        self.push(" /* Fill in all of the fields of a receive-event structure. */",
                  istack)
        self.code_fill_in_comm_struct(struct, message_spec, attributes,
                                      sourcevar, "source", istack)
        if "asynchronously" in attributes:
            self.push("pendingrecvbytes += %s;" % message_size, istack)
            if touching != "no_touching":
                self.push("*(ncptl_int *)(ncptl_queue_allocate(touchedqueue)) = ncptl_queue_length(eventqueue) - 1;",
                          istack)
        self.pushmany(self.invoke_hook("n_recv_stmt_BODY", locals()), istack)

        # Close the scope(s) begun earlier in this method.
        if num_messages != "1":
            self.push("}", istack)
        self.code_end_target_loop(source_task, target_tasks, istack)
        self.combine_to_marker(istack)


    def n_awaits_completion(self, node):
        "Block until all pending asynchronous operations complete."
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS AWAIT COMPLETION */", istack)
        else:
            self.push(" /* TASKS %s AWAIT COMPLETION */" % source_task[1],
                      istack)
        self.code_begin_source_scope(source_task, istack)
        self.push(" /* Fill in all of the fields of a wait-event structure. */",
                  istack)
        self.code_allocate_event("EV_WAIT", istack)
        self.pushmany([
            "thisev->s.wait.numsends = pendingsends;",
            "thisev->s.wait.numrecvs = pendingrecvs;",
            "thisev->s.wait.numrecvbytes = pendingrecvbytes;",
            "thisev->s.wait.touchedlist = (ncptl_int *) ncptl_queue_contents (touchedqueue, 1);",
            "thisev->s.wait.numtouches = ncptl_queue_length (touchedqueue);",
            "ncptl_queue_empty (touchedqueue);",
            "pendingsends = 0;",
            "pendingrecvs = 0;",
            "pendingrecvbytes = 0;"],
                      istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def n_output_stmt(self, node):
        "Output a message to the standard output device."
        outputlist = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        outputvalues = map(lambda p: p[1], outputlist)
        output_text = self.clean_comments(repr(outputvalues))
        if source_task[0] == "task_all":
            if source_task[1]:
                header_comment = (" /* ALL TASKS %s OUTPUT %s */" %
                                  (source_task[1], output_text))
            else:
                header_comment = " /* ALL TASKS OUTPUT %s */" % output_text
        elif source_task[0] == "task_expr":
            header_comment = (" /* TASK %s OUTPUTS %s */" %
                              (source_task[1], output_text))
        elif source_task[0] == "task_restricted":
            header_comment = (" /* TASKS %s SUCH THAT %s OUTPUT %s */" %
                              (source_task[1], source_task[2], output_text))
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        self.push(header_comment, istack)
        self.code_allocate_code_event(source_task,
                                      string.join(outputvalues),
                                      istack)
        self.combine_to_marker(istack)

        # Build up one large printf() command to store as arbitrary code.
        astack = self.arbitrary_code
        self.push_marker(astack)
        formatlist = []
        valuelist = []
        for itemtype, itemvalue in outputlist:
            if itemtype == "expr":
                formatlist.append("%.10lg")
                valuelist.append(self.code_make_expression_fp(itemvalue))
            elif itemtype == "string":
                formatlist.append("%s")
                valuelist.append(itemvalue)
            else:
                self.errmsg.error_internal('unknown output item "%s"' %
                                           (self.thisfile, itemtype))
        self.push(header_comment, astack)
        self.push("if (!suppress_output) {", astack)
        self.code_clock_control("DECLARE", astack)
        self.code_clock_control("STOP", astack)
        self.push('printf ("%s\\n", %s);' % (string.join(formatlist, ""),
                                             string.join(valuelist, ", ")),
                  astack)
        self.code_clock_control("RESTART", astack)
        self.push("}", astack)
        self.combine_to_marker(astack)

    def n_backend_stmt(self, node):
        "Execute arbitrary, backend-specific code."
        execlist = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        execvalues = map(lambda p: p[1], execlist)
        backend_text = self.clean_comments(repr(execvalues))
        if source_task[0] == "task_all":
            if source_task[1]:
                header_comment = (" /* ALL TASKS %s BACKEND EXECUTE %s */" %
                                  (source_task[1], backend_text))
            else:
                header_comment = " /* ALL TASKS BACKEND EXECUTE %s */" % backend_text
        elif source_task[0] == "task_expr":
            header_comment = (" /* TASK %s BACKEND EXECUTES %s */" %
                              (source_task[1], backend_text))
        elif source_task[0] == "task_restricted":
            header_comment = (" /* TASKS %s SUCH THAT %s BACKEND EXECUTES %s */" %
                              (source_task[1], source_task[2], backend_text))
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        self.push(header_comment, istack)
        self.code_allocate_code_event(source_task, string.join(execvalues), istack)
        self.combine_to_marker(istack)

        # Build up one large command to store as arbitrary code.
        astack = self.arbitrary_code
        self.push_marker(astack)
        commandlist = []
        for itemtype, itemvalue in execlist:
            if itemtype == "expr":
                commandlist.append(self.code_make_expression_fp(itemvalue))
            elif itemtype == "string":
                commandlist.append(self.unquote_string(itemvalue))
            else:
                self.errmsg.error_internal('unknown output item "%s"' %
                                           (self.thisfile, itemtype))
        self.push(header_comment, astack)
        self.push("{", astack)
        backend_code = string.join(commandlist)
        backend_re = re.compile(r'\[message\s+buffer\s+([^\]]+)\]', re.IGNORECASE)
        backend_code = backend_re.sub(r'(ncptl_get_message_buffer ((ncptl_int)(\1)))', backend_code)
        self.push(backend_code, astack)
        self.push("}", astack)
        self.combine_to_marker(astack)

    def n_assert_stmt(self, node):
        "Abort (at initialization time) if a given condition isn't met."
        expression = self.pop()
        description = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        self.pushmany([
            " /* ASSERT THAT %s. */" % self.clean_comments(description[1:-1]),
            "if (!(%s))" % expression,
            'ncptl_fatal ("Assertion failure: %s");' % description[1:-1]],
                      istack)
        self.combine_to_marker(istack)

    def n_computes_for(self, node):
        '"Compute" for a given length of time.'
        multiplier = self.pop()
        count = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* COMPUTE FOR (%s)*(%s) MICROSECONDS */" %
                   (count, multiplier),
                  istack)
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_DELAY", istack)
        self.pushmany([
            "thisev->s.delay.microseconds = (uint64_t) %s;" % count,
            "thisev->s.delay.microseconds *= (uint64_t) %s;" % multiplier,
            "thisev->s.delay.spin0sleep1 = 0;"],
                      istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def n_sleeps_for(self, node):
        'Relinquish the CPU for a given length of time.'
        multiplier = self.pop()
        count = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        self.push(" /* SLEEP FOR (%s)*(%s) MICROSECONDS */" %
                   (count, multiplier),
                  istack)
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_DELAY", istack)
        self.pushmany([
            "thisev->s.delay.microseconds = (uint64_t) %s;" % count,
            "thisev->s.delay.microseconds *= (uint64_t) %s;" % multiplier,
            "thisev->s.delay.spin0sleep1 = 1;"],
                      istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def n_touch_stmt(self, node):
        'Walk a region of memory, reading various pieces at each step.'

        # Canonicalize our arguments.
        struct = "thisev->s.touch"
        if len(node.kids) == 4:
            # We're touching a region of the default size.
            stride = self.pop()
            repeat_count = self.pop()
            region_bytes = self.pop()
            source_task = self.pop()
            word_size = "4%s" % self.ncptl_int_suffix
            num_accesses = None
        else:
            # We're touching a region with a specified count and a
            # specified datatype.
            stride = self.pop()
            repeat_count = self.pop()
            region_bytes = self.pop()
            word_size = self.pop()
            num_accesses = self.pop()
            source_task = self.pop()
        if stride[0] == "default":
            stride_bytes = word_size
        elif stride[0] == "random":
            stride_bytes = "NCPTL_INT_MIN"
            self.program_uses_randomness = max(self.program_uses_randomness, 1)
        else:
            stride_bytes = "(%s)*%s" % (stride[1], stride[2])
        if not num_accesses:
            if stride[0] == "random":
                num_accesses = "%s.regionbytes/%s.wordsize" % (struct, struct)
            else:
                num_accesses = "%s.regionbytes/%s.bytestride" % (struct, struct)
        num_accesses = "%s*(%s)" % (repeat_count, num_accesses)

        # Allocate an event and fill it in.
        istack = self.init_elements
        self.push_marker(istack)
        if stride_bytes == "NCPTL_INT_MIN":
            stride_desc = "RANDOM STRIDE"
            random_stride = 1
        else:
            stride_desc = "STRIDE %s BYTES" % stride_bytes
            random_stride = 0
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS TOUCH %s BYTES WITH %s */" %
                      (region_bytes, stride_desc),
                      istack)
        else:
            self.push(" /* TASKS %s TOUCH %s BYTES WITH %s */" %
                      (source_task[1], region_bytes, stride_desc),
                      istack)
        self.code_begin_source_scope(source_task, istack)
        if not random_stride:
            self.code_declare_var(type="static ncptl_int", name="nextbyte",
                                  rhs="0", comment="Next byte in the region to acecss",
                                  stack=istack)
        self.code_allocate_event("EV_TOUCH", istack)
        self.pushmany([
            "%s.regionbytes = %s;" % (struct, region_bytes),
            "%s.wordsize = %s;" % (struct, word_size),
            "%s.bytestride = %s;" % (struct, stride_bytes),
            "%s.numaccesses = %s;" % (struct, num_accesses),
            "if (touch_region_size < %s.regionbytes) {" % struct,
            "touch_region_size = %s.regionbytes;" % struct,
            "touch_region = ncptl_realloc (touch_region, touch_region_size, ncptl_pagesize);",
            "}"],
                      istack)
        if random_stride:
            self.push("%s.firstbyte = 0%s;" % (struct, self.ncptl_int_suffix),
                      istack)
        else:
            self.pushmany([
                "if (%s.bytestride < 0)" % struct,
                "%s.numaccesses = -%s.numaccesses;" % (struct, struct),
                "%s.firstbyte = nextbyte;" % struct,
                "nextbyte = (nextbyte+%s.numaccesses*%s.bytestride) %% %s.regionbytes;" %
                (struct, struct, struct)],
                          stack=istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def n_touch_buffer_stmt(self, node):
        "Walk a communication buffer, reading various pieces at each step."
        if node.attr == "expr":
            buffer_num = self.pop()
        else:
            buffer_num = "default"
        source_task = self.pop()

        # Write some section comments.
        istack = self.init_elements
        self.push_marker(istack)
        if buffer_num == "default":
            if node.attr == "all":
                buffer_name = "ALL MESSAGE BUFFERS"
            elif node.attr == "current":
                buffer_name = "THE CURRENT MESSAGE BUFFER"
            else:
                self.errmsg.error_internal('Unknown buffer number "%s"' % node.attr)
        else:
            buffer_name = "BUFFER %s" % buffer_num
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS TOUCH %s */" % buffer_name, istack)
        else:
            self.push(" /* TASKS %s TOUCH %s */" %
                      (source_task[1], buffer_name),
                      istack)

        # Allocate an event and fill it in.
        self.code_begin_source_scope(source_task, istack)
        if buffer_num != "default":
            self.push("if (%s >= 0) {" % buffer_num, istack)
        self.code_allocate_event("EV_TOUCH", istack)
        struct = "thisev->s.touch"
        if buffer_num == "default":
            if node.attr == "all":
                buffer_rhs = "-1%s;   /* Indicate all buffers. */" % self.ncptl_int_suffix
            elif node.attr == "current":
                buffer_rhs = "pendingsends+pendingrecvs;   /* Really the buffer number */"
            else:
                self.errmsg.error_internal('Unknown buffer number "%s"' % node.attr)
        else:
            buffer_rhs = "%s;   /* Really the buffer number */" % buffer_num
        self.pushmany([
            "%s.bytestride = 4%s;" % (struct, self.ncptl_int_suffix),
            "%s.wordsize = 4%s;" % (struct, self.ncptl_int_suffix),
            "%s.firstbyte = -1%s;   /* Indicate that placeholders exist. */" % (struct, self.ncptl_int_suffix),
            "%s.regionbytes = %s" % (struct, buffer_rhs)],
                      istack)
        if buffer_num != "default":
            self.push("}", istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    def n_sync_stmt(self, node):
        "Barrier-synchronize a set of tasks."
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS SYNCHRONIZE */", istack)
        else:
            self.push(" /* TASKS %s SYNCHRONIZE */" % source_task[1], istack)

        # Produce a synchronization event.
        extra_decl_code = self.invoke_hook("n_sync_stmt_DECL", locals(), before=["{"])
        self.pushmany(extra_decl_code, stack=istack)
        self.pushmany(self.invoke_hook("n_sync_stmt_PRE", locals()),
                      stack=istack)
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_SYNC", istack)
        self.pushmany(self.invoke_hook("n_sync_stmt_INIT", locals()),
                      stack=istack)
        self.code_end_source_scope(source_task, istack)
        self.pushmany(self.invoke_hook("n_sync_stmt_POST", locals()),
                      stack=istack)
        if extra_decl_code != []:
            self.push("}", istack)
        self.combine_to_marker(istack)

    def n_reset_stmt(self, node):
        "Reset all of the var_total_* variables."
        self.code_counter_stmt("RESET", node)

    def n_store_stmt(self, node):
        "Push all of the var_total_* variables' current values."
        self.code_counter_stmt("STORE", node)

    def n_restore_stmt(self, node):
        "Pope all of the var_total_* variables' values."
        self.code_counter_stmt("RESTORE", node)

    def n_log_stmt(self, node):
        "Log an expression to a particular row+column of a log file."
        self.program_uses_log_file = 1
        entrylist = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)

        # Write a comment string.
        comment = ""
        if source_task[0] == "task_all":
            comment = comment + ' /* ALL TASKS LOG '
        elif source_task[0] == "task_expr":
            comment = comment + ' /* TASK %s LOGS ' % source_task[1]
        elif source_task[0] == "task_restricted":
            comment = comment + ' /* TASKS %s SUCH THAT %s LOG ' % source_task[1:]
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        for logentry in range(len(entrylist)):
            description = self.clean_comments(entrylist[logentry][0])
            if logentry == 0:
                comment = comment + "%s " % description
            else:
                comment = comment + "AND %s " % description
        comment = comment + "*/"
        self.push(comment, istack)
        self.code_allocate_code_event(source_task,
                                      string.join(map(lambda e: e[1], entrylist)),
                                      istack)
        self.combine_to_marker(istack)

        # Generate the corresponding code.
        astack = self.arbitrary_code
        self.push_marker(astack)
        self.pushmany([
            comment,
            "if (!suppress_output) {"],
                      astack)

        self.code_clock_control("DECLARE", astack)
        self.code_clock_control("STOP", astack)
        for description, expression, aggregate in entrylist:
            clean_desc = string.replace(description, "\\n", " ")
            if aggregate:
                aggregate_enum = "NCPTL_FUNC_" + string.upper(aggregate)
            else:
                aggregate_enum = "NCPTL_FUNC_NO_AGGREGATE"
            self.push('ncptl_log_write (logstate, %s, %s, %s, %s);' %
                       (self.logcolumn, clean_desc, aggregate_enum,
                        self.code_make_expression_fp(expression)),
                      astack)
            self.logcolumn = self.logcolumn + 1
        self.code_clock_control("RESTART", astack)
        self.push("}", astack)
        self.combine_to_marker(astack)

    def n_log_flush_stmt(self, node):
        """Compute the previously specified aggregate functions and
        write the results to the log file."""
        self.program_uses_log_file = 1
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS COMPUTE AGGREGATES */", istack)
        elif source_task[0] == "task_expr":
            self.push(" /* TASK %s COMPUTES AGGREGATES */" % source_task[1],
                      istack)
        elif source_task[0] == "task_restricted":
            self.push(" /* TASKS %s SUCH THAT %s COMPUTE AGGREGATES */" % source_task[1:],
                      istack)
        else:
            self.errmsg.error_internal("Unknown source task type %s" % repr(source_task[0]))
        self.code_begin_source_scope(source_task, istack)
        self.code_allocate_event("EV_FLUSH", declare="(void)", stack=istack)
        self.code_end_source_scope(source_task, istack)
        self.combine_to_marker(istack)

    # For the following, all backends will need to define
    # n_reduce_stmt_DECL and n_reduce_stmt_INIT to initialize
    # thisev->s.reduce.
    def n_reduce_stmt(self, node):
        "Reduce a set of values and multicast the result."
        # Gather all information about the communication.
        allreduce = "allreduce" in node.attr
        if not allreduce:
            target_tasks = self.pop()
        target_message_spec = self.pop()
        source_message_spec = self.pop()
        source_tasks = self.pop()
        if allreduce:
            target_tasks = source_tasks
        istack = self.init_elements
        self.push_marker(istack)
        if source_tasks[0] == "task_all":
            source_task_str = "ALL TASKS"
        else:
            source_task_str = str(source_tasks[1])
        if allreduce:
            self.push(" /* REDUCE from %s...back to %s */" % (source_task_str, source_task_str), istack)
        else:
            if target_tasks[0] == "task_all":
                target_task_str = "ALL TASKS"
            else:
                target_task_str = "TASKS " + str(target_tasks[1])
            self.push(" /* REDUCE from %s TO %s */" %
                      (source_task_str, target_task_str),
                      istack)
        if not allreduce and source_tasks == target_tasks:
            # If we know at compile time that the senders must match
            # the receivers then we can consider this an allreduce
            # operation.
            allreduce = 1

        # Determine if we're a sender.
        self.push("{", istack)
        num_open_scopes = 1
        self.code_declare_var(name="reduce_senders", type="char *",
                              comment="1=rank represents a sender; 0=it doesn't",
                              stack=istack)
        self.code_declare_var(name="reduce_receivers", type="char *",
                              comment="1=rank represents a receiver; 0=it doesn't",
                              stack=istack)
        self.code_declare_var(name="numsenders", rhs="0"+self.ncptl_int_suffix,
                              comment="Number of tasks who will compute the reduced values",
                              stack=istack)
        self.code_declare_var(name="numreceivers", rhs="0"+self.ncptl_int_suffix,
                              comment="Number of tasks who will receive the reduced values",
                              stack=istack)
        self.code_declare_var(name="i", stack=istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_DECL", locals()), stack=istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_PRE", locals(),
                                       after=[""], before=[
            "",
            " /* Perform initializations specific to the %s backend. */" %
            self.backend_name]),
                      stack=istack)
        self.pushmany([
            " /* Determine the set of senders. */",
            "reduce_senders = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);"],
                      stack=istack)
        source_task_var = None
        if source_tasks[0] == "task_all":
            source_task_var = source_tasks[1]
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_senders[i] = 1;",
                "numsenders = var_num_tasks;"],
                          stack=istack)
        else:
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_senders[i] = 0;"],
                          stack=istack)
            if source_tasks[0] == "task_expr":
                self.pushmany([
                    "if ((%s)>=0 && (%s)<var_num_tasks) {" %
                    (source_tasks[1], source_tasks[1]),
                    "reduce_senders[%s] = 1;" % source_tasks[1],
                    "numsenders = 1%s;" % self.ncptl_int_suffix,
                    "}"],
                              stack=istack)
            elif source_tasks[0] == "task_restricted":
                source_task_var = source_tasks[1]
                self.pushmany([
                    "for (i=0; i<var_num_tasks; i++) {",
                    "ncptl_int %s = i;" % source_tasks[1],
                    "if (%s) {" % source_tasks[2],
                    "reduce_senders[i] = 1;",
                    "numsenders++;",
                    "}",
                    "}"],
                              stack=istack)
            else:
                self.errmsg.error_internal('unknown source task type "%s"' % source_tasks[0])

        # Determine if we're a receiver.
        must_close_receiver_scope = 0
        self.pushmany([
            "",
            " /* Determine the set of receivers. */",
            "reduce_receivers = (char *) ncptl_malloc (var_num_tasks*sizeof(char), 0);"],
                      stack=istack)
        if target_tasks[0] == "task_all":
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_receivers[i] = 1;",
                "numreceivers = var_num_tasks;"],
                          stack=istack)
        else:
            self.pushmany([
                "for (i=0; i<var_num_tasks; i++)",
                "reduce_receivers[i] = 0;"],
                          stack=istack)
            if (source_task_var != None
                and re.search(r'\b%s\b' % source_task_var, target_tasks[1])
                and (target_tasks[0] == "task_expr" or target_tasks[1] != source_task_var)):
                self.push("{", istack)
                must_close_receiver_scope = 1
                self.code_declare_var(name=source_task_var,
                                      comment="Source task number",
                                      stack=istack)
                self.pushmany([
                    "for (%s=0; %s<var_num_tasks; %s++)" %
                    (source_task_var, source_task_var, source_task_var),
                    "if (reduce_senders[%s])" % source_task_var],
                              stack=istack)
            if target_tasks[0] == "task_expr":
                self.pushmany([
                    "if ((%s)>=0 && (%s)<var_num_tasks) {" %
                    (target_tasks[1], target_tasks[1]),
                    "reduce_receivers[%s] = 1;" % target_tasks[1],
                    "numreceivers = 1%s;" % self.ncptl_int_suffix,
                    "}"],
                              stack=istack)
            elif target_tasks[0] == "task_restricted":
                self.pushmany([
                    "for (i=0; i<var_num_tasks; i++) {",
                    "ncptl_int %s = i;" % target_tasks[1],
                    "if (%s) {" % target_tasks[2],
                    "reduce_receivers[i] = 1;",
                    "numreceivers++;",
                    "}",
                    "}"],
                              stack=istack)
            else:
                self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        if must_close_receiver_scope:
            self.push("}", istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_HAVE_PEERS", locals(),
                                       before=[""]),
                      stack=istack)

        # Enqueue a REDUCE event for every task that is either a
        # sender or a receiver.
        self.pushmany([
            "",
            " /* Enqueue a REDUCE event for each task involved in the reduction. */",
            "if (numsenders && numreceivers && (reduce_senders[virtrank] || reduce_receivers[virtrank])) {"],
                      stack=istack)
        self.code_allocate_event("EV_REDUCE", istack)
        self.code_declare_var(name="message_size",
                              comment="Message size as the product of the number of items and the item size",
                              stack=istack)
        struct = "thisev->s.reduce"
        item_count, uniqueness, data_type, alignment, misaligned, touching, buffer_num = source_message_spec
        self.pushmany(self.invoke_hook("n_reduce_stmt_INIT", locals(),
                                       before=[""]),
                      stack=istack)
        self.pushmany([
            "%s.numitems = %s;" % (struct, item_count),
            "%s.itemsize = %s;" % (struct, data_type),
            "%s.sending = reduce_senders[virtrank];" % struct,
            "%s.receiving = reduce_receivers[virtrank];" % struct,
            "message_size = %s.numitems * %s.itemsize;" % (struct, struct)],
                      stack=istack)
        faked_message_spec = (1, uniqueness, None, alignment, misaligned, touching, buffer_num)
        self.code_fill_in_comm_struct(struct, faked_message_spec, [], None, None, stack=istack, verification=0)

        # Handle the buffer field differently based on whether the
        # message buffer is supposed to be unique.
        if uniqueness == "unique":
            if misaligned == 1:
                self.push("%s.buffer = ncptl_malloc_misaligned (message_size, %s);" %
                          (struct, alignment),
                          istack)
            else:
                self.push("%s.buffer = ncptl_malloc (message_size, %s);" %
                          (struct, alignment),
                          istack)
        else:
            self.pushmany([
                "(void) ncptl_malloc_message (message_size, %s.alignment, %s.buffernum, %s.misaligned);" %
                (struct, struct, struct),
                "%s.buffer = NULL;" % struct],
                          istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_INIT2", locals(),
                                       before=[""]),
                      stack=istack)
        self.push("}", istack)
        self.pushmany(self.invoke_hook("n_reduce_stmt_POST", locals(),
                                       before=[""]),
                      stack=istack)

        # Free allocated memory.
        self.push("ncptl_free (reduce_receivers);", istack)
        self.push("ncptl_free (reduce_senders);", istack)

        # Close all of our open scopes.
        for i in range(0, num_open_scopes):
            self.push("}", istack)
        self.combine_to_marker(istack)

    # For the following, all backends will need to define
    # n_mcast_stmt_DECL and n_mcast_stmt_INIT to initialize
    # thisev->s.mcast.
    def n_mcast_stmt(self, node):
        "Send a set of one-to-many messages."
        # Gather all information about the communication.
        attributes = self.pop()
        target_tasks = self.pop()
        message_spec = self.pop()
        source_task = self.pop()
        if "asynchronously" in attributes:
            self.errmsg.error_fatal('asynchronous multicasts are not yet implemented by the %s backend' % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)
        num_messages, uniqueness, message_size, alignment, misaligned, touching, buffer_num = message_spec
        if source_task[0] != "task_expr":
            self.errmsg.error_fatal("many-to-one and many-to-many multicast messages are not yet implemented by the %s backend" % self.backend_name,
                                    lineno0=node.lineno0, lineno1=node.lineno1)
        istack = self.init_elements
        self.push_marker(istack)
        if target_tasks[0] == "all_others":
            self.push(" /* MULTICAST...TO ALL OTHERS */", istack)
        else:
            self.push(" /* MULTICAST...TO %s */" % str(target_tasks[1]), istack)

        # Assign target_or_source the union of the source and target tasks.
        if target_tasks[0] == "task_expr":
            rankvar = self.newvar(suffix="rank")
            target_or_source = ("task_restricted",
                                rankvar,
                                "((%s==%s) || (%s==%s))" %
                                (rankvar, source_task[1], rankvar, target_tasks[1]))
        elif target_tasks[0] == "task_restricted":
            target_or_source = (target_tasks[0], target_tasks[1],
                                "((%s==%s) || (%s))" %
                                (target_tasks[1], source_task[1], target_tasks[2]))
        elif target_tasks[0] == "all_others":
            target_or_source = ("task_all", None)
        else:
            self.errmsg.error_internal('unknown target task type "%s"' % target_tasks[0])
        extra_decl_code = self.invoke_hook("n_mcast_stmt_DECL", locals(),
                                           before=["{"])
        self.pushmany(extra_decl_code, stack=istack)
        self.pushmany(self.invoke_hook("n_mcast_stmt_PRE", locals(),
                                       before=[""]),
                      stack=istack)

        # Perform the correct number of multicasts.
        one = "1" + self.ncptl_int_suffix
        if num_messages == "1":
            num_messages = one
        if num_messages != one:
            self.pushmany([
                " /* Prepare to multicast %s messages. */" % num_messages,
                "{"],
                          istack)
            loopvar = self.code_declare_var(suffix="loop", stack=istack)
            self.push("for (%s=0; %s<%s; %s++)" %
                      (loopvar, loopvar, num_messages, loopvar),
                      istack)

        # Produce a multicast event on the source *and* target tasks.
        self.code_begin_source_scope(target_or_source, istack)
        self.code_allocate_event("EV_MCAST", istack)
        struct = "thisev->s.mcast"
        self.code_fill_in_comm_struct(struct, message_spec, attributes,
                                      source_task[1], "source", istack)
        self.pushmany(self.invoke_hook("n_mcast_stmt_INIT", locals(),
                                       before=[""]),
                      stack=istack)
        self.code_end_source_scope(target_or_source, istack)

        # Close any scopes we opened.
        if num_messages != one:
            self.push("}", istack)
        self.pushmany(self.invoke_hook("n_mcast_stmt_POST", locals(),
                                       before=[""]),
                      stack=istack)
        if extra_decl_code != []:
            self.push("}", istack)
        self.combine_to_marker(istack)

    def n_processor_stmt(self, node):
        "Modify the mapping between task IDs and processors."
        if len(node.kids) == 1:
            physrank = "[random]"
        else:
            physrank = self.pop()
        source_task = self.pop()
        istack = self.init_elements
        self.push_marker(istack)
        if source_task[0] == "task_all":
            self.push(" /* ALL TASKS ARE ASSIGNED PROCESSOR %s */" % physrank, istack)
        else:
            self.push(" /* TASKS %s ARE ASSIGNED PROCESSOR %s */" %
                      (source_task[1], physrank),
                      istack)
        if physrank == "[random]":
            physrank = "ncptl_random_task(0, var_num_tasks-1, -1)"
            self.program_uses_randomness = max(self.program_uses_randomness, 2)
        self.pushmany([
            "{",
            ' /* In the following, "task ID" implies a virtual rank in the',
            '  * computation while "processor" implies a physical rank. */'],
                      istack)

        # The re-ranking is performed by *all* tasks, not just the
        # source task.  Hence, we can't call code_begin_source_scope.
        # Instead, we declare a variable for our virtual rank and loop
        # over all specified values.
        if source_task[0] == "task_expr":
            virtrankvar = "virtID"
            virtrankvalue = source_task[1]
        else:
            if source_task[1]:
                virtrankvar = source_task[1]
            else:
                virtrankvar = "virtID"
            virtrankvalue = None
        self.code_declare_var(name=virtrankvar, rhs=virtrankvalue,
                              comment="Task ID",
                              stack=istack)
        if source_task[0] in ["task_all", "task_restricted"]:
            if source_task[0] == "task_all":
                self.push("for (%s=0; %s<var_num_tasks; %s++) {" %
                          (virtrankvar, virtrankvar, virtrankvar),
                          istack)
            else:
                self.pushmany([
                    "for (%s=0; %s<var_num_tasks; %s++)" %
                    (virtrankvar, virtrankvar, virtrankvar),
                    "if (%s) {" % source_task[2]],
                              istack)
        elif source_task[0] == "task_expr":
            pass
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])
        self.push("virtrank = ncptl_assign_processor (%s, %s, procmap, physrank);" %
                  (virtrankvar, physrank),
                  istack)
        self.push("}", istack)
        if source_task[0] != "task_expr":
            self.push("}", istack)
        self.combine_to_marker(istack)


    #-----------------------------------#
    # AST interpretation: trivial nodes #
    #-----------------------------------#

    def n_trivial_node(self, node):
        "Do nothing."
        pass
