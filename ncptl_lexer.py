########################################################################
#
# Lexer module for the coNCePTuaL language
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
import string
import os
import lex
from ncptl_error import NCPTL_Error
from ncptl_keywords import Keywords

class NCPTL_Lexer:
    def __init__(self):
        "Initialize the lexer."
        # Define a mapping from each uppercase keyword to its
        # canonicalized form.
        self.canonicalize_kw = {
            "A"           : "AN",
            "AWAIT"       : "AWAITS",
            "BIT"         : "BITS",
            "BUFFER"      : "BUFFERS",
            "BYTE"        : "BYTES",
            "COMPLETION"  : "COMPLETIONS",
            "COMPUTE"     : "COMPUTES",
            "DAY"         : "DAYS",
            "DOUBLEWORD"  : "DOUBLEWORDS",
            "EXECUTE"     : "EXECUTES",
            "HALFWORD"    : "HALFWORDS",
            "HOUR"        : "HOURS",
            "INTEGER"     : "INTEGERS",
            "IS"          : "ARE",
            "IT"          : "THEM",
            "ITS"         : "THEIR",
            "LOG"         : "LOGS",
            "MESSAGE"     : "MESSAGES",
            "MICROSECOND" : "MICROSECONDS",
            "MILLISECOND" : "MILLISECONDS",
            "MINUTE"      : "MINUTES",
            "MULTICAST"   : "MULTICASTS",
            "OUTPUT"      : "OUTPUTS",
            "PAGE"        : "PAGES",
            "PROCESSOR"   : "PROCESSORS",
            "QUADWORD"    : "QUADWORDS",
            "RECEIVE"     : "RECEIVES",
            "REPETITION"  : "REPETITIONS",
            "REDUCE"      : "REDUCES",
            "RESET"       : "RESETS",
            "RESTORE"     : "RESTORES",
            "RESULT"      : "RESULTS",
            "SECOND"      : "SECONDS",
            "SEND"        : "SENDS",
            "SLEEP"       : "SLEEPS",
            "STORE"       : "STORES",
            "SYNCHRONIZE" : "SYNCHRONIZES",
            "TASK"        : "TASKS",
            "TIME"        : "TIMES",
            "TOUCH"       : "TOUCHES",
            "WORD"        : "WORDS"}
        for kw in map(string.upper, Keywords.keywords):
            self.canonicalize_kw[kw] = self.canonicalize_kw.get(kw, kw)

        # Define a list of token names.
        tokens = {}
        for ckw in self.canonicalize_kw.values():
            tokens[ckw] = 1
        tokens = tokens.keys()
        tokens.extend(["comma",
                       "ellipsis",
                       "ident_token",
                       "integer",
                       "lbrace",
                       "lbracket",
                       "logic_and",
                       "logic_or",
                       "lparen",
                       "op_and",
                       "op_div",
                       "op_eq",
                       "op_geq",
                       "op_gt",
                       "op_leq",
                       "op_lshift",
                       "op_lt",
                       "op_minus",
                       "op_mult",
                       "op_neq",
                       "op_or",
                       "op_plus",
                       "op_power",
                       "op_rshift",
                       "period",
                       "rbrace",
                       "rbracket",
                       "rparen",
                       "star",
                       "string_token"])
        self.tokens = tokens

    def tokenize(self, sourcecode, filesource='<stdin>'):
        "Tokenize the given string of source code."
        self.errmsg = NCPTL_Error(filesource)

        # Keep track of all the comments we've encountered by storing
        # a mapping from line number to comment (including the initial
        # hash character).
        self.line2comment = {}

        # Initialize the lexer.
        lex.lex(module=self)

        # Repeatedly invoke the lexer and return all of the tokens it produces.
        self.lineno = 1
        lex.input(sourcecode)
        self.toklist = []
        while 1:
            # Acquire the next token and assign it a line number if necessary.
            token = lex.token()
            if not token:
                break
            if token.lineno < self.lineno:
                token.lineno = self.lineno

            # Hack: Disambiguate op_mult and star on the parser's behalf.
            if token.type in ["comma", "rparen"]:
                try:
                    if self.toklist[-1].type == "op_mult":
                        self.toklist[-1].type = "star"
                except IndexError:
                    pass

            # We now have one more valid token.
            self.toklist.append(token)
        return self.toklist

    # Define a bunch of simple token types.
    t_comma       = r' , '
    t_ellipsis    = r' \.\.\. '
    t_lbrace      = r' \{ '
    t_lbracket    = r' \[ '
    t_logic_and   = r' /\\ '
    t_logic_or    = r' \\/ '
    t_lparen      = r' \( '
    t_op_and      = r' & '
    t_op_div      = r' / '
    t_op_eq       = r' = '
    t_op_geq      = r' >= '
    t_op_gt       = r' > '
    t_op_leq      = r' <= '
    t_op_lshift   = r' << '
    t_op_lt       = r' < '
    t_op_minus    = r' - '
    t_op_mult     = r' \* '
    t_op_neq      = r' <> '
    t_op_or       = r' \| '
    t_op_plus     = r' \+ '
    t_op_power    = r' \*\* '
    t_op_rshift   = r' >> '
    t_period      = r' \. '
    t_rbrace      = r' \} '
    t_rbracket    = r' \] '
    t_rparen      = r' \) '

    # Keep track of line numbers.
    def t_newline(self, token):
        r' \r?\n '
        self.lineno = self.lineno + 1
        return None

    # Ignore whitespace.
    def t_whitespace(self, token):
        r' [ \t]+ '
        return None

    # Remove comments.
    def t_comment(self, token):
        r' \#.* '
        self.line2comment[self.lineno] = token.value
        return None

    # Sanitize and store string literals.
    def t_string_token(self, token):
        r' \"([^\\]|(\\[\000-\177]))*?\" '
        sanitized = []
        c = 1
        while c < len(token.value)-1:
            onechar = token.value[c]
            if onechar == "\\":
                c = c + 1
                onechar = token.value[c]
                if onechar == "n":
                    sanitized.append("\n")
                elif onechar == "t":
                    sanitized.append("\t")
                elif onechar == "r":
                    sanitized.append("\r")
                elif onechar == "\n":
                    self.lineno = self.lineno + 1
                elif onechar in ["\\", '"']:
                    sanitized.append(onechar)
                else:
                    self.errmsg.warning('Discarding unrecognized escape sequence "\\%s"' % onechar,
                                        lineno0=self.lineno, lineno1=self.lineno)
            else:
                sanitized.append(onechar)
                if onechar == "\n":
                    self.lineno = self.lineno + 1
            c = c + 1
        token.value = '"%s"' % string.join(sanitized, "")
        token.lineno = self.lineno
        return token

    # Store idents as "ident" and keywords as themselves (uppercased).
    def t_ident_or_keyword(self, token):
        r' [A-Za-z]\w* '
        try:
            # Store a keyword with its value (uppercase) as its type.
            token.type = self.canonicalize_kw[string.upper(token.value)]
            if len(self.toklist) > 0 and self.toklist[-1].value == "-":
                # A "-" before a keyword is treated as whitespace.
                self.toklist.pop()
        except KeyError:
            # Store an identifier with a tuple for a value:
            # {lowercase, original}.
            token.type = "ident_token"
            token.value = (string.lower(token.value), token.value)
        token.lineno = self.lineno
        return token

    # Store an integer as a tuple {long-expanded, original}.  Note
    # that coNCePTuaL integers can contain a trailing multiplier, a
    # trailing exponent, and a trailing "st", "nd", "rd", or "th".
    def t_integer(self, token):
        r' \d+([KMGkmg]|([Ee]\d+))?([Ss][Tt]|[NnRr][Dd]|[Tt][Hh]?)? '
        canon_token = re.sub(r'(st|nd|rd|th)$', "", string.lower(token.value))
        parts = re.split(r'([kmgte])', canon_token, 1)
        if not parts[-1]:
            parts = parts[:-1]
        number = long(parts[0])
        if len(parts) == 2:
            if parts[1] == "k":
                number = number * 1024L
            elif parts[1] == "m":
                number = number * 1024L**2
            elif parts[1] == "g":
                number = number * 1024L**3
            elif parts[1] == "t":
                number = number * 1024L**4
            else:
                self.errmsg.error_syntax(token.value, lineno0=token.lineno, lineno1=token.lineno)
        elif len(parts) == 3:
            number = number * 10**long(parts[2])
        token.value = (number, token.value)
        token.lineno = self.lineno
        return token

    # Everything else we encounter should return a syntax error.
    def t_error(self, token):
        self.errmsg.error_syntax(token.value[0], lineno0=token.lineno, lineno1=token.lineno)


# If the lexer is run as a standalone program, output a mapping from
# keyword to canonicalized keyword in the format needed by the
# coNCePTuaL IDE's keyword-map file.
if __name__ == '__main__':
    lexer = NCPTL_Lexer()
    keywords = lexer.canonicalize_kw.keys()
    keywords.sort()
    for keyw in keywords:
        print "%-35.35s %s" % (keyw, lexer.canonicalize_kw[keyw])
