#! /usr/bin/env python

########################################################################
#
# The top-level compiler for the coNCePTuaL language
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
import os
import getopt
import re
import string
import random
from ncptl_lexer import NCPTL_Lexer
from ncptl_parser import NCPTL_Parser
from ncptl_semantic import NCPTL_Semantic
from ncptl_config import ncptl_config, expanded_ncptl_config
from ncptl_error import NCPTL_Error
from ncptl_backends import backend_list


def show_backends(odev):
    "List all available backends."
    odev.write('''The following backends are available ("*" = standard backend; "-" = other
backend found in the backend path):\n\n''')
    sorted_backends = backend2path.items()
    if len(sorted_backends) > 0:
        sorted_backends.sort(lambda a, b: cmp(a[1], b[1]) or cmp(a[0], b[0]))
        sorted_backends = map(lambda name_dir: name_dir[0], sorted_backends)
        maxnamelen = max(map(len, sorted_backends))
        for bend in sorted_backends:
            if bend in backend_list:
                bullet = "*"
            else:
                bullet = "-"
            odev.write("          %s %-*s (%s)\n" %
                       (bullet, maxnamelen, bend, backend2path[bend]))
    else:
        odev.write("          [none]\n")
    odev.write("\n")
    odev.write("Backend path: %s\n" % string.join(backend_path, ":"))
    odev.write("\n")


def show_installation(odev):
    "Report where coNCePTuaL's Python files were supposedly installed."
    packagedir = ncptl_config["pkgpythondir"]
    metavar_re = re.compile(r'\$\{(\w+)\}')
    metavar = metavar_re.match(packagedir)
    while metavar:
        packagedir = string.replace(packagedir, metavar.group(0), ncptl_config[metavar.group(1)])
        metavar = metavar_re.match(packagedir)
    odev.write("Installation directory: %s\n" % packagedir)
    odev.write("\n")


def usage(exitcode=0):
    "Provide a usage message."
    if exitcode == 0:
        dev = sys.stdout
    else:
        dev = sys.stderr
    dev.write("""Usage: ncptl [--backend=<string>] [--quiet] [--no-link | --no-compile]
         [--keep-ints] [--lenient] [--filter=<sed expr>] [--output=<file>]
         <file.ncptl> | --program=<program>
         [<backend-specific options>]

       ncptl --help

       ncptl [--backend=<string>] --help-backend

""")
    show_backends(dev)
    show_installation(dev)
    dev.write("Report bugs to %s.\n\n" % ncptl_config["PACKAGE_BUGREPORT"])
    raise SystemExit, exitcode


def locate_backend(backend):
    "Search the input argument and the environment for a backend."
    if backend == None:
        try:
            backend = os.environ["NCPTL_BACKEND"]
        except KeyError:
            return None
    if not backend2path.has_key(backend):
        sys.stderr.write("ncptl: Unable to find the %s backend\n\n" % backend)
        show_backends(sys.stderr)
        raise SystemExit, 1
    return backend


def sed_filter(somestring, sedexpr):
    "Apply a sed-style expression to a given string."

    # Split a sed-like substitution expression into a list
    # (e.g., "s/foo/bar/g" --> ["s", "foo", "bar", "g"]).
    bad_subst = 'invalid sed substitution string "%s"' % sedexpr
    sedexpr = string.strip(sedexpr)
    if len(sedexpr) < 5 or sedexpr[0] != "s" or not re.match(r'\S', sedexpr[1]):
        errmsg.error_fatal(badsubst)
    sedfrags = []
    for frag in string.split(sedexpr, sedexpr[1]):
        try:
            if sedfrags[-1][-1] == "\\":
                sedfrags[-1] = sedfrags[-1] + frag
            else:
                sedfrags.append(frag)
        except IndexError:
            sedfrags.append(frag)
    if len(sedfrags) != 4:
        errmsg.error_fatal(badsubst)

    # Convert the list of flag characters to a single number.
    flags = 0
    numsubs = 1
    if not hasattr(re, "UNICODE"):
        # Prevent an error from older versions of Python.
        re.UNICODE = 0
    flag2num = {
        "i": re.IGNORECASE,
        "l": re.LOCALE,
        "m": re.MULTILINE,
        "s": re.DOTALL,
        "u": re.UNICODE,
        "x": re.VERBOSE}
    for flagchar in sedfrags[3]:
        if flagchar == "g":
            numsubs = 0
        else:
            try:
                flags = flags | flag2num[flagchar]
            except KeyError:
                errmsg.error_fatal('unknown substitution flag "%s"' % flagchar)

    # Perform the substitution(s).
    subst_obj = re.compile(sedfrags[1], flags)
    return subst_obj.sub(sedfrags[2], somestring, numsubs)


