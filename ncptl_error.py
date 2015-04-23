########################################################################
#
# Error and warning generation for the coNCePTuaL compiler
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# 
# Copyright (C) 2015, Los Alamos National Security, LLC
# All rights reserved.
# 
# Copyright (2015).  Los Alamos National Security, LLC.  This software
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


class NCPTL_Error:
    def __init__(self, filename=None):
        "Initialize the error class."
        self.filename = filename
    
    def _report_problem(self, message, lineno0=0, lineno1=0, filename=None):
        """
            Report a problem but continue running the program.  This
            method is used to implement warnings, errors, and internal
            errors.
        """
        if not filename and not hasattr(self, "filename"):
            # We haven't yet been given a filename.
            sys.stderr.write("ncptl: %s\n" % message)
            return
        if not filename:
            filename = self.filename
        if lineno0:
            # For now, we don't use lineno1 but we might in a future version.
            sys.stderr.write("%s:%s: %s\n" %
                             (filename, lineno0, message))
        else:
            sys.stderr.write("%s: %s\n" % (filename, message))

    def warning(self, message, lineno0=0, lineno1=0, filename=None):
        "Issue a warning message but continue running the program."
        self._report_problem("warning: %s" % message,
                             lineno0, lineno1, filename)

    def error_fatal(self, message, lineno0=0, lineno1=0, filename=None):
        "Produce an error message and abort the program."
        self._report_problem(message, lineno0, lineno1, filename)
        raise SystemExit, 1

    def error_internal(self, message, lineno0=0, lineno1=0, filename=None):
        'Produce an "internal error" message and abort the program.'
        def caller_location():
            "Return a {filename, line number} tuple representing our caller."
            try:
                raise Exception
            except:
                grandparent_frame = sys.exc_info()[2].tb_frame.f_back.f_back
                return (grandparent_frame.f_globals["__file__"], grandparent_frame.f_lineno)
        grandparent_filename, grandparent_lineno = caller_location()
        if lineno0 == 0 and lineno1 == 0:
            lineno0 = grandparent_lineno
            lineno1 = grandparent_lineno
        if filename == None:
            filename = os.path.basename(grandparent_filename)
            if filename[-4:] == ".pyc":
                filename = filename[:-1]
        self.error_fatal("internal error: %s" % message,
                         lineno0=lineno0, lineno1=lineno1, filename=filename)

    def error_parse(self, message, lineno0=0, lineno1=0, filename=None):
        'Produce an "parse error" message and abort the program.'
        self.error_fatal("parse error at or near `%s'" % message,
                         lineno0=lineno0, lineno1=lineno1, filename=filename)

    def error_syntax(self, message, lineno0=0, lineno1=0, filename=None):
        'Produce an "syntax error" message and abort the program.'
        self.error_fatal("syntax error at or near `%s'" % message,
                         lineno0=lineno0, lineno1=lineno1, filename=filename)
