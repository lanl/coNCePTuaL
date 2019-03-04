########################################################################
#
# Parser module for the coNCePTuaL language
#
# By Scott Pakin <pakin@lanl.gov>
#
# ----------------------------------------------------------------------
#
# 
# Copyright (C) 2003, Triad National Security, LLC
# All rights reserved.
# 
# Copyright (2003).  Triad National Security, LLC.  This software
# was produced under U.S. Government contract 89233218CNA000001 for
# Los Alamos National Laboratory (LANL), which is operated by Los
# Alamos National Security, LLC (Triad) for the U.S. Department
# of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
#   * Neither the name of Triad National Security, LLC, Los Alamos
#     National Laboratory, the U.S. Government, nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
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
import types
import copy
import lex
import yacc
from ncptl_ast import AST
from ncptl_token import Token
from ncptl_error import NCPTL_Error
from ncptl_config import ncptl_config
from ncptl_lexer import NCPTL_Lexer
try:
    from java.security import AccessControlException
except ImportError:
    class AccessControlException(Exception):
        pass


# Define the name of the parse table to generate.
_tabmodule = "ncptl_parse_table"

class NCPTL_Parser:
    language_version = "1.5"

    def __init__(self, lexer):
        "Initialize the coNCePTuaL parser."
        self.lexer = lexer
        self.tokens = lexer.tokens
        self._opname = {'/\\'     : 'op_land',
                        '\\/'     : 'op_lor',
                        '='       : 'op_eq',
                        '<'       : 'op_lt',
                        '>'       : 'op_gt',
                        '<='      : 'op_le',
                        '>='      : 'op_ge',
                        '<>'      : 'op_ne',
                        'DIVIDES' : 'op_divides',
                        '+'       : 'op_plus',
                        '-'       : 'op_minus',
                        '|'       : 'op_or',
                        'XOR'     : 'op_xor',
                        '**'      : 'op_power',
                        '*'       : 'op_mult',
                        '/'       : 'op_div',
                        'MOD'     : 'op_mod',
                        '>>'      : 'op_shr',
                        '<<'      : 'op_shl',
                        '&'       : 'op_and',
                        'u+'      : 'op_pos',
                        'u-'      : 'op_neg',
                        'uNOT'    : 'op_not'}
        self.precedence = (tuple(['nonassoc'] + self.tokens),)
        self.parser_list = {}

    def parsetokens(self, tokenlist, filesource='<stdin>', start="program", write_tables=0):
        "Parse a list of tokens into an AST."
        self.tokenlist = tokenlist
        self.tokidx = 0
        self.errmsg = NCPTL_Error(filesource)
        if not write_tables:
            # Suppress "yacc: Symbol '...' is unreachable" messages.
            orig_stderr = sys.stderr
            try:
                sys.stderr = open(ncptl_config["NULL_DEVICE_NAME"][1:-1], "w")
            except (IOError, AccessControlException):
                # We were built under one operating system but are
                # running under a different operating system.  (We
                # might be running as a Java program.)  Alternatively,
                # we might be running in a sandbox with limited file
                # access.
                pass
        try:
            parser = self.parser_list[start]
        except KeyError:
            parser = yacc.yacc(module=self, start=start,
                               debug=0, tabmodule=_tabmodule,
                               write_tables=write_tables,
                               outputdir=os.path.dirname(__import__(self.__module__).__file__))
            self.parser_list[start] = parser
        if not write_tables:
            # Restore the stderr filehandle.
            if sys.stderr != orig_stderr:
                sys.stderr.close()
                sys.stderr = orig_stderr
        return parser.parse(lexer=self)

    def p_error(self, lextoken):
        try:
            token = self._lextoken2token(lextoken)
        except AttributeError:
            # We might have failed trying to parse an empty token list.
            token = Token(type="", attr="", lineno=1)
        self.errmsg.error_parse(token.printable, token.lineno, token.lineno)

    def token(self):
        "Return the next token in the list."
        try:
            next_token = self.tokenlist[self.tokidx]
            self.tokidx = self.tokidx + 1
            return next_token
        except IndexError:
            return None

    def _lextoken2token(self, lextoken):
        "Convert a PLY LexToken object to a coNCePTuaL Token object."
        try:
            if type(lextoken.value) not in (types.ListType, types.TupleType):
                raise TypeError
            printable = lextoken.value[1]
            attr = lextoken.value[0]
        except (TypeError, IndexError):
            printable = lextoken.value
            attr = lextoken.value
        return Token(lineno=lextoken.lineno,
                     type=lextoken.type,
                     attr=attr,
                     printable=printable)

    def _token2ast(self, token, left=None, right=None, kids=None):
        "Convert a token to an AST."
        if not kids:
            kids = []
        return AST(type=token, left=left, right=right, kids=kids)

    def _lextoken2ast(self, lextoken, left=None, right=None, kids=None):
        "Convert a token to an AST."
        token = self._lextoken2token(lextoken)
        return self._token2ast(token, left=left, right=right, kids=kids)

    def _str2ast(self, str, lineno=-1, lineno0=-1, lineno1=-1,
                 attr=None, left=None, right=None, kids=None, printable=""):
        "Convert a string into an AST."
        dummyToken = Token(type=str, attr=attr, lineno=lineno)
        dummyToken.printable = printable
        if lineno0 != -1:
            dummyToken.lineno0 = lineno0
        if lineno1 != -1:
            dummyToken.lineno1 = lineno1
        if not kids:
            kids = []
        return AST(type=dummyToken, left=left, right=right, kids=kids)

    def _wrapAST(self, typestr, args, kidofs=None, attr=None, assign0state=1,
                 source_task=None, target_tasks=None):
        "Wrap args[kidofs] in an AST of a given type."
        # Determine the subset of args to use and the corresponding
        # line numbers.
        if kidofs == None:
            kidofs = range(1, len(args.slice))
        else:
            kidofs.sort()
        if kidofs == []:
            lineno0, lineno1 = args.linespan(0)
        else:
            lineno0, lineno1 = self._linespan(args, first=kidofs[0], last=kidofs[-1])

        # Create new ASTs for source and target tasks, if specified.
        args_copy = args
        if source_task != None:
            args_copy[source_task] = self._make_source_task(args, source_task)
        if target_tasks != None:
            args_copy[target_tasks] = self._make_target_tasks(args, target_tasks)

        # Create a new AST.
        newAST = self._str2ast(typestr,
                               lineno0=lineno0, lineno1=lineno1,
                               kids=filter(lambda k: hasattr(k, "attr"),
                                           map(lambda o, args_copy=args_copy: args_copy[o], kidofs)),
                               attr=attr)

        # Assign extra state to the AST and return it.
        if assign0state:
            self._assign0state(args_copy, ast=newAST, kidofs=kidofs)
        return newAST

    def _wrapAST_twice(self, typestr1, typestr2, args, kidofs=None, attr=None,
                       assign0state=1, source_task=None, target_tasks=None):
        """
             Wrap args[kidofs] in an AST of a given type and wrap that
             in an AST of a second type.
        """
        innerAST = self._wrapAST(typestr2, args, kidofs, attr, assign0state,
                                 source_task, target_tasks)
        outerAST = self._wrapAST(typestr1, args, kidofs, None, assign0state)
        outerAST.kids = [innerAST]
        return outerAST

    def _hoist_buffer_offset(self, message_spec):
        "Move a buffer_offset from a child of buffer_number to a child of message_spec."
        buffer_offset = message_spec.kids[6].kids[0]
        if buffer_offset.type != "buffer_offset":
            self.errmsg.error_internal("Expected buffer_offset; found %s" % buffer_offset.type)
        del message_spec.kids[6].kids[0]
        message_spec.kids.insert(6, buffer_offset)

    def _apply2attr(self, func, astlist):
        "Apply a function to the (unique) leaf's attribute."
        if len(astlist.kids) == 0:
            # Leaf
            astlist.attr = func(astlist.attr)
        elif len(astlist.kids) == 1:
            # Unique child
            self._apply2attr(func, astlist.kids[0])
        else:
            raise TypeError, "leaf is not unique"

    def _linespan(self, args, first=1, last=None):
        """
             Return the first line number of the first argument and
             the last line number of the last argument.
        """
        if last == None:
            last = len(args.slice) - 1
        lineno0, not_used = args.linespan(first)
        not_used, lineno1 = args.linespan(last)
        return (lineno0, lineno1)

    def _assign0state(self, args, ast=None, kidofs=None):
        "Assign line numbers to args[0] and introduce an is_empty attribute."
        # Determine the subset of args[] that we care about
        if kidofs == None:
            numargs = len(args.slice)
            if numargs == 1:
                kidofs = []
            elif numargs == 2:
                kidofs = [1]
            else:
                kidofs = range(1, numargs)

        # Assign empty status and line numbers.  We set lineno0 to the
        # smallest nonzero line number encountered and lineno1 to the
        # largest nonzero line number encountered.
        if ast == None:
            ast = args[0]
        ast.is_empty = int(len(args.slice) == 1)
        if ast.is_empty:
            ast.lineno0, ast.lineno1 = 0, 0
        minlineno0, maxlineno1 = sys.maxint, 0
        for argnum in kidofs:
            try:
                # AST
                lineno0, lineno1 = args[argnum].lineno0, args[argnum].lineno1
            except AttributeError:
                # LexToken
                lineno0 = args.slice[argnum].lineno
                lineno1 = lineno0
            if lineno0 != 0 and minlineno0 > lineno0:
                minlineno0 = lineno0
            if lineno1 != 0 and maxlineno1 < lineno1:
                maxlineno1 = lineno1
        if minlineno0 == sys.maxint:
            minlineno0 = 0
        ast.lineno0, ast.lineno1 = minlineno0, maxlineno1

        # Assign printable text to the AST.
        printable = []
        max_text_len = 2**30    # Truncate strings after this many characters.
        for argnum in kidofs:
            arg = args[argnum]
            if isinstance(arg, AST):
                # AST
                if hasattr(arg, "printable"):
                    printable.append(arg.printable)
                else:
                    printable_list = map(lambda k: k.printable, arg.kids)
                    kidprintable = string.join(printable_list, "")
                    arg.printable = kidprintable
                    printable.append(kidprintable)
            elif isinstance(arg, str):
                # Token (string)
                if arg in [".", ","] and argnum > 0:
                    # As a special case, don't put a space before "." or ",".
                    printable[-1] = printable[-1] + arg
                else:
                    printable.append(arg)
            elif isinstance(arg, tuple):
                # Token (integer)
                printable.append(arg[-1])
            else:
                self.errmsg.error_internal('Unexpected argument type "%s"' % str(type(arg)))
        complete_text = string.join(filter(lambda s: s != "", printable), " ")
        complete_text = string.replace(string.replace(complete_text, "( ", "("),
                                       " )", ")")
        if len(complete_text) > max_text_len:
            complete_text = complete_text[:max_text_len] + " ..."
        ast.printable = complete_text

    def _make_source_task(self, args, argnum):
        "Validate a source-style task_expr and return a source_task AST."
        ast = args[argnum]
        if ast.type != "task_expr":
            self.errmsg.error_internal('Expected an AST of type "task_expr" but found "%s"' % ast.type)
        return self._wrapAST("source_task", args, kidofs=[argnum])

    def _make_target_tasks(self, args, argnum):
        "Validate a target-style task_expr and return a target_tasks AST."
        ast = args[argnum]
        if ast.type != "task_expr":
            self.errmsg.error_internal('Expected an AST of type "task_expr" but found "%s"' % ast.type)
        return self._wrapAST("target_tasks", args, kidofs=[argnum])


    def _dump_grammar(self):
        "Output the complete grammar in a format suitable for the coNCePTuaL GUI."
        # Store all of the main grammar rules.
        rulelist = []
        allfuncs = self.__class__.__dict__
        for funcname in allfuncs.keys():
            if funcname[:2] != "p_" or funcname == "p_error":
                continue
            rule = string.strip(allfuncs[funcname].__doc__)
            (lhs, all_rhs) = string.split(rule, None, 1)
            for sep_rhs in string.split(all_rhs, "\n"):
                try:
                    # Right-hand side is nonempty.
                    (sep, rhs) = string.split(sep_rhs, None, 1)
                    rulelist.append("%s ::= %s" % (lhs, rhs))
                except:
                    # Right-hand side is empty.
                    rulelist.append("%s ::=" % lhs)

        # Store all of the rules that map to literal symbol sequences.
        alltoks = self.lexer.__class__.__dict__
        for tokname in alltoks.keys():
            if tokname[:2] != "t_":
                continue
            try:
                # String
                rhs = re.sub(r'\\(.)', r'\1', string.strip(alltoks[tokname]))
                rulelist.append("%s ::= %s" % (tokname[2:], rhs))
            except AttributeError:
                # Function
                pass

        # Output the sorted list of rules.
        rulelist.sort()
        for rule in rulelist:
            print rule


    #---------------------------#
    # Start rules (and helpers) #
    #---------------------------#

    def p_program_1(self, args):
        '''
             program :
                     | header_decl_list
        '''
        args[0] = self._wrapAST("program", args)
        if args[0].lineno0 == 0:
            # Prevent the semantic analyzer from complaining about
            # empty programs.
            args[0].lineno0 = 1
            args[0].lineno1 = 1

    def p_program_2(self, args):
        '''
             program : top_level_stmt_list
                     | header_decl_list top_level_stmt_list
        '''
        args[0] = self._wrapAST("program", args)

    def p_top_level_stmt_list_1(self, args):
        '''
             top_level_stmt_list : top_level_stmt
                                 | top_level_stmt period
        '''
        args[0] = self._wrapAST("top_level_stmt_list", args, attr=1L)

    def p_top_level_stmt_list_2(self, args):
        '''
             top_level_stmt_list : top_level_stmt top_level_stmt_list
                                 | top_level_stmt period top_level_stmt_list
        '''
        numentries = args[len(args)-1].attr + 1L
        args[len(args)-1].attr = None
        args[0] = self._str2ast("top_level_stmt_list", attr=numentries,
                                kids=[args[1]] + args[len(args)-1].kids)
        self._assign0state(args)


    #---------------------#
    # Header declarations #
    #---------------------#

    def p_header_decl_list_1(self, args):
        '''
             header_decl_list : header_decl
                              | header_decl period
        '''
        args[0] = self._wrapAST("header_decl_list", args, attr=1L)

    def p_header_decl_list_2(self, args):
        '''
             header_decl_list : header_decl header_decl_list
                              | header_decl period header_decl_list
        '''
        numentries = args[len(args)-1].attr + 1L
        args[len(args)-1].attr = None
        args[0] = self._str2ast("header_decl_list", attr=numentries,
                                kids=[args[1]] + args[len(args)-1].kids)
        self._assign0state(args)

    def p_header_decl(self, args):
        '''
            header_decl : param_decl
                        | version_decl
                        | backend_decl
        '''
        args[0] = self._wrapAST("header_decl", args)

    def p_param_decl(self, args):
        ' param_decl : ident ARE string AND COMES FROM string OR string WITH DEFAULT expr '
        args[0] = self._wrapAST("param_decl", args)

    def p_version_decl(self, args):
        ' version_decl : REQUIRE LANGUAGE VERSION string '
        requested_version = args[4].attr
        if requested_version != self.language_version:
            self.errmsg.warning('language version "%s" was requested but only version "%s" is supported' %
                                (requested_version, self.language_version),
                                args[4].lineno0, args[4].lineno1)
        args[0] = self._wrapAST("version_decl", args,
                                attr=[requested_version, self.language_version])

    def p_backend_decl(self, args):
        ' backend_decl : THE BACKEND DECLARES string '
        args[0] = self._wrapAST("backend_decl", args)


    #------------#
    # Statements #
    #------------#

    def p_top_level_stmt(self, args):
        ' top_level_stmt : simple_stmt_list '
        args[0] = self._wrapAST("top_level_stmt", args)

    def p_simple_stmt_list_1(self, args):
        ' simple_stmt_list : simple_stmt '
        args[0] = self._wrapAST("simple_stmt_list", args, attr=1L)

    def p_simple_stmt_list_2(self, args):
        ' simple_stmt_list : simple_stmt THEN simple_stmt_list '
        numentries = args[3].attr + 1L
        args[3].attr = None
        args[0] = self._str2ast("simple_stmt_list", attr=numentries,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_simple_stmt_1(self, args):
        '''
             simple_stmt : send_stmt
                         | mcast_stmt
                         | receive_stmt
                         | delay_stmt
                         | wait_stmt
                         | sync_stmt
                         | touch_stmt
                         | touch_buffer_stmt
                         | log_stmt
                         | log_flush_stmt
                         | reset_stmt
                         | store_stmt
                         | restore_stmt
                         | assert_stmt
                         | output_stmt
                         | backend_stmt
                         | processor_stmt
                         | reduce_stmt
        '''
        args[0] = self._wrapAST("simple_stmt", args)

    def p_simple_stmt_2(self, args):
        ' simple_stmt : FOR EACH ident IN range_list simple_stmt '
        args[0] = self._wrapAST_twice("simple_stmt", "for_each", args)

    def p_simple_stmt_3(self, args):
        '''
             simple_stmt : FOR expr REPETITIONS simple_stmt
                         | FOR expr REPETITIONS PLUS expr WARMUP REPETITIONS simple_stmt
                         | FOR expr REPETITIONS PLUS expr WARMUP REPETITIONS AND AN SYNCHRONIZATION simple_stmt
        '''
        if len(args.slice) == 12:
            attr = "synchronized"
        else:
            attr = ""
        args[0] = self._wrapAST_twice("simple_stmt", "for_count", args, attr=attr)

    def p_simple_stmt_4(self, args):
        '''
             simple_stmt : FOR expr time_unit simple_stmt
                         | FOR expr time_unit PLUS expr WARMUP time_unit simple_stmt
                         | FOR expr time_unit PLUS expr WARMUP time_unit AND AN SYNCHRONIZATION simple_stmt
        '''
        if len(args.slice) == 12:
            attr = "synchronized"
        else:
            attr = ""
        args[0] = self._wrapAST_twice("simple_stmt", "for_time", args, attr=attr)

    def p_simple_stmt_5(self, args):
        ' simple_stmt : LET let_binding_list WHILE simple_stmt '
        args[0] = self._wrapAST_twice("simple_stmt", "let_stmt", args)

    def p_simple_stmt_6(self, args):
        ' simple_stmt : lbrace simple_stmt_list rbrace '
        args[0] = self._wrapAST("simple_stmt", args)

    def p_simple_stmt_7(self, args):
        ' simple_stmt : lbrace rbrace '
        args[0] = self._wrapAST("empty_stmt", args)

    def p_simple_stmt_8(self, args):
        '''
             simple_stmt : IF rel_expr THEN simple_stmt
                         | IF rel_expr THEN simple_stmt OTHERWISE simple_stmt
        '''
        args[0] = self._wrapAST_twice("simple_stmt", "if_stmt", args)

    def p_send_stmt_1(self, args):
        ' send_stmt : task_expr opt_async SENDS message_spec TO opt_unsusp task_expr '
        # To simplify argument processing, assign a name to each argument.
        source_arg = self._make_source_task(args, 1)
        async_arg = args[2]
        msg_spec_arg = args[4]
        unsusp_arg = args[6]
        target_arg = self._make_target_tasks(args, 7)

        # Construct a list of send attributes.
        attributes = []
        async_lineno = args.lineno(3)
        if async_arg.attr:
            attributes.append("asynchronously")
            async_lineno = async_arg.lineno0
        unsusp_lineno = target_arg.lineno0
        if unsusp_arg.attr:
            attributes.append("unsuspecting")
            unsusp_lineno = unsusp_arg.lineno1
        attrAST = self._str2ast("send_attrs", attr=attributes,
                                lineno0=async_lineno, lineno1=unsusp_lineno)
        attrAST.printable = string.join(filter(lambda s: s != "",
                                               [async_arg.printable, unsusp_arg.printable]),
                                        " ... ")

        # Convert a message_spec into a recv_message_spec.
        recv_attrAST = copy.deepcopy(attrAST)
        recv_attrAST.type = "receive_attrs"
        recv_message_spec = copy.deepcopy(msg_spec_arg)
        recv_message_spec.kids[7].type = "recv_buffer_number"
        if recv_message_spec.kids[7].attr == "from":
            recv_message_spec.kids[7].attr = "into"

        # Create and return an AST with all the information needed to
        # send and receive a set of messages.
        args[0] = self._str2ast("send_stmt",
                                kids=[source_arg, msg_spec_arg, attrAST,
                                      target_arg, recv_message_spec, recv_attrAST])
        self._assign0state(args)

    def p_send_stmt_2(self, args):
        ' send_stmt : task_expr opt_async SENDS message_spec TO opt_unsusp task_expr WHO RECEIVES THEM recv_message_spec '
        # To simplify argument processing, assign a name to each argument.
        source_arg = self._make_source_task(args, 1)
        async_arg = args[2]
        msg_spec_arg = args[4]
        opt_unsusp_arg = args[6]
        target_arg = self._make_target_tasks(args, 7)
        recv_msg_spec_arg = args[11]
        if not opt_unsusp_arg.is_empty:
            # The only reason we included opt_unsusp above is to
            # appease the SLR parser.
            self.errmsg.error_parse("unsuspecting",
                                    opt_unsusp_arg.lineno0, opt_unsusp_arg.lineno1)

        # Construct a list of send attributes.
        attributes = []
        async_lineno = args.lineno(3)
        if async_arg.attr:
            attributes.append("asynchronously")
            async_lineno = async_arg.lineno0
        attrAST = self._str2ast("send_attrs", attr=attributes,
                                lineno0=async_lineno, lineno1=args.lineno(5))
        attrAST.printable = async_arg.printable

        # Complain if *all* optional arguments were omitted.
        no_arguments = 1
        for child in recv_msg_spec_arg.kids:
            if not child.is_empty:
                no_arguments = 0
                break
        if no_arguments:
            self.errmsg.error_parse(args.slice[10].value, args.lineno(10), args.lineno(10))

        # The receiver receives the message(s) with different
        # attributes from what the sender uses to send them.
        recv_info = recv_msg_spec_arg.kids
        recv_message_spec = copy.deepcopy(recv_msg_spec_arg)
        recv_message_spec.type = "message_spec"
        del recv_message_spec.kids[0]
        recv_message_spec.kids[0] = copy.deepcopy(msg_spec_arg.kids[0])
        recv_message_spec.kids.insert(2, copy.deepcopy(msg_spec_arg.kids[2]))

        # Overwrite all fabricated attributes with the sender's version.
        for arg in range(0, len(recv_info)):
            if recv_info[arg].is_fabricated:
                recv_message_spec.kids[arg] = copy.deepcopy(msg_spec_arg.kids[arg])
        recv_message_spec.kids[7].type = "recv_buffer_number"
        if recv_info[0].is_fabricated:
            # Copy the sender's attributes.
            recv_attributes = attributes
        elif recv_info[0].attr:
            recv_attributes = ["asynchronously"]
        else:
            recv_attributes = []
        if recv_message_spec.attr == -1:
            # Copy the misalignment flag from the sender.
            recv_message_spec.attr = msg_spec_arg.attr
        recv_attrAST = self._str2ast("receive_attrs", attr=recv_attributes,
                                     lineno0=recv_msg_spec_arg.lineno0,
                                     lineno1=recv_msg_spec_arg.lineno1)
        recv_attrAST.printable = args[11].printable

        # Create and return an AST with all the information needed to
        # send and receive a set of messages.
        args[0] = self._str2ast("send_stmt",
                                kids=[source_arg, msg_spec_arg, attrAST,
                                      target_arg, recv_message_spec, recv_attrAST])
        self._assign0state(args)

    def p_mcast_stmt(self, args):
        ' mcast_stmt : task_expr opt_async MULTICASTS message_spec TO task_expr '
        sourceAST = self._make_source_task(args, 1)
        if args[2].attr:
            attrAST = self._wrapAST("send_attrs", args,
                                    attr=["asynchronously"], kidofs=[2])
        else:
            attrAST = self._wrapAST("send_attrs", args, attr=[], kidofs=[])
        targetAST = self._make_target_tasks(args, 6)
        args[0] = self._str2ast("mcast_stmt",
                                kids=[sourceAST, args[4], targetAST, attrAST])
        self._assign0state(args)

    def p_receive_stmt(self, args):
        ' receive_stmt : task_expr opt_async RECEIVES message_spec_into FROM task_expr '
        targetAST = self._make_target_tasks(args, 1)
        attr = []
        if args[2].attr:
            attr = ["asynchronously"]
        attrAST = self._wrapAST("receive_attrs", args, attr=attr, kidofs=[2])
        attrAST.kids = []
        sourceAST = self._make_source_task(args, 6)
        args[0] = self._str2ast("receive_stmt", kids=[targetAST, args[4], sourceAST, attrAST])
        self._assign0state(args)

    def p_delay_stmt(self, args):
        '''
             delay_stmt : task_expr COMPUTES FOR expr time_unit
                        | task_expr SLEEPS FOR expr time_unit
        '''
        args[0] = self._wrapAST("%s_%s" % (args.slice[2].type, args.slice[3].type),
                                args, source_task=1)

    def p_wait_stmt(self, args):
        ' wait_stmt : task_expr AWAITS COMPLETIONS '
        args[0] = self._wrapAST("awaits_completion", args, source_task=1)

    def p_sync_stmt(self, args):
        ' sync_stmt : task_expr SYNCHRONIZES '
        args[0] = self._wrapAST("sync_stmt", args, source_task=1)

    def p_touch_stmt(self, args):
        '''
             touch_stmt : task_expr TOUCHES expr data_type OF AN item_size MEMORY REGION touch_repeat_count stride
                        | task_expr TOUCHES AN item_size MEMORY REGION touch_repeat_count stride
        '''
        args[0] = self._wrapAST("touch_stmt", args, source_task=1)

    def p_touch_buffer_stmt(self, args):
        '''
             touch_buffer_stmt : task_expr TOUCHES ALL MESSAGES BUFFERS
                               | task_expr TOUCHES THE CURRENT MESSAGES BUFFERS
                               | task_expr TOUCHES MESSAGES BUFFERS expr
        '''
        if args.slice[3].type == "ALL":
            attr = "all"
        elif args.slice[3].type == "THE":
            attr = "current"
        else:
            attr = "expr"
        args[0] = self._wrapAST("touch_buffer_stmt", args, attr=attr, source_task=1)

    def p_log_stmt(self, args):
        ' log_stmt : task_expr LOGS log_expr_list '
        args[0] = self._wrapAST("log_stmt", args, source_task=1)

    def p_log_flush_stmt(self, args):
        ' log_flush_stmt : task_expr COMPUTES AGGREGATES '
        args[0] = self._wrapAST("log_flush_stmt", args, source_task=1)

    def p_reset_stmt(self, args):
        ' reset_stmt : task_expr RESETS THEIR COUNTERS '
        args[0] = self._wrapAST("reset_stmt", args, source_task=1)

    def p_store_stmt(self, args):
        ' store_stmt : task_expr STORES THEIR COUNTERS '
        args[0] = self._wrapAST("store_stmt", args, source_task=1)

    def p_restore_stmt(self, args):
        ' restore_stmt : task_expr RESTORES THEIR COUNTERS '
        args[0] = self._wrapAST("restore_stmt", args, source_task=1)

    def p_assert_stmt(self, args):
        ' assert_stmt : ASSERT THAT string WITH rel_expr '
        args[0] = self._wrapAST("assert_stmt", args)

    def p_output_stmt(self, args):
        ' output_stmt : task_expr OUTPUTS string_or_expr_list '
        args[0] = self._wrapAST("output_stmt", args, source_task=1)

    def p_backend_stmt(self, args):
        ' backend_stmt : task_expr BACKEND EXECUTES string_or_expr_list '
        args[0] = self._wrapAST("backend_stmt", args, source_task=1)

    def p_processor_stmt(self, args):
        '''
             processor_stmt : task_expr ARE ASSIGNED TO PROCESSORS expr
                            | task_expr ARE ASSIGNED TO AN RANDOM PROCESSORS
        '''
        args[0] = self._wrapAST("processor_stmt", args, source_task=1)

    def p_reduce_stmt_1(self, args):
        '''
             reduce_stmt : task_expr REDUCES reduce_message_spec
                         | task_expr REDUCES reduce_message_spec TO reduce_message_spec
        '''
        sourceAST = self._make_source_task(args, 1)
        if len(args.slice) == 4:
            recv_reduce_msg_spec = copy.deepcopy(args[3])
            self._assign0state(args, ast=recv_reduce_msg_spec, kidofs=[3])
        else:
            recv_reduce_msg_spec = args[5]
        args[0] = self._str2ast("reduce_stmt", attr=["allreduce"],
                                kids=[sourceAST, args[3], recv_reduce_msg_spec])
        self._assign0state(args)

    def p_reduce_stmt_2(self, args):
        '''
             reduce_stmt : task_expr REDUCES reduce_message_spec TO task_expr
                         | task_expr REDUCES reduce_message_spec TO task_expr WHO RECEIVES THE RESULTS reduce_target_message_spec
        '''
        sourceAST = self._make_source_task(args, 1)
        targetAST = self._make_source_task(args, 5)    # Yes, this is correct.
        if len(args) == 6:
            recv_reduce_msg_spec = copy.deepcopy(args[3])
            self._assign0state(args, ast=recv_reduce_msg_spec, kidofs=[3])
        else:
            # Convert the reduce_target_message_spec to a reduce_message_spec.
            recv_reduce_msg_spec = args[10]
            for k in range(0, len(recv_reduce_msg_spec.kids)):
                if recv_reduce_msg_spec.kids[k].attr == "unspecified":
                    recv_reduce_msg_spec.kids[k] = copy.deepcopy(args[3].kids[k])
            if recv_reduce_msg_spec.attr == -1:
                recv_reduce_msg_spec.attr = args[3].attr
            recv_reduce_msg_spec.type = "reduce_message_spec"
        args[0] = self._str2ast("reduce_stmt", attr=[],
                                kids=[sourceAST, args[3], recv_reduce_msg_spec, targetAST])
        self._assign0state(args)


    #------------------------#
    # Relational expressions #
    #------------------------#

    def p_rel_expr(self, args):
        ' rel_expr : rel_disj_expr '
        args[0] = self._wrapAST("rel_expr", args)

    def p_rel_disj_expr_1(self, args):
        ' rel_disj_expr : rel_conj_expr '
        args[0] = self._wrapAST("rel_disj_expr", args)

    def p_rel_disj_expr_2(self, args):
        r' rel_disj_expr : rel_disj_expr logic_or rel_conj_expr '
        args[0] = self._wrapAST("rel_disj_expr", args,
                                attr=self._opname[args.slice[2].value])

    def p_rel_conj_expr_1(self, args):
        ' rel_conj_expr : rel_primary_expr '
        args[0] = self._wrapAST("rel_conj_expr", args)

    def p_rel_conj_expr_2(self, args):
        r' rel_conj_expr : rel_conj_expr logic_and rel_primary_expr '
        args[0] = self._wrapAST("rel_conj_expr", args,
                                attr=self._opname[args.slice[2].value])

    def p_rel_primary_expr(self, args):
        '''
             rel_primary_expr : eq_expr
                              | lparen rel_expr rparen
        '''
        args[0] = self._wrapAST("rel_primary_expr", args)

    def p_eq_expr_1(self, args):
        '''
             eq_expr : expr op_eq expr
                     | expr op_lt expr
                     | expr op_gt expr
                     | expr op_leq expr
                     | expr op_geq expr
                     | expr op_neq expr
                     | expr DIVIDES expr
        '''
        args[0] = self._wrapAST("eq_expr", args,
                                attr=self._opname[string.upper(args.slice[2].value)])

    def p_eq_expr_2(self, args):
        '''
             eq_expr : expr ARE EVEN
                     | expr ARE ODD
        '''
        lineno0, lineno1 = self._linespan(args)
        args[0] = self._str2ast("eq_expr",
                                attr="op_"+string.lower(args.slice[3].type),
                                left=args[1],
                                lineno0=lineno0, lineno1=lineno1)
        self._assign0state(args)

    def p_eq_expr_3(self, args):
        ' eq_expr : expr ARE IN lbracket expr comma expr rbracket '
        self.errmsg.warning('"%s %s [%s,%s]" is deprecated; please use "%s %s {%s,...,%s} instead' %
                            (args[2], args[3], args[5].printable, args[7].printable,
                             args[2], args[3], args[5].printable, args[7].printable))

        args[0] = self._wrapAST("eq_expr", args, attr="op_in_range")

    def p_eq_expr_4(self, args):
        ' eq_expr : expr ARE NOT IN lbracket expr comma expr rbracket '
        self.errmsg.warning('"%s %s %s [%s,%s]" is deprecated; please use "%s %s %s {%s,...,%s} instead' %
                            (args[2], args[3], args[4], args[6].printable, args[8].printable,
                             args[2], args[3], args[4], args[6].printable, args[8].printable))

        args[0] = self._wrapAST("eq_expr", args, attr="op_not_in_range")

    def p_eq_expr_5(self, args):
        ' eq_expr : expr ARE IN range_list '
        args[0] = self._wrapAST("eq_expr", args, attr="op_in_range_list")

    def p_eq_expr_6(self, args):
        ' eq_expr : expr ARE NOT IN range_list '
        args[0] = self._wrapAST("eq_expr", args, attr="op_not_in_range_list")


    #-----------------------#
    # Aggregate expressions #
    #-----------------------#

    def p_aggregate_expr_1(self, args):
        '''
             aggregate_expr : expr
                            | EACH expr
        '''
        args[0] = self._wrapAST("aggregate_expr", args, attr="no_aggregate")

    def p_aggregate_expr_2(self, args):
        ' aggregate_expr : THE expr '
        aggr_func_ast = self._str2ast("aggregate_func", attr="ONLY")
        self._assign0state(args, ast=aggr_func_ast, kidofs=[1])
        args[0] = self._str2ast("aggregate_expr", kids=[aggr_func_ast, args[2]])
        self._assign0state(args)

    def p_aggregate_expr_3(self, args):
        '''
             aggregate_expr : THE aggregate_func_list expr
                            | THE aggregate_func_list OF expr
                            | THE aggregate_func_list OF THE expr
        '''
        args[0] = self._wrapAST("aggregate_expr", args)

    def p_aggregate_expr_4(self, args):
        '''
             aggregate_expr : AN HISTOGRAM OF expr
                            | AN HISTOGRAM OF THE expr
        '''
        lineno0, lineno1 = self._linespan(args, last=len(args.slice)-2)
        funcAST = self._str2ast("aggregate_func", attr="HISTOGRAM",
                                lineno0=lineno0, lineno1=lineno1)
        args[0] = self._str2ast("aggregate_expr",
                                left=funcAST, right=args[len(args)-1])
        self._assign0state(args)


    #------------------------#
    # Arithmetic expressions #
    #------------------------#

    def p_expr(self, args):
        ' expr : ifelse_expr '
        args[0] = self._wrapAST("expr", args)

    def p_ifelse_expr_1(self, args):
        ' ifelse_expr : add_expr '
        args[0] = self._wrapAST("ifelse_expr", args)

    def p_ifelse_expr_2(self, args):
        ' ifelse_expr : add_expr IF rel_expr OTHERWISE ifelse_expr '
        args[0] = self._wrapAST("ifelse_expr", args)

    def p_add_expr_1(self, args):
        ' add_expr : mult_expr '
        args[0] = self._wrapAST("add_expr", args)

    def p_add_expr_2(self, args):
        '''
             add_expr : add_expr op_plus mult_expr
                      | add_expr op_minus mult_expr
                      | add_expr op_or mult_expr
                      | add_expr XOR mult_expr
        '''
        args[0] = self._wrapAST("add_expr", args,
                                attr=self._opname[string.upper(args.slice[2].value)])

    def p_mult_expr_1(self, args):
        ' mult_expr : unary_expr '
        args[0] = self._wrapAST("mult_expr", args)

    def p_mult_expr_2(self, args):
        '''
             mult_expr : mult_expr op_mult unary_expr
                       | mult_expr op_div unary_expr
                       | mult_expr MOD unary_expr
                       | mult_expr op_rshift unary_expr
                       | mult_expr op_lshift unary_expr
                       | mult_expr op_and unary_expr
        '''
        args[0] = self._wrapAST("mult_expr", args,
                                attr=self._opname[string.upper(args.slice[2].value)])

    def p_unary_expr_1(self, args):
        ' unary_expr : power_expr '
        args[0] = self._wrapAST("unary_expr", args)

    def p_unary_expr_2(self, args):
        ' unary_expr : unary_operator unary_expr '
        targetexpr = args[2]
        new_printable = None
        try:
            # Assume we have a number -- modify it in place.
            if args[1].attr == "op_pos":
                new_printable = targetexpr.printable
            elif args[1].attr == "op_neg":
                self._apply2attr(lambda n: -n, targetexpr)
                new_printable = "-" + targetexpr.printable
            elif args[1].attr == "op_not":
                self._apply2attr(lambda n: ~n, targetexpr)
            else:
                self.errmsg.error_internal('Unknown unary operator "%s"' % str(args[1].attr))
        except TypeError:
            # We have an expression -- wrap it with the unary operator.
            targetexpr = self._wrapAST("unary_expr", args, attr=args[1].attr, kidofs=[2])
        args[0] = targetexpr
        self._assign0state(args)
        if new_printable != None:
            args[0].printable = new_printable

    def p_unary_operator(self, args):
        '''
             unary_operator : op_plus
                            | op_minus
                            | NOT
        '''
        # Rename binary operators as unary.
        operator_name = self._opname["u" + string.upper(args.slice[1].value)]
        args[0] = self._wrapAST("unary_operator", args, attr=operator_name)

    def p_power_expr_1(self, args):
        ' power_expr : primary_expr '
        args[0] = self._wrapAST("power_expr", args)

    def p_power_expr_2(self, args):
        ' power_expr : primary_expr op_power unary_expr '
        args[0] = self._wrapAST("power_expr", args)

    def p_primary_expr_1(self, args):
        ' primary_expr : lparen expr rparen '
        args[0] = self._wrapAST("primary_expr", args)

    def p_primary_expr_2(self, args):
        ' primary_expr : func_name lparen expr_list rparen '
        lineno0, lineno1 = self._linespan(args)
        funcAST = self._str2ast("func_call", attr=string.upper(args[1].type),
                                left=args[3], lineno0=lineno0, lineno1=lineno1)
        funcAST.printable = args[1].printable
        args[0] = self._str2ast("primary_expr", left=funcAST)
        self._assign0state(args)

    def p_primary_expr_3(self, args):
        ' primary_expr : REAL lparen expr rparen '
        # Although it looks like a function, REAL is actually a special form.
        realAST = self._lextoken2ast(args.slice[1], left=args[3])
        self._assign0state(args, ast=realAST)
        args[0] = self._str2ast("primary_expr", left=realAST)
        self._assign0state(args)

    def p_primary_expr_4(self, args):
        ' primary_expr : ident '
        args[0] = self._wrapAST("primary_expr", args)

    def p_primary_expr_5(self, args):
        ' primary_expr : integer '
        integerAST = self._lextoken2ast(args.slice[1])
        self._assign0state(args, ast=integerAST)
        args[0] = self._str2ast("primary_expr", left=integerAST)
        self._assign0state(args)

    def p_primary_expr_6(self, args):
        ' primary_expr : MESH_NEIGHBOR lparen lparen dimension_list rparen comma expr comma lparen expr_list rparen rparen '
        lineno0, lineno1 = self._linespan(args)
        funcAST = self._str2ast("func_call", attr=string.upper(args[1]),
                                kids=[args[4], args[7], args[10]],
                                lineno0=lineno0, lineno1=lineno1)
        funcAST.printable = args[1]
        args[0] = self._str2ast("primary_expr", left=funcAST)
        self._assign0state(args)
        if args[4].attr != args[10].attr:
            self.errmsg.error_fatal("a MESH_NEIGHBOR's mesh and offset lists must have the same length",
                                    args[0].lineno0, args[0].lineno1)


    def p_primary_expr_7(self, args):
        '''
              primary_expr : MESH_COORDINATE lparen lparen dimension_list rparen comma expr comma expr rparen
                           | MESH_DISTANCE lparen lparen dimension_list rparen comma expr comma expr rparen
        '''
        lineno0, lineno1 = self._linespan(args)
        funcAST = self._str2ast("func_call", attr=string.upper(args[1]),
                                kids=[args[4], args[7], args[9]],
                                lineno0=lineno0, lineno1=lineno1)
        funcAST.printable = args[1]
        args[0] = self._str2ast("primary_expr", left=funcAST)
        self._assign0state(args)

    def p_primary_expr_8(self, args):
        ' primary_expr : MY TASKS '
        lineno0, lineno1 = self._linespan(args)
        mytaskAST = self._str2ast("my_task", lineno0=lineno0, lineno1=lineno1)
        mytaskAST.printable = args[1] + " " + args[2]
        args[0] = self._str2ast("primary_expr", left=mytaskAST)
        self._assign0state(args)

    def p_primary_expr_9(self, args):
        # FILE_DATA and STATIC_FILE_DATA are special because their
        # first, fourth, and fifth arguments are strings.
        '''
            primary_expr : FILE_DATA lparen string rparen
            primary_expr : FILE_DATA lparen string comma expr rparen
            primary_expr : FILE_DATA lparen string comma expr comma expr rparen
            primary_expr : FILE_DATA lparen string comma expr comma expr comma string rparen
            primary_expr : FILE_DATA lparen string comma expr comma expr comma string comma string rparen

            primary_expr : STATIC_FILE_DATA lparen string rparen
            primary_expr : STATIC_FILE_DATA lparen string comma expr rparen
            primary_expr : STATIC_FILE_DATA lparen string comma expr comma expr rparen
            primary_expr : STATIC_FILE_DATA lparen string comma expr comma expr comma string rparen
            primary_expr : STATIC_FILE_DATA lparen string comma expr comma expr comma string comma string rparen
        '''
        lineno0, lineno1 = self._linespan(args)
        children = []
        for i in range(3, len(args), 2):
            children.append(args[i])
        funcAST = self._str2ast("func_call", attr=string.upper(args[1]),
                                kids=children, lineno0=lineno0, lineno1=lineno1)
        funcAST.printable = args[1]
        args[0] = self._str2ast("primary_expr", left=funcAST)
        self._assign0state(args)


    #-------------------------#
    # Messaging-related rules #
    #-------------------------#

    def p_message_spec_1(self, args):
        ' message_spec : item_count unique item_size message_alignment MESSAGES touching_type tag buffer_number '
        is_misaligned = args[4].is_misaligned
        delattr(args[4], "is_misaligned")
        args[0] = self._wrapAST("message_spec", args, attr=is_misaligned)
        self._hoist_buffer_offset(args[0])

    def p_message_spec_2(self, args):
        ' message_spec : item_count unique message_alignment MESSAGES touching_type tag buffer_number '
        is_misaligned = args[3].is_misaligned
        delattr(args[3], "is_misaligned")
        itemsizeAST = self._str2ast("item_size")
        self._assign0state(args, ast=itemsizeAST, kidofs=[])
        args[0] = self._wrapAST("message_spec", args, attr=is_misaligned)
        args[0].kids.insert(2, itemsizeAST)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_message_spec_into(self, args):
        ' message_spec_into : item_count unique item_size message_alignment MESSAGES touching_type tag recv_buffer_number '
        is_misaligned = args[4].is_misaligned
        delattr(args[4], "is_misaligned")
        args[0] = self._wrapAST("message_spec", args, attr=is_misaligned)
        self._hoist_buffer_offset(args[0])

    def p_recv_message_spec_1(self, args):
        ' recv_message_spec : opt_async touching_type tag recv_buffer_number '
        # Fabricate any ASTs we weren't provided.
        opt_an = self._str2ast("opt_an")
        unique = self._str2ast("unique")
        message_alignment = self._str2ast("message_alignment")
        for ast in (opt_an, unique, message_alignment):
            ast.lineno0 = args[2].lineno0
            ast.lineno1 = args[2].lineno0
            ast.is_fabricated = 1
            ast.is_empty = 1

        # Treat all empty ASTs as fabricated.
        opt_async, touching_type, tag, buffer_number = args[1], args[2], args[3], args[4]
        kidlist = [opt_async, opt_an, unique, message_alignment, touching_type, tag, buffer_number]
        for kid in kidlist:
            kid.is_fabricated = getattr(kid, "is_fabricated", getattr(kid, "is_empty", 1))

        # Return an AST with attribute -1 (fabricated alignment).
        args[0] = self._str2ast("message_spec", kids=kidlist, attr=-1)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_recv_message_spec_2(self, args):
        ' recv_message_spec : opt_async AS opt_an unique message_alignment MESSAGES touching_type tag recv_buffer_number '
        kidlist = [args[1], args[3], args[4], args[5], args[7], args[8], args[9]]
        for kid in kidlist:
            kid.is_fabricated = kid.is_empty
        if args[5].is_fabricated:
            is_misaligned = -1
        else:
            is_misaligned = args[5].is_misaligned
            delattr(args[5], "is_misaligned")
        args[0] = self._str2ast("message_spec", kids=kidlist, attr=is_misaligned)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_reduce_message_spec_1(self, args):
        ' reduce_message_spec : item_count unique message_alignment data_type touching_type tag buffer_number '
        is_misaligned = args[3].is_misaligned
        delattr(args[3], "is_misaligned")
        args[0] = self._wrapAST("reduce_message_spec", args, attr=is_misaligned)
        self._hoist_buffer_offset(args[0])

    def p_reduce_message_spec_2(self, args):
        ' reduce_message_spec : item_count unique data_type touching_type tag buffer_number '
        message_alignment = self._str2ast("message_alignment", attr="unspecified",
                                          lineno=args.lineno(3))
        message_alignment.is_fabricated = 1
        kidlist = [args[1], args[2], message_alignment, args[3], args[4], args[5], args[6]]
        args[0] = self._str2ast("reduce_message_spec", kids=kidlist, attr=0)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_reduce_target_message_spec_1(self, args):
        ' reduce_target_message_spec : touching_type tag recv_buffer_number '
        # Fabricate any ASTs we weren't provided.
        item_count = self._str2ast("an", attr="unspecified")
        unique = self._str2ast("unique", attr="unspecified")
        message_alignment = self._str2ast("message_alignment", attr="unspecified")
        data_type = self._str2ast("unknown", attr="unspecified")
        for ast in (item_count, unique, message_alignment, data_type):
            ast.lineno0 = args[1].lineno0
            ast.lineno1 = args[1].lineno0
            ast.is_fabricated = 1

        # Treat all empty ASTs as fabricated.
        touching_type, tag, buffer_number = args[1], args[2], args[3]
        kidlist = [item_count, unique, message_alignment, data_type, touching_type, tag, buffer_number]
        for kid in kidlist:
            kid.is_fabricated = getattr(kid, "is_fabricated", getattr(kid, "is_empty", 1))

        # Return an AST with attribute -1 (fabricated alignment).
        args[0] = self._str2ast("reduce_target_message_spec", kids=kidlist, attr=-1)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_reduce_target_message_spec_2(self, args):
        ' reduce_target_message_spec : AS item_count unique message_alignment data_type touching_type tag recv_buffer_number '
        kidlist = map(lambda a, args=args: args[a], range(2, 9))
        for kid in kidlist:
            kid.is_fabricated = kid.is_empty
        if args[4].is_fabricated:
            is_misaligned = -1
        else:
            is_misaligned = args[4].is_misaligned
            delattr(args[4], "is_misaligned")
        args[0] = self._str2ast("reduce_target_message_spec", kids=kidlist, attr=is_misaligned)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_reduce_target_message_spec_3(self, args):
        ' reduce_target_message_spec : AS item_count unique data_type touching_type tag recv_buffer_number '
        kidlist = map(lambda a, args=args: args[a], range(2, 8))
        for kid in kidlist:
            kid.is_fabricated = kid.is_empty
        message_alignment = self._str2ast("message_alignment", attr="unspecified",
                                          lineno=args[4].lineno0)
        message_alignment.is_fabricated = 1
        kidlist.insert(2, message_alignment)
        args[0] = self._str2ast("reduce_target_message_spec", kids=kidlist, attr=-1)
        self._assign0state(args)
        self._hoist_buffer_offset(args[0])

    def p_opt_an(self, args):
        '''
        opt_an :
               | AN
        '''
        args[0] = self._wrapAST("opt_an", args, attr=len(args.slice)-1)

    def p_opt_async(self, args):
        '''
        opt_async :
                  | ASYNCHRONOUSLY
                  | SYNCHRONOUSLY
        '''
        if len(args.slice) == 2 and args.slice[1].type == "ASYNCHRONOUSLY":
            attr = 1
        else:
            attr = 0
        args[0] = self._wrapAST("opt_async", args, attr=attr)

    def p_opt_unsusp(self, args):
        '''
        opt_unsusp :
                   | UNSUSPECTING
        '''
        args[0] = self._wrapAST("opt_unsusp", args, attr=len(args.slice)-1)

    def p_unique(self, args):
        '''
        unique :
               | UNIQUE
               | NONUNIQUE
        '''
        attr = int(len(args.slice) > 1 and args.slice[1].type == "UNIQUE")
        args[0] = self._wrapAST("unique", args, attr=attr)

    def p_tag(self, args):
        '''
        tag :
            | USING TAG expr
            | USING TAG string
        '''
        args[0] = self._wrapAST("tag", args)

    def p_buffer_offset(self, args):
        '''
        buffer_offset :
                      | expr data_multiplier INTO
        '''
        args[0] = self._wrapAST("buffer_offset", args)
        args[0].is_fabricated = 0

    def p_buffer_number(self, args):
        '''
        buffer_number :
                      | FROM buffer_offset THE DEFAULT BUFFERS
                      | FROM buffer_offset BUFFERS expr
        '''
        if len(args.slice) == 1:
            args[0] = self._wrapAST("buffer_number", args, attr="implicit")
        else:
            args[0] = self._wrapAST("buffer_number", args, attr=string.lower(args.slice[1].type))
        if args[0].kids == []:
            buffer_offset = self._str2ast("buffer_offset", lineno=args[0].lineno0)
            buffer_offset.is_fabricated = 1
            args[0].kids.insert(0, buffer_offset)

    def p_recv_buffer_number(self, args):
        '''
        recv_buffer_number :
                           | INTO buffer_offset THE DEFAULT BUFFERS
                           | INTO buffer_offset BUFFERS expr
        '''
        if len(args.slice) == 1:
            args[0] = self._wrapAST("recv_buffer_number", args, attr="implicit")
        else:
            args[0] = self._wrapAST("recv_buffer_number", args, attr=string.lower(args.slice[1].type))
        if args[0].kids == []:
            buffer_offset = self._str2ast("buffer_offset", lineno=args[0].lineno0)
            buffer_offset.is_fabricated = 1
            args[0].kids.insert(0, buffer_offset)

    def p_message_alignment_1(self, args):
        '''
        message_alignment :
                          | UNALIGNED
                          | byte_count ALIGNED
                          | data_type ALIGNED
        '''
        args[0] = self._wrapAST("message_alignment", args)
        args[0].is_misaligned = 0

    def p_message_alignment_2(self, args):
        '''
        message_alignment : data_type MISALIGNED
                          | byte_count MISALIGNED
        '''
        args[0] = self._wrapAST("message_alignment", args)
        args[0].is_misaligned = 1

    def p_touching_type(self, args):
        '''
        touching_type :
                      | WITH DATA TOUCHING
                      | WITHOUT DATA TOUCHING
                      | WITH VERIFICATION
                      | WITHOUT VERIFICATION
        '''
        if len(args.slice) == 1:
            operation = "no_touching"
            attr = "implicit"
        else:
            attr = string.lower(args.slice[-1].type)
            if args.slice[1].type == "WITH":
                operation = attr
            else:
                operation = "no_touching"
        lineno0, lineno1 = args.linespan(0)
        touchAST = self._str2ast(operation, attr=attr,
                                 lineno0=lineno0, lineno1=lineno1)
        self._assign0state(args, ast=touchAST)
        args[0] = self._str2ast("touching_type", left=touchAST,
                                lineno0=lineno1, lineno1=lineno1)
        self._assign0state(args)


    #--------------#
    # Helper rules #
    #--------------#

    def p_task_expr_1(self, args):
        ' task_expr : TASKS restricted_ident '
        args[0] = self._wrapAST("task_expr", args, attr="such_that")

    def p_task_expr_2(self, args):
        ' task_expr : TASKS expr '
        args[0] = self._wrapAST("task_expr", args, attr="expr")

    def p_task_expr_3(self, args):
        '''
        task_expr : ALL TASKS
                  | ALL TASKS ident
        '''
        args[0] = self._wrapAST("task_expr", args, attr="task_all")

    def p_task_expr_4(self, args):
        ' task_expr : ALL OTHER TASKS '
        args[0] = self._wrapAST("task_expr", args, attr="all_others")

    def p_task_expr_5(self, args):
        ' task_expr : TASKS GROUP ident '
        args[0] = self._wrapAST("task_expr", args, attr="let_task")

    def p_task_expr_6(self, args):
        ' task_expr : TASKS range_list '
        # "TASKS <range_list>" is syntactic sugar for "TASKS a SUCH
        # THAT a IS IN <range_list>".
        range_list = args[2]
        ident_A = self._str2ast("ident", attr="a",
                                lineno0=range_list.lineno0,
                                lineno1=range_list.lineno1)
        expr_A = copy.copy(ident_A)
        for exprtype in ["primary_expr", "power_expr", "unary_expr",
                         "mult_expr", "add_expr", "ifelse_expr", "expr"]:
            expr_A = self._str2ast(exprtype,
                                   lineno0=range_list.lineno0,
                                   lineno1=range_list.lineno1,
                                   left=expr_A)
        eq_expr = self._str2ast("eq_expr", attr="op_in_range_list",
                                lineno0=range_list.lineno0,
                                lineno1=range_list.lineno1,
                                left=expr_A, right=range_list)
        rel_expr = eq_expr
        for exprtype in ["rel_primary_expr", "rel_conj_expr", "rel_disj_expr", "rel_expr"]:
            rel_expr = self._str2ast(exprtype,
                                     lineno0=range_list.lineno0,
                                     lineno1=range_list.lineno1,
                                     left=rel_expr)
        restricted_ident = self._str2ast("restricted_ident",
                                         lineno0=range_list.lineno0,
                                         lineno1=range_list.lineno1,
                                         left=ident_A, right=rel_expr)
        args[0] = self._str2ast("task_expr", attr="such_that",
                                lineno0=range_list.lineno0,
                                lineno1=range_list.lineno1,
                                printable=args[2].printable,
                                left=restricted_ident)

    def p_restricted_ident(self, args):
        ' restricted_ident : ident SUCH THAT rel_expr '
        args[0] = self._wrapAST("restricted_ident", args)

    def p_range_list_1(self, args):
        ' range_list : range '
        args[0] = self._wrapAST("range_list", args, attr=1L)

    def p_range_list_2(self, args):
        ' range_list : range comma range_list '
        numentries = args[3].attr + 1L
        args[3].attr = None
        args[0] = self._str2ast("range_list", attr=numentries,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_range(self, args):
        '''
        range : lbrace expr_list rbrace
              | lbrace expr_list comma ellipsis comma expr rbrace
              | lbrace expr list_comp_expr rbrace
        '''
        numargs = len(args.slice)
        if numargs == 4:
            attr = None
        elif numargs == 5:
            attr = "list_comp"
        else:
            attr = "ellipsis"
        args[0] = self._wrapAST("range", args, attr=attr)

    def p_where_expr(self, args):
        ' where_expr : WHERE rel_expr '
        args[0] = self._wrapAST("where_expr", args)

    def p_list_comp_expr(self, args):
        '''
        list_comp_expr : FOR EACH ident IN range_list
                       | FOR EACH ident IN range_list where_expr
                       | FOR EACH ident IN range_list list_comp_expr
        '''
        args[0] = self._wrapAST("for_each_expr", args)

    def p_expr_list_1(self, args):
        ' expr_list : expr '
        args[0] = self._wrapAST("expr_list", args, attr=1L)

    def p_expr_list_2(self, args):
        ' expr_list : expr_list comma expr '
        numentries = args[1].attr + 1L
        args[1].attr = None
        args[0] = self._str2ast("expr_list", attr=numentries,
                                kids=args[1].kids + [args[3]])
        self._assign0state(args)

    def p_time_unit(self, args):
        '''
        time_unit : MICROSECONDS
                  | MILLISECONDS
                  | SECONDS
                  | MINUTES
                  | HOURS
                  | DAYS
        '''
        args[0] = self._str2ast("time_unit", attr=string.lower(args.slice[1].type))
        self._assign0state(args)

    def p_item_count_1(self, args):
        ' item_count : AN '
        anAST = self._str2ast("an", lineno=args.lineno(1))
        self._assign0state(args, ast=anAST)
        args[0] = self._str2ast("item_count", left=anAST)
        self._assign0state(args)

    def p_item_count_2(self, args):
        ' item_count : expr '
        args[0] = self._wrapAST("item_count", args)

    def p_item_size(self, args):
        '''
        item_size :
                  | expr data_multiplier
                  | data_type SIZED
        '''
        args[0] = self._wrapAST("item_size", args)

    def p_data_multiplier(self, args):
        '''
        data_multiplier : BITS
                        | BYTES
                        | KILOBYTE
                        | MEGABYTE
                        | GIGABYTE
                        | HALFWORDS
                        | WORDS
                        | INTEGERS
                        | DOUBLEWORDS
                        | QUADWORDS
                        | PAGES
        '''
        args[0] = self._wrapAST("data_multiplier", args, attr=string.lower(args.slice[1].type))

    def p_data_type(self, args):
        '''
        data_type : BYTES
                  | HALFWORDS
                  | WORDS
                  | INTEGERS
                  | DOUBLEWORDS
                  | QUADWORDS
                  | PAGES
        '''
        args[0] = self._wrapAST("data_type", args, attr=string.lower(args.slice[1].type))

    def p_byte_count(self, args):
        ' byte_count : expr data_multiplier '
        args[0] = self._wrapAST("byte_count", args)

    def p_aggregate_func_list_1(self, args):
        ' aggregate_func_list : aggregate_func '
        args[0] = self._wrapAST("aggregate_func_list", args, attr=1L)

    def p_aggregate_func_list_2(self, args):
        '''
            aggregate_func_list : aggregate_func AND aggregate_func_list
            aggregate_func_list : aggregate_func AND THE aggregate_func_list
        '''
        lastarg = len(args) - 1
        numentries = args[lastarg].attr + 1L
        args[lastarg].attr = None
        args[0] = self._str2ast("aggregate_func_list", attr=numentries,
                                kids=[args[1]] + args[lastarg].kids)
        self._assign0state(args)

    def p_aggregate_func(self, args):
        '''
        aggregate_func : MEAN
                       | ARITHMETIC MEAN
                       | HARMONIC MEAN
                       | GEOMETRIC MEAN
                       | MEDIAN
                       | STANDARD DEVIATION
                       | MEDIAN ABSOLUTE DEVIATION
                       | VARIANCE
                       | SUM
                       | MINIMUM
                       | MAXIMUM
                       | FINAL
                       | expr PERCENTILE
        '''
        if len(args) == 3 and string.lower(args[2]) == "percentile":
            args[0] = self._str2ast("aggregate_func", attr="percentile", left=args[1])
        else:
          funcname = string.lower(args[1])
          if funcname == "standard":
              funcname = "stdev"
          elif funcname == "harmonic":
              funcname = "harmonic_mean"
          elif funcname == "geometric":
              funcname = "geometric_mean"
          elif funcname == "arithmetic":
              funcname = "mean"
          elif funcname == "median" and len(args) >= 3 and string.lower(args[2]) == "absolute":
              funcname = "mad"
          args[0] = self._str2ast("aggregate_func", attr=funcname)
        self._assign0state(args)

    def p_func_name(self, args):
        '''
        func_name : ABS
                  | BITS
                  | CBRT
                  | CEILING
                  | FACTOR10
                  | FLOOR
                  | KNOMIAL_CHILD
                  | KNOMIAL_CHILDREN
                  | KNOMIAL_PARENT
                  | LOG10
                  | MAX
                  | MIN
                  | PROCESSOR_OF
                  | RANDOM_GAUSSIAN
                  | RANDOM_PARETO
                  | RANDOM_POISSON
                  | RANDOM_UNIFORM
                  | ROOT
                  | ROUND
                  | SQRT
                  | TASK_OF
                  | TREE_CHILD
                  | TREE_PARENT
        '''
        args[0] = self._lextoken2ast(args.slice[1])

    def p_dimension(self, args):
        '''
        dimension : expr
                  | expr star
        '''
        attr = len(args.slice) == 3
        args[0] = self._wrapAST("dimension", args, attr=attr, kidofs=[1])

    def p_dimension_list_1(self, args):
        ' dimension_list : dimension '
        args[0] = self._wrapAST("dimension_list", args, attr=1L)

    def p_dimension_list_2(self, args):
        ' dimension_list : dimension comma dimension_list '
        numentries = args[3].attr + 1L
        args[3].attr = None
        args[0] = self._str2ast("dimension_list", attr=numentries,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_log_expr_list_1(self, args):
        ' log_expr_list : log_expr_list_elt '
        args[0] = self._wrapAST("log_expr_list", args, attr=1L)

    def p_log_expr_list_2(self, args):
        ' log_expr_list : log_expr_list AND log_expr_list_elt '
        numentries = args[1].attr + 1L
        args[1].attr = None
        args[0] = self._str2ast("log_expr_list", attr=numentries,
                                kids=args[1].kids + [args[3]])
        self._assign0state(args)

    def p_log_expr_list_elt(self, args):
        ' log_expr_list_elt : aggregate_expr AS string_or_log_comment '
        args[0] = self._wrapAST("log_expr_list_elt", args)

    def p_let_binding_1(self, args):
        ' let_binding : ident BE expr '
        args[0] = self._wrapAST("let_binding", args)

    def p_let_binding_2(self, args):
        '''
        let_binding : ident BE AN RANDOM TASKS
                    | ident BE AN RANDOM TASKS OTHER THAN expr
                    | ident BE AN RANDOM TASKS LESS THAN expr
                    | ident BE AN RANDOM TASKS GREATER THAN expr
                    | ident BE AN RANDOM TASKS IN lbracket expr comma expr rbracket
                    | ident BE AN RANDOM TASKS LESS THAN expr BUT NOT expr
                    | ident BE AN RANDOM TASKS GREATER THAN expr BUT NOT expr
                    | ident BE AN RANDOM TASKS IN lbracket expr comma expr rbracket BUT NOT expr
        '''
        # Construct a list of children and an attribute string
        # consisting of a sequence of the following letters, each
        # corresponding to one child (except the first, which is
        # always the identifier name).
        #
        #   l: loose lower bound (must add 1)
        #   L: tight lower bound
        #   u: loose upper bound (must subtract 1)
        #   U: tight upper bound
        #   E: exception
        kidlist = [args[1]]
        nodeattrs = ""
        nextarg = 6
        if len(args.slice) == 6:
            pass
        else:
            word2argsattrsnext = {
                "OTHER"   : ([8],     "E", 9),
                "LESS"    : ([8],     "u", 9),
                "GREATER" : ([8],     "l", 9),
                "IN"      : ([8, 10], "LU", 12)}
            try:
                argnums, attrs, nextarg = word2argsattrsnext[args.slice[6].type]
            except KeyError:
                self.errmsg.error_internal('Unexpected keyword "%s" after "%s %s %s"' %
                                           (args[6], args[3], args[4], args[5]))
            kidlist.extend(map(lambda n, self=self, args=args: self._wrapAST("expr", args, kidofs=[n], assign0state=0), argnums))
            nodeattrs = nodeattrs + attrs
        if len(args.slice) > nextarg:
            # We have a "BUT NOT" clause.
            kidlist.append(self._wrapAST("expr", args, kidofs=[nextarg+2]))
            nodeattrs = nodeattrs + "E"
        args[0] = self._str2ast("let_binding", attr=nodeattrs, kids=kidlist)
        self._assign0state(args)

    def p_let_binding_3(self, args):
        ' let_binding : ident BE task_expr '
        args[1].attr = "GROUP " + args[1].attr   # Use a different namespace.
        args[0] = self._wrapAST("let_binding", args)

    def p_let_binding_list_1(self, args):
        ' let_binding_list : let_binding '
        args[0] = self._wrapAST("let_binding_list", args, attr=1L)

    def p_let_binding_list_2(self, args):
        ' let_binding_list : let_binding AND let_binding_list '
        numentries = args[3].attr + 1L
        args[3].attr = None
        args[0] = self._str2ast("let_binding_list", attr=numentries,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_string_or_log_comment_1(self, args):
        ' string_or_log_comment : string '
        args[0] = self._wrapAST("string_or_log_comment", args, attr="string")

    def p_string_or_log_comment_2(self, args):
        ' string_or_log_comment : THE VALUE OF string '
        args[0] = self._wrapAST("string_or_log_comment", args, attr="value_of")

    def p_string_or_expr_list_1(self, args):
        ' string_or_expr_list : string_or_log_comment '
        args[0] = self._wrapAST("string_or_expr_list", args, attr=["string"])

    def p_string_or_expr_list_2(self, args):
        ' string_or_expr_list : expr '
        args[0] = self._wrapAST("string_or_expr_list", args, attr=["expr"])

    def p_string_or_expr_list_3(self, args):
        ' string_or_expr_list : string_or_log_comment AND string_or_expr_list '
        typelist = args[3].attr
        args[3].attr = None
        args[0] = self._str2ast("string_or_expr_list",
                                attr=["string"] + typelist,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_string_or_expr_list_4(self, args):
        ' string_or_expr_list : expr AND string_or_expr_list '
        typelist = args[3].attr
        args[3].attr = None
        args[0] = self._str2ast("string_or_expr_list",
                                attr=["expr"] + typelist,
                                kids=[args[1]] + args[3].kids)
        self._assign0state(args)

    def p_stride(self, args):
        '''
        stride :
               | WITH RANDOM STRIDE
               | WITH STRIDE expr data_type
        '''
        if len(args.slice) == 1:
            attr = "default"
        elif len(args) == 4:
            attr = "random"
        else:
            attr = "specified"
        args[0] = self._wrapAST("stride", args, attr=attr)

    def p_touch_repeat_count(self, args):
        '''
        touch_repeat_count :
                           | expr TIMES
        '''
        args[0] = self._wrapAST("touch_repeat_count", args)

    def p_ident(self, args):
        ' ident : ident_token '
        args[0] = self._lextoken2ast(args.slice[1])
        args[0].type = "ident"
        self._assign0state(args)

    def p_string(self, args):
        ' string : string_token '
        args[0] = self._lextoken2ast(args.slice[1])
        args[0].type = "string"
        args[0].attr = args[0].attr[1:-1]
        self._assign0state(args)


# If the parser is run as a standalone program, enable it to output
# the language version, dump a human-readable version of the SLR parse
# table, or compile the grammar into a machine-readable parse table.
if __name__ == '__main__':
    import getopt
    shortlongopts = [("V",  "version"),
                     ("d:", "debug-file="),
                     ("g",  "dump-grammar"),
                     ("c",  "compile")]
    shortopts = string.join(map(lambda sl: sl[0], shortlongopts), "")
    longopts = map(lambda sl: sl[1], shortlongopts)
    try:
        optlist, extra_args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError, message:
        errmsg = NCPTL_Error(sys.argv[0])
        errmsg.error_fatal(string.capitalize(str(message)))
    for opt, arg in optlist:
        if opt in ["-V", "--version"]:
            print NCPTL_Parser.language_version
        elif opt in ["-d", "--debug-file"]:
            yacc.yacc(module=NCPTL_Parser(NCPTL_Lexer()), start="program",
                      write_tables=0, debugfile=arg)
        elif opt in ["-c", "--compile"]:
            yacc.yacc(module=NCPTL_Parser(NCPTL_Lexer()), start="program",
                      write_tables=1, tabmodule=_tabmodule, debug=0)
        elif opt in ["-g", "--dump-grammar"]:
            parser = NCPTL_Parser(NCPTL_Lexer())
            parser._dump_grammar()