def test_runability(executable_name):
    "Output a warning message if the generated executable seems unlikely to run."
    if not executable_name or not os.access(executable_name, os.F_OK):
        # Executable doesn't exist (e.g., is "-").
        return
    try:
        dynlib_cmd_tmpl = ncptl_config["DYNLIB_CMD_FMT"]
        dynlib_out = os.popen((dynlib_cmd_tmpl % executable_name)[1:-1])
        oneline = dynlib_out.readline()
        while oneline:
            if string.find(oneline, "ncptl") != -1 and string.find(oneline, "not found") != -1:
                libdir = expanded_ncptl_config["libdir"]
                sys.stderr.write("#\n")
                sys.stderr.write("# WARNING: Don't forget to put %s in your dynamic library search path:\n" % libdir)
                try:
                    ld_library_path = string.join([os.environ["LD_LIBRARY_PATH"], libdir], ":")
                except KeyError:
                    ld_library_path = libdir
                sys.stderr.write("#    [bash] export LD_LIBRARY_PATH=%s\n" % ld_library_path)
                sys.stderr.write("#    [tcsh] setenv LD_LIBRARY_PATH %s\n" % ld_library_path)
                return
            oneline = dynlib_out.readline()
        dynlib_out.close()
    except:
        pass

###########################################################################

# The program starts here.
if __name__ == "__main__":
    # Prepare to issue uniform error messages.
    errmsg = NCPTL_Error("ncptl")

    # Set default values for our command-line parameters.
    outfilename = "-"
    backend = None
    entirefile = None
    backend_options = []
    filter_list = []
    execute_compile = 1
    execute_link = 1
    keep_ints = 0
    lenient = 0
    be_verbose = 1

    # Determine where coNCePTuaL was installed.
    try:
        pythondir = ncptl_config["pythondir"]
        prefix = ncptl_config["prefix"]
        pythondir = re.sub(r'\$\{prefix\}', prefix, pythondir)
    except:
        pythondir = None

    # Look for additional backends.
    backend2path = {}
    backend_path = []
    if os.environ.has_key("NCPTL_PATH"):
        backend_path.extend(string.split(os.environ["NCPTL_PATH"], ":"))
    if pythondir:
        backend_path.append(pythondir)
    backend_path.extend(sys.path)
    backend_path = map(os.path.normpath, backend_path)
    for bdir in backend_path:
        try:
            for somefile in os.listdir(bdir):
                re_matches = re.search(r'^codegen_(.+)\.py[co]?$', somefile)
                if re_matches:
                    new_backend = re_matches.group(1)
                    if not backend2path.has_key(new_backend):
                        backend2path[new_backend] = os.path.normpath(os.path.join(bdir, somefile))
        except:
            # Ignore non-directories and directories we don't have access to.
            pass

    # Parse the command line.
    end_of_options = "--~!@#$%^&*"
    argumentlist = map(lambda a: re.sub(r'^--$', end_of_options, a), sys.argv[1:])
    success = 0
    filelist = []
    options = []
    shortlongopts = [("h",  "help"),
                     ("q",  "quiet"),
                     ("V",  "version"),
                     ("c",  "no-link"),
                     ("E",  "no-compile"),
                     ("K",  "keep-ints"),
                     ("L",  "lenient"),
                     ("o:", "output="),
                     ("b:", "backend="),
                     ("f:", "filter="),
                     ("p:", "program=")]
    shortopts = string.join(map(lambda sl: sl[0], shortlongopts), "")
    longopts = map(lambda sl: sl[1], shortlongopts)
    while not success:
        try:
            opts, args = getopt.getopt(argumentlist, shortopts, longopts)
            options.extend(opts)
            if len(args) == 0:
                success = 1
            else:
                filelist.append(args[0])
                argumentlist = args[1:]
        except getopt.error, errormsg:
            unrecognized = re.match(r'option (\S+) not recognized', str(errormsg))
            if unrecognized:
                # Move the unrecognized parameter and everything that
                # follows it from the argumentlist list to the
                # backend_options list.
                unrec = unrecognized.group(1)
                removed  = 0
                for arg in xrange(0, len(argumentlist)):
                    badarg = argumentlist[arg]
                    if unrec == badarg \
                           or unrec+"=" == badarg[0:len(unrec)+1] \
                           or (unrec[1] != '-' and unrec == badarg[0:2]):
                        if unrec == end_of_options:
                            backend_options.extend(argumentlist[arg+1:])
                        else:
                            backend_options.extend(argumentlist[arg:])
                        backend_options = map(lambda s:
                                                  re.sub(r'^(-H|--help-backend)$',
                                                         "--help", s),
                                              backend_options)
                        argumentlist = argumentlist[0:arg]
                        removed = 1
                        break
                if not removed:
                    errmsg.error_internal('failed to find "%s" in %s' % (unrec, repr(argumentlist)))
            else:
                sys.stderr.write("ncptl: %s\n\n" % errormsg)
                usage(1)
    for opt, optarg in options:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-q", "--quiet"):
            be_verbose = 0
        elif opt in ("-V", "--version"):
            print ncptl_config["PACKAGE_STRING"]
            raise SystemExit, 0
        elif opt in ("-c", "--no-link"):
            execute_link = 0
        elif opt in ("-E", "--no-compile"):
            execute_compile = 0
            execute_link = 0
        elif opt in ("-K", "--keep-ints"):
            keep_ints = 1
        elif opt in ("-L", "--lenient"):
            lenient = 1
        elif opt in ("-o", "--output"):
            outfilename = optarg
        elif opt in ("-b", "--backend"):
            backend = optarg
        elif opt in ("-f", "--filter"):
            filter_list.append(optarg)
        elif opt in ("-p", "--program"):
            entirefile = optarg
            infilename = "<command line>"
        else:
            usage(1)
    if len(filelist) > 1 or (len(filelist) > 0 and entirefile != None):
        # We currently allow only one program to be compiled per invocation.
        usage(1)

    # Load the named backend.
    backend = locate_backend(backend)
    try:
        if backend != None:
            if be_verbose:
                sys.stderr.write("# Loading the %s backend from %s ...\n" %
                                 (backend, os.path.abspath(backend2path[backend])))
            orig_path = sys.path
            if pythondir:
                sys.path.insert(0, pythondir)
            if os.environ.has_key("NCPTL_PATH"):
                sys.path[:0] = string.split(os.environ["NCPTL_PATH"], ":")
            exec("from codegen_%s import NCPTL_CodeGen" % backend)
            sys.path = orig_path
    except ImportError, reason:
        errmsg.error_fatal('unable to load backend "%s" (reason: %s)' %
                           (backend, str(reason)))

    # Prepare to announce what we're going to compile.  This is useful
    # in case the user mistakenly omitted a filename and doesn't
    # realize that ncptl expects input from stdin.
    if entirefile == None:
        if filelist==[] or filelist[0]=="-":
            infilename = "<stdin>"

            # As a special case, if --help appears on the command
            # line, and we would normally read from standard input,
            # specify a dummy, empty program so the backend will
            # output a help message and exit.  Note that --help *must*
            # be a backend option at this point because we've already
            # processed the frontend's command line and therefore
            # would have already seen a frontend --help.
            if "--help" in sys.argv or "--help-backend" in sys.argv or "-H" in sys.argv:
                if backend == None:
                    errmsg.warning('backend help cannot be provided unless a backend is specified')
                    sys.stderr.write("\n")
                    usage(1)
                entirefile = ""
        else:
            infilename = filelist[0]


    # Read the entire input file unless a complete program was
    # provided on the command line.
    if entirefile == None:
        try:
            if be_verbose:
                if infilename == "<stdin>":
                    input_program_source = "the standard input device"
                else:
                    input_program_source = infilename
                sys.stderr.write("# Reading a coNCePTuaL program from %s ...\n" % input_program_source)
            if infilename == "<stdin>":
                entirefile = sys.stdin.read()
            else:
                infile = open(infilename)
                entirefile = infile.read()
                infile.close()
        except IOError, (errno, strerror):
            errmsg.error_fatal("unable to read from %s (%s)" % (infilename, strerror))

    # Instantiate a lexer, parser, and code generator.
    lexer = NCPTL_Lexer()
    parser = NCPTL_Parser(lexer)
    semantic = NCPTL_Semantic()
    if backend != None:
        codegen = NCPTL_CodeGen(backend_options)

    # Compile the program into backend-specific source code.
    try:
        sys.setcheckinterval(100000)
    except AttributeError:
        # Jython 2.2a1 doesn't support sys.setcheckinterval.
        pass
    if be_verbose:
        sys.stderr.write("# Lexing ...\n")
    tokenlist = lexer.tokenize(entirefile, filesource=infilename)
    del lexer
    if be_verbose:
        sys.stderr.write("# Parsing ...\n")
    syntree = parser.parsetokens(tokenlist, filesource=infilename)
    del parser
    if be_verbose:
        sys.stderr.write("# Analyzing program semantics ...\n")
    syntree = semantic.analyze(syntree, filesource=infilename, lenient=lenient)
    del semantic
    if backend == None:
        # If a backend wasn't specified we have nothing left to do.
        if be_verbose:
            sys.stderr.write("# Not compiling %s -- no backend was specified.\n" % infilename)
        sys.exit(0)
    if be_verbose:
        if backend_options == []:
            sys.stderr.write("# Compiling %s using the %s backend ...\n" %
                             (infilename, backend))
        else:
            if len(backend_options) == 1:
                option_word = "option"
            else:
                option_word = "options"
            sys.stderr.write('# Compiling %s using the %s backend with the %s "%s"\n' %
                             (infilename, backend, option_word,
                              string.join(backend_options, " ")))
    codelist = codegen.generate(syntree, filesource=infilename, filetarget=outfilename, sourcecode=entirefile)

    # Filter the code listing if so desired.
    if filter_list != []:
        codestring = string.join(codelist, "\n")
        dummystring = string.join(map(lambda n: chr(random.randint(33, 126)),
                                      [None] * 30),
                                  "")
        for sedexpr in filter_list:
            # Temporarily replace the sed expression with a dummy
            # string so the filter doesn't filter itself.
            codestring = string.replace(sed_filter(string.replace(codestring, sedexpr, dummystring), sedexpr),
                                        dummystring, sedexpr)
        codelist = string.split(codestring, "\n")

    # Write the output file.  Optionally compile it in a
    # backend-specific manner.  Optionally link it in a
    # backend-specific manner.
    if infilename != "<command line>":
        # Put generated files in the current directory.
        infilename = os.path.basename(infilename)
    if execute_link:
        if be_verbose:
            sys.stderr.write("# Compiling and linking the result ...\n")
        true_outfilename = codegen.compile_and_link(infilename, codelist, outfilename, be_verbose, keep_ints)
        if be_verbose:
            test_runability(true_outfilename)
    elif execute_compile:
        if be_verbose:
            sys.stderr.write("# Compiling (but not linking) the result ...\n")
        codegen.compile_only(infilename, codelist, outfilename, be_verbose, keep_ints)
    else:
        try:
            if outfilename == "-":
                if be_verbose:
                    sys.stderr.write("# Writing to standard output ...\n")
                outfile = sys.stdout
            else:
                if be_verbose:
                    sys.stderr.write("# Writing %s ...\n" % outfilename)
                outfile = open(outfilename, "w")
            for oneline in codelist:
                outfile.write("%s\n" % oneline)
            outfile.close()
        except IOError, (errno, strerror):
            errmsg.error_fatal("unable to produce %s (%s)" % (outfilename, strerror))
        if be_verbose:
            if outfilename == "-":
                sys.stderr.write("# Files generated: <standard output>\n")
            else:
                sys.stderr.write("# Files generated: %s\n" % outfilename)
