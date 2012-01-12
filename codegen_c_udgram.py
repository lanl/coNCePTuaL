#! /usr/bin/env python

########################################################################
#
# Code generation module for the coNCePTuaL language:
# C + Unix-domain (i.e., local) sockets
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

import codegen_c_generic
from ncptl_config import ncptl_config

class NCPTL_CodeGen(codegen_c_generic.NCPTL_CodeGen):

    def __init__(self, options=None):
        "Initialize the C + Unix sockets code generation module."
        codegen_c_generic.NCPTL_CodeGen.__init__(self, options)
        self.backend_name = "c_udgram"
        self.backend_desc = "C + Unix-domain datagram sockets"

        # Add a command-line option to the generated code to enable a
        # user to specify the number of tasks.
        self.base_global_parameters.append(("NCPTL_TYPE_INT",
                                            "var_num_tasks",
                                            "tasks",
                                            "T",
                                            "Number of tasks to use",
                                            "1"))

        # We don't have our own command-line options but we handle
        # --help, nevertheless.
        for arg in range(0, len(options)):
            if options[arg] == "--help":
                # Output a help message.
                self.show_help()
                raise SystemExit, 0


    # ---------------------------- #
    # Backend-specific helper code #
    # ---------------------------- #

    def code_reject_nonzero_tag(self, struct, statement):
        "Check for a nonzero tag and abort if one is found."
        return ["if (%s.tag != 0%s)" % (struct, self.ncptl_int_suffix),
                'ncptl_fatal ("The %s backend does not support nonzero tags in %s statements");' % (self.backend_name, statement)]


    # ----------- #
    # Header code #
    # ----------- #

    def code_specify_include_files_POST(self, localvars):
        "Specify extra header files needed by the c_udgram backend."
        includefiles = [
            "#include <errno.h>",
            "#include <signal.h>",
            "#include <sys/socket.h>",
            "#include <sys/un.h>",
            "#include <sys/ioctl.h>",
            "#include <sys/wait.h>"]
        if ncptl_config.has_key("HAVE_SYS_SELECT_H"):
            self.push("#include <sys/select.h>", includefiles)
        return includefiles

    def code_define_macros_POST(self, localvars):
        "Define some macros to simplify the generated C code."

        # Define a filename template to use for our sockets.
        definition = [
            "/* Define a filename template for this program's sockets. */",
            '#define SOCKET_TEMPLATE "c_udgram_XXXXXX"',
            ""]

        # Define a CONC_SYSTEM_ERROR macro that invokes ncptl_fatal()
        # with a description or the number of the most recent system
        # error.  We use strerror() if configure detected it.
        # Otherwise, we use sys_errlist[] if configure detected that.
        # Otherwise, we simply use errno.
        definition.extend([
            '/* Define a wrapper for ncptl_fatal() after a system call failure. */',
            '#define CONC_SYSTEM_ERROR(MSG)                                     \\',
            '  do {                                                             \\'])
        if ncptl_config.has_key("HAVE_STRERROR"):
            definition.extend([
                '    if (strerror(errno))                                           \\',
                '      ncptl_fatal (MSG " (%s, errno=%d)", strerror(errno), errno); \\',
                '    else                                                           \\',
                '      ncptl_fatal (MSG " (errno=%d)", errno);                      \\'])
        elif ncptl_config.has_key("HAVE_DECL_SYS_ERRLIST"):
            definition.extend([
                '    if (errno < sys_nerr)                                          \\',
                '      ncptl_fatal (MSG " (%s)", sys_errlist[errno]);               \\',
                '    else                                                           \\',
                '      ncptl_fatal (MSG " (errno=%d)", errno);                      \\'])
        else:
            definition.extend([
                '    ncptl_fatal (MSG " (errno=%d)", errno);                        \\'])
        definition.extend([
            '  }                                                                \\',
            '  while (0)',
            ''])

        # Define a CONC_SET_BLOCKING macro that sets a socket to
        # either blocking or nonblocking, as desired.
        definition.extend([
            "/* Define a macro that sets or resets a socket's blocking state. */",
            '#define CONC_SET_BLOCKING(CSTATE, PEER, BLOCKING)                         \\',
            '  do {                                                                    \\',
            '    int nonblocking = 1 - (BLOCKING);                                     \\',
            '    if (ioctl ((CSTATE)->channels[PEER], FIONBIO, &nonblocking) == -1)    \\',
            '      CONC_SYSTEM_ERROR ("Failed to toggle a socket\'s blocking state");  \\',
            '  }                                                                       \\',
            '  while (0)'])
        return definition


    def code_declare_datatypes_POST(self, localvars):
        "Declare additional types needed by the c_udgram backend."
        newtypes = []
        self.pushmany([
            "/* Declare a type that encapsulates much of the communication state. */",
            "typedef struct {"],
                      stack=newtypes)
        self.code_declare_var(type="int *", name="channels",
                              comment="Socket connections to each other task",
                              stack=newtypes)
        self.code_declare_var(type="NCPTL_QUEUE **", name="blockedsendQ",
                              comment="Queue of events corresponding to blocked sends to each destination",
                              stack=newtypes)
        self.code_declare_var(type="NCPTL_QUEUE **", name="blockedrecvQ",
                              comment="Queue of events corresponding to blocked receives from each source",
                              stack=newtypes)
        self.code_declare_var(type="int", name="sendsblocked",
                              comment="0=all blockedsendQ[] are empty; 1=nonempty",
                              stack=newtypes)
        self.code_declare_var(type="int", name="recvsblocked",
                              comment="0=all blockedrecvQ[] are empty; 1=nonempty",
                              stack=newtypes)
        self.pushmany([
            "} COMMSTATE;",
            "",
            "/* Create symbolic names for each set of communication state we plan to use. */",
            "typedef enum {",
            "COMMSTATE_PT2PT,   /* State for point-to-point communication */",
            "COMMSTATE_COLL,    /* State for collective communication */",
            "NUMCHANNELSETS     /* Sentinel describing the number of entries in COMMSTATE_TYPES */",
            "} COMMSTATE_TYPES;"],
                      newtypes)
        return newtypes

    def code_declare_globals_EXTRA(self, localvars):
        "Declare additional C global variables needed by the c_udgram backend."
        newvars = []
        self.code_declare_var(type="COMMSTATE", name="commstate",
                              arraysize="NUMCHANNELSETS",
                              comment="Communication state for multiple independent channels",
                              stack=newvars)
        self.code_declare_var(type="int", name="abnormal_exit", rhs="1",
                              comment="1=exit handler invoked after an abnormal exit; 0=invoked after a normal one",
                              stack=newvars)
        self.code_declare_var(name="maxpacketlen",
                              comment="Maximum message length that can be transmitted whole",
                              stack=newvars)
        self.code_declare_var(type="NCPTL_QUEUE *", name="alltasksQ",
                              comment="List of 0, ..., var_num_tasks-1 for all-task synchronization",
                              stack=newvars)

        # Make all declarations static.
        static_newvars = []
        for var in newvars:
            static_newvars.append("static " + var)
        return static_newvars

    def code_def_init_decls_POST(self, localvars):
        """
           Declare C variables needed by code_define_functions_INIT_COMM_3,
           code_def_init_msg_mem_PRE, and code_def_init_misc_EXTRA.
        """
        newvars = []
        self.code_declare_var(type="int", name="cset",
                              comment="Index into commstate[]",
                              stack=newvars)
        self.code_declare_var(name="taskID", comment="Loop over all task IDs",
                              stack=newvars)
        self.code_declare_var(type="struct sockaddr_un ***", name="socketinfo",
                              comment="Socket information (e.g., filename) for every socket in channels[][][]",
                              stack=newvars)
        self.code_declare_var(type="char", name="maxpacketlen_str",
                              arraysize="50", comment="String equivalent of maxpacketlen",
                              stack=newvars)
        return newvars


    # --------------------------- #
    # Helper-function definitions #
    # --------------------------- #

    def code_define_functions_PRE(self, localvars):
        "Define some point-to-point and collective communication functions."
        msgfuncs = []
        uses_send   = self.events_used.has_key("EV_SEND")
        uses_asend  = self.events_used.has_key("EV_ASEND")
        uses_recv   = self.events_used.has_key("EV_RECV")
        uses_arecv  = self.events_used.has_key("EV_ARECV")
        uses_sync   = self.events_used.has_key("EV_SYNC")
        uses_mcast  = self.events_used.has_key("EV_MCAST")
        uses_wait   = self.events_used.has_key("EV_WAIT")
        uses_etime  = self.events_used.has_key("EV_ETIME")
        uses_reduce = self.events_used.has_key("EV_REDUCE")

        # State all function dependencies.
        uses_sync = 1        # Currently required by conc_finalize().
        if uses_etime:
            uses_send = 1
            uses_recv = 1
        if uses_sync or uses_mcast:
            uses_asend = 1
            uses_recv = 1
            uses_wait = 1
        if uses_reduce:
            uses_send = 1
            uses_arecv = 1
            uses_wait = 1

        # Define a wrapper for send() with automatic error checking. */
        self.pushmany([
            "/* Attempt to send data.  Abort on error.  Return 1 on success,",
            " * 0 if the send blocked. */",
            "static inline int conc_send_packet (COMMSTATE *cstate, int dest, void *buffer, int packetsize)",
            "{"],
                      stack=msgfuncs)
        self.code_declare_var(type="int", name="bytessent",
                              comment="Number of bytes actually sent",
                              stack=msgfuncs)
        self.pushmany([
            "do",
            "bytessent = send (cstate->channels[dest], buffer, (size_t) packetsize, 0);",
            "while (bytessent == -1 && errno == EINTR);",
            "if (bytessent == -1)",
            "if (errno == EAGAIN)",
            "return 0;             /* send() blocked. */",
            "else",
            'CONC_SYSTEM_ERROR ("Failed to send a message");',
            "else",
            " /* send() did not block. */",
            "if (bytessent != packetsize)",
            'ncptl_fatal ("Expected to send %d bytes but actually sent %d bytes",',
            "packetsize, bytessent);",
            "return 1;",
            "}",
            ""],
                      stack=msgfuncs)

        # Define a wrapper for recv() with automatic error checking.
        self.pushmany([
            "/* Attempt to send data.  Abort on error.  Return 1 on success,",
            " * 0 if the send blocked. */",
            "static inline int conc_receive_packet (COMMSTATE *cstate, int source, void *buffer, int packetsize)",
            "{"],
                      stack=msgfuncs)
        self.code_declare_var(type="int", name="bytesreceived",
                              comment="Number of bytes actually received",
                              stack=msgfuncs)
        self.pushmany([
            "do",
            "bytesreceived = recv (cstate->channels[source],",
            "buffer, packetsize, MSG_WAITALL|MSG_TRUNC);",
            "while (bytesreceived == -1 && errno == EINTR);",
            "if (bytesreceived == -1)",
            "if (errno == EAGAIN)",
            "return 0;             /* recv() blocked. */",
            "else",
            'CONC_SYSTEM_ERROR ("Failed to receive a message");',
            "else",
            " /* recv() did not block. */",
            "if (bytesreceived != packetsize)",
            'ncptl_fatal ("Expected to receive %d bytes but actually received %d bytes",',
            "packetsize, bytesreceived);",
            "return 1;",
            "}",
            ""],
                      stack=msgfuncs)

        # Define a function that determines the maximum socket size.
        self.pushmany([
            "/* Binary search for the largest valid packet length. */",
            "static ncptl_int conc_find_max_packet_len (COMMSTATE *cstate)",
            "{",],
                      stack=msgfuncs)
        self.code_declare_var(type="int", name="maxsize",
                              comment="Maximum valid message size",
                              stack=msgfuncs)
        self.code_declare_var(type="int", name="delta",
                              comment="Change in message size to try next",
                              stack=msgfuncs)
        self.code_declare_var(type="socklen_t", name="intsize", rhs="sizeof(int)",
                              comment="Number of bytes in maxsize",
                              stack=msgfuncs)
        self.code_declare_var(type="char *", name="msgbuffer",
                              comment="Buffer used for sending and receiving",
                              stack=msgfuncs)
        self.code_declare_var(type="int", name="bytessent",
                              comment="Number of bytes actually sent",
                              stack=msgfuncs)
        self.code_declare_var(type="int", name="bytesreceived",
                              comment="Number of bytes actually received",
                              stack=msgfuncs)
        self.pushmany([
            "CONC_SET_BLOCKING (cstate, physrank, 1);",
            "if (getsockopt (cstate->channels[physrank], SOL_SOCKET, SO_SNDBUF, &maxsize, &intsize) == -1 ||",
            "!maxsize)",
            'CONC_SYSTEM_ERROR ("Failed to get a socket parameter");',
            "msgbuffer = (char *) ncptl_malloc (maxsize, 0);",
            "",
            "for (delta=maxsize/2; delta; delta/=2) {",
            "do",
            "bytessent =",
            "send (cstate->channels[physrank], msgbuffer, (size_t) maxsize, 0);",
            "while (bytessent == -1 && errno == EINTR);",
            "if (bytessent != -1) {",
            "do",
            "bytesreceived = recv (cstate->channels[physrank], msgbuffer,",
            "(size_t) maxsize, MSG_WAITALL | MSG_TRUNC);",
            "while (bytesreceived == -1 && errno == EINTR);",
            "if (bytesreceived != (int) maxsize)",
            'ncptl_fatal ("Expected to receive %d bytes but actually received %d bytes",',
            "maxsize, bytesreceived);",
            "maxsize += delta;",
            "}",
            "else",
            "maxsize -= delta;",
            "}",
            "ncptl_free (msgbuffer);",
            "CONC_SET_BLOCKING (cstate, physrank, 0);",
            "return (maxsize/sizeof(ncptl_int))*sizeof(ncptl_int) - 1;",
            "}"],
                              stack=msgfuncs)

        # Define a wait-one function.
        if uses_wait:
            self.pushmany([
                " /* Wait until a specific send/receive request completes.",
                "  * ASSUMPTION: target_req has not yet completed. */",
                "static inline void conc_wait_one (COMMSTATE *cstate, void *target_req)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(type="struct timeval", name="polltime",
                                  comment="Time structure corresponding to a minimal poll time",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                " /* Alternately complete receives and sends until target_req",
                "  * is satisfied. */",
                "while (1) {"],
                          stack=msgfuncs)
            self.code_declare_var(name="task_ofs",
                                  comment="Offset from our task ID",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                " /* Process each task ID in turn, starting from our own. */",
                "for (task_ofs=0; task_ofs<var_num_tasks; task_ofs++) {"],
                          stack=msgfuncs)
            for type, name, rhs, comment in [
                ("ncptl_int", "taskID", "(physrank+task_ofs) % var_num_tasks", "Task ID to process"),
                ("ncptl_int", "pendingsends", "ncptl_queue_length (cstate->blockedsendQ[taskID])", "Number of blocked sends"),
                ("ncptl_int", "pendingrecvs", "ncptl_queue_length (cstate->blockedrecvQ[taskID])", "Number of blocked receives"),
                ("int", "making_progress", None, "1=a packet was sent/received; 0=we idled")]:
                self.code_declare_var(type=type, name=name, rhs=rhs,
                                      comment=comment, stack=msgfuncs)
            self.pushmany([
                "",
                " /* Keep sending from task taskID and/or receiving from task",
                "  * taskID until we can no longer do so. */",
                "making_progress = pendingrecvs || pendingsends;",
                "while (making_progress) {"],
                          stack=msgfuncs)
            for type, name, rhs, comment in [
                ("int", "recvfd", "0", "File descriptor for a receive channel"),
                ("int", "sendfd", "0", "File descriptor for a send channel"),
                ("fd_set", "firstrecv", None, "Set containing either recvfd or nothing"),
                ("fd_set", "firstsend", None, "Set containing either sendfd or nothing"),
                ("int", "last_fd", "-1", "1 + highest-numbered descriptor on which to select()"),
                ("CONC_RECV_EVENT *", "recvev", "NULL", "List of blockedrecvQ's contents"),
                ("CONC_SEND_EVENT *", "sendev", "NULL", "List of blockedsendQ's contents"),
                ("int", "recv_available", None, "1=recv() won't block; 0=it will"),
                ("int", "send_available", None, "1=send() won't block; 0=it will")]:
                self.code_declare_var(type=type, name=name, rhs=rhs,
                                      comment=comment, stack=msgfuncs)
            self.pushmany([
                "",
                "FD_ZERO (&firstrecv);",
                "if (pendingrecvs) {",
                "recvev = ncptl_queue_contents (cstate->blockedrecvQ[taskID], 0);",
                "recvfd = cstate->channels[recvev->source];",
                "FD_SET(recvfd, &firstrecv);",
                "last_fd = recvfd>last_fd ? recvfd : last_fd;",
                "}",
                "FD_ZERO (&firstsend);",
                "if (pendingsends) {",
                "sendev = ncptl_queue_contents (cstate->blockedsendQ[taskID], 0);",
                "sendfd = cstate->channels[sendev->dest];",
                "FD_SET(sendfd, &firstsend);",
                "last_fd = sendfd>last_fd ? sendfd : last_fd;",
                "}",
                "polltime.tv_sec = 0;",
                "polltime.tv_usec = 1;    /* Setting to 0 tends to hog the CPU. */",
                "select (last_fd+1, &firstrecv, &firstsend, NULL, &polltime);",
                "send_available = sendfd && FD_ISSET(sendfd, &firstsend);",
                "recv_available = recvfd && FD_ISSET(recvfd, &firstrecv);",
                "if (!send_available && !recv_available)",
                " /* Give up if we're blocked on both the send and receive sides. */",
                "break;",
                "making_progress = 0;    /* Assume no progress. */",
                "",
                " /* Process a pending receive, if any. */",
                "if (pendingrecvs && recv_available) {"],
                          stack=msgfuncs)
            self.code_declare_var(type="int", name="packetsize",
                                  rhs="(int) (recvev->size>maxpacketlen ? maxpacketlen : recvev->size)",
                                  comment="Number of bytes to receive per call",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                "if (conc_receive_packet (cstate, recvev->source, recvev->buffer, packetsize)) {",
                " /* The receive went through. */",
                "making_progress = 1;",
                "recvev->buffer = (void *) ((char *)recvev->buffer + packetsize);",
                "recvev->size -= packetsize;",
                "if (!recvev->size) {",
                " /* We received a complete message. */",
                "(void) ncptl_queue_pop (cstate->blockedrecvQ[taskID]);",
                "if (!--pendingrecvs)",
                "ncptl_queue_empty (cstate->blockedrecvQ[taskID]);",
                "if (recvev == target_req)",
                " /* We finished the one message we care about. */",
                "return;",
                "}",
                "}",
                "}",
                "",
                " /* Process a pending send, if any. */",
                "if (pendingsends && send_available) {",
                "int packetsize = (int) (sendev->size>maxpacketlen ? maxpacketlen : sendev->size);   /* Number of bytes to send per call */",
                "if (conc_send_packet (cstate, sendev->dest, sendev->buffer, packetsize)) {",
                " /* The send went through. */",
                "making_progress = 1;",
                "sendev->buffer = (void *) ((char *) sendev->buffer + packetsize);",
                "sendev->size -= packetsize;",
                "if (!sendev->size) {",
                " /* We sent a complete message. */",
                "(void) ncptl_queue_pop (cstate->blockedsendQ[taskID]);",
                "if (!--pendingsends)",
                "ncptl_queue_empty (cstate->blockedsendQ[taskID]);",
                "if (sendev == target_req)",
                " /* We finished the one message we care about. */",
                "return;",
                "}",
                "}",
                "}",
                "}",
                "}",
                "}",
                "}"],
                          stack=msgfuncs)

        # Define a wait-all function.
        if uses_wait:
            self.pushmany([
                "/* Wait until all of our blocked sends and receives complete. */",
                "static inline void conc_wait_all (COMMSTATE *cstate)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(name="taskID", comment="Loop over all task IDs",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                " /* Ensure we have something to do. */",
                "if (!cstate->sendsblocked && !cstate->recvsblocked)",
                "return;",
                "",
                " /* Await completion from each task in turn -- not very efficient",
                "  * but we expect var_num_tasks to be small. */",
                "for (taskID=0; taskID<var_num_tasks; taskID++) {"],
                          stack=msgfuncs)
            self.code_declare_var(name="pendingsends", comment="Number of blocked sends",
                                  stack=msgfuncs)
            self.code_declare_var(name="pendingrecvs", comment="Number of blocked receives",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                " /* Wait for the final send to complete. */",
                "pendingsends = ncptl_queue_length (cstate->blockedsendQ[taskID]);",
                "if (pendingsends) {"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_SEND_EVENT *", name="lastsend",
                                  comment="Task taskID's final pending send",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                "lastsend = (CONC_SEND_EVENT *) ncptl_queue_contents (cstate->blockedsendQ[taskID], 0);",
                "lastsend += pendingsends - 1;",
                "conc_wait_one (cstate, (void *) lastsend);",
                "}",
                "",
                " /* Wait for the final receive to complete. */",
                "pendingrecvs = ncptl_queue_length (cstate->blockedrecvQ[taskID]);",
                "if (pendingrecvs) {"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_RECV_EVENT *", name="lastrecv",
                                  comment="Task taskID's final pending receive",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                "lastrecv = (CONC_RECV_EVENT *) ncptl_queue_contents (cstate->blockedrecvQ[taskID], 0);",
                "lastrecv += pendingrecvs - 1;",
                "conc_wait_one (cstate, (void *) lastrecv);   /* Wait for the final receive */",
                "}",
                "}",
                "",
                " /* Enable send/receive functions to proceed. */",
                "cstate->sendsblocked = 0;",
                "cstate->recvsblocked = 0;",
                "}"],
                          stack=msgfuncs)

        # Define a synchronous send function.
        if uses_send:
            self.pushmany([
                "/* Enqueue a message on a given channel and block until it completes. */",
                "static inline void conc_send_msg (COMMSTATE *cstate, CONC_SEND_EVENT *sendev)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_SEND_EVENT *", name="sendev_copy",
                                  comment="Mutable copy of sendev",
                                  stack=msgfuncs)
            self.pushmany([
                "cstate->sendsblocked = 1;",
                "sendev_copy = (CONC_SEND_EVENT *) ncptl_queue_push (cstate->blockedsendQ[sendev->dest], (void *) sendev);",
                "sendev_copy->buffer = (void *) ((char *)sendev_copy->buffer + sendev_copy->bufferofs);",
                "conc_wait_one (cstate, sendev_copy);",
                "}"],
                          stack=msgfuncs)

        # Define a synchronous receive function.
        if uses_recv:
            self.pushmany([
                "/* Post a receive and block until it completes. */",
                "static inline void conc_recv_msg (COMMSTATE *cstate, CONC_RECV_EVENT *recvev)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_RECV_EVENT *", name="recvev_copy",
                                  comment="Mutable copy of recvev",
                                  stack=msgfuncs)
            self.pushmany([
                "cstate->recvsblocked = 1;",
                "recvev_copy = (CONC_RECV_EVENT *) ncptl_queue_push (cstate->blockedrecvQ[recvev->source], (void *) recvev);",
                "recvev_copy->buffer = (void *) ((char *)recvev_copy->buffer + recvev_copy->bufferofs);",
                "conc_wait_one (cstate, recvev_copy);",
                "}"],
                          stack=msgfuncs)

        # Define an asynchronous send function.
        if uses_asend:
            self.pushmany([
                "/* Enqueue a message on a given channel (nonblocking). */",
                "static inline void conc_asend_msg (COMMSTATE *cstate, CONC_SEND_EVENT *sendev)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_SEND_EVENT *", name="sendev_copy",
                                  comment="Mutable copy of sendev",
                                  stack=msgfuncs)
            self.pushmany([

                "cstate->sendsblocked = 1;",
                "sendev_copy = (CONC_SEND_EVENT *) ncptl_queue_push (cstate->blockedsendQ[sendev->dest], (void *) sendev);",
                "sendev_copy->buffer = (void *) ((char *)sendev_copy->buffer + sendev_copy->bufferofs);",
                "}"],
                          stack=msgfuncs)

        # Define an asynchronous receive function.
        if uses_arecv:
            self.pushmany([
                "/* Enqueue a receive request on a given channel (nonblocking). */",
                "static inline void conc_arecv_msg (COMMSTATE *cstate, CONC_RECV_EVENT *recvev)",
                "{"],
                          stack=msgfuncs)
            self.code_declare_var(type="CONC_RECV_EVENT *", name="recvev_copy",
                                  comment="Mutable copy of recvev",
                                  stack=msgfuncs)
            self.pushmany([
                "cstate->recvsblocked = 1;",
                "recvev_copy = (CONC_RECV_EVENT *) ncptl_queue_push (cstate->blockedrecvQ[recvev->source], (void *) recvev);",
                "recvev_copy->buffer = (void *) ((char *)recvev_copy->buffer + recvev_copy->bufferofs);",
                "}"],
                          stack=msgfuncs)

        # Define a synchronization function.
        if uses_sync:
            self.pushmany([
                "/* Barrier-synchronize a list of tasks using a butterfly pattern. */",
                "static inline void conc_synchronize (COMMSTATE *cstate, int *peerlist, ncptl_int maxrank, ncptl_int syncrank)",
                "{"],
                          stack=msgfuncs)
            for type, name, comment in [
                ("ncptl_int", "stage", "Current stage of the butterfly pattern"),
                ("CONC_SEND_EVENT", "sendev", "Send event to pass to conc_asend_msg()"),
                ("CONC_RECV_EVENT", "recvev", "Receive event to pass to conc_recv_msg()"),
                ("ncptl_int", "dummybuffer", "Dummy message buffer")]:
                self.code_declare_var(type=type, name=name, comment=comment,
                                      stack=msgfuncs)

            # For each peer with a Hamming distance of 1 from us,
            # perform a nonblocking send followed by a blocking
            # receive.
            self.pushmany([
                "",
                "memset ((void *)&sendev, 0, sizeof(CONC_SEND_EVENT));",
                "memset ((void *)&recvev, 0, sizeof(CONC_RECV_EVENT));",
                "for (stage=ncptl_func_bits(maxrank)-1; stage>=0; stage--) {"],
                      stack=msgfuncs)
            self.code_declare_var(name="peernum",
                                  rhs="syncrank ^ (1<<stage)",
                                  comment="Offset into peerlist[] of our current peer",
                                  stack=msgfuncs)
            self.pushmany([
                "if (peernum <= maxrank) {",
                "sendev.dest = peerlist[peernum];",
                "sendev.buffer = (void *) &dummybuffer;",
                "conc_asend_msg (cstate, &sendev);",
                "recvev.source = peerlist[peernum];",
                "recvev.buffer = (void *) &dummybuffer;",
                "conc_recv_msg (cstate, &recvev);",
                "conc_wait_all (cstate);",
                "}",
                "}",
                "}"],
                          stack=msgfuncs)

        # Define a multicast function.
        if uses_mcast:
            self.pushmany([
                    "/* Multicast data from a single source to a set of destinations. */",
                    "static void conc_multicast (COMMSTATE *cstate, CONC_MCAST_EVENT *mcast_ev)",
                    "{"],
                          stack=msgfuncs)
            self.code_declare_var(name="mcastrank",
                                  rhs="mcast_ev->mcastrank",
                                  comment="This task's rank in the multicast",
                                  stack=msgfuncs)
            self.code_declare_var(type="int *", name="peerlist",
                                  rhs="(int *) ncptl_queue_contents(mcast_ev->peerqueue, 0)",
                                  comment="List of our peers' physical task numbers",
                                  stack=msgfuncs)
            self.code_declare_var(name="maxrank",
                                  rhs="ncptl_queue_length(mcast_ev->peerqueue) - 1",
                                  comment="Number of tasks involved in the multicast",
                                  stack=msgfuncs)
            self.code_declare_var(type="CONC_SEND_EVENT", name="sendev",
                                  comment="Send event to pass to conc_asend_msg()",
                                  stack=msgfuncs)
            self.code_declare_var(type="CONC_RECV_EVENT", name="recvev",
                                  comment="Receive event to pass to conc_recv_msg()",
                                  stack=msgfuncs)
            self.pushmany([
                    "",
                    " /* Multicast data in a binary-tree pattern. */",
                    "memset ((void *)&sendev, 0, sizeof(CONC_SEND_EVENT));",
                    "sendev.size = mcast_ev->size;"],
                          stack=msgfuncs)
            for field in ["alignment", "buffernum", "bufferofs", "misaligned",
                          "touching", "verification", "buffer"]:
                self.push("sendev.%s = mcast_ev->%s;" % (field, field), msgfuncs)
            self.pushmany([
                    "memset ((void *)&recvev, 0, sizeof(CONC_RECV_EVENT));",
                    "recvev.size = mcast_ev->size;"],
                          stack=msgfuncs)
            for field in ["alignment", "buffernum", "bufferofs", "misaligned",
                          "touching", "verification", "buffer"]:
                self.push("recvev.%s = mcast_ev->%s;" % (field, field), msgfuncs)
            self.pushmany([
                    "if (mcastrank > 0) {",
                    " /* Receive synchronously from our parent. */",
                    "recvev.source = peerlist[(mcastrank-1)/2];",
                    "conc_recv_msg (cstate, &recvev);",
                    "}",
                    "if ((mcastrank+1)*2-1 <= maxrank) {",
                    " /* Send asynchronously to our left child. */",
                    "sendev.dest = peerlist[(mcastrank+1)*2 - 1];",
                    "conc_asend_msg (cstate, &sendev);",
                    "if ((mcastrank+1)*2 <= maxrank) {",
                    " /* Send asynchronously to our right child. */",
                    "sendev.dest = peerlist[(mcastrank+1)*2];",
                    "conc_asend_msg (cstate, &sendev);",
                    "}",
                    "",
                    " /* Wait for all of our pending sends to complete. */",
                    "conc_wait_all (cstate);",
                    "}",
                    "}"],
                          stack=msgfuncs)

        # Define a reduction function.
        if uses_reduce:
            self.pushmany([
                    "/* Reduce data from one set of tasks to another set. */",
                    "static inline void conc_reduce (COMMSTATE *cstate, CONC_REDUCE_EVENT *reduce_ev)",
                    "{"],
                          stack=msgfuncs)
            self.push(" /* Implement all forms of reduction as a reduce-to-one followed by an optional multicast. */", msgfuncs)
            self.code_declare_var(name="sendrank",
                                  rhs="reduce_ev->sendrank",
                                  comment="This task's rank in the reduction step",
                                  stack=msgfuncs)
            self.code_declare_var(name="recvrank",
                                  rhs="reduce_ev->recvrank",
                                  comment="This task's rank in the multicast step",
                                  stack=msgfuncs)
            self.code_declare_var(name="msgsize",
                                  rhs="reduce_ev->numitems * reduce_ev->itemsize",
                                  comment="The number of bytes in the reduction message",
                                  stack=msgfuncs)
            self.code_declare_var(type="ncptl_int *", name="send_peerlist",
                                  rhs="(ncptl_int *) ncptl_queue_contents(reduce_ev->all_senders, 0)",
                                  comment="List of our reduction peers' physical task numbers",
                                  stack=msgfuncs)
            self.code_declare_var(type="ncptl_int *", name="recv_peerlist",
                                  rhs="(ncptl_int *) ncptl_queue_contents(reduce_ev->all_receivers, 0)",
                                  comment="List of our multicast peers' physical task numbers",
                                  stack=msgfuncs)
            self.code_declare_var(name="num_send_peers",
                                  rhs="ncptl_queue_length(reduce_ev->all_senders)",
                                  comment="Number of tasks involved in the reduction step",
                                  stack=msgfuncs)
            self.code_declare_var(name="num_recv_peers",
                                  rhs="ncptl_queue_length(reduce_ev->all_receivers)",
                                  comment="Number of tasks involved in the multicast step",
                                  stack=msgfuncs)
            self.code_declare_var(type="CONC_SEND_EVENT", name="sendev",
                                  comment="Send event to pass to conc_asend_msg()",
                                  stack=msgfuncs)
            self.code_declare_var(type="CONC_RECV_EVENT", name="recvev",
                                  comment="Receive event to pass to conc_recv_msg()",
                                  stack=msgfuncs)
            self.pushmany([
                "",
                " /* Implement a reduction tree to reduce a value to the first sender. */",
                "memset ((void *)&sendev, 0, sizeof(CONC_SEND_EVENT));",
                "sendev.size = msgsize;"],
                          stack=msgfuncs)
            for field in ["alignment", "buffernum", "bufferofs", "misaligned",
                          "touching", "buffer"]:
                self.push("sendev.%s = reduce_ev->%s;" % (field, field), msgfuncs)
            self.pushmany([
                "memset ((void *)&recvev, 0, sizeof(CONC_RECV_EVENT));",
                "recvev.size = msgsize;"],
                          stack=msgfuncs)
            for field in ["alignment", "buffernum", "bufferofs", "misaligned",
                          "touching", "buffer"]:
                self.push("recvev.%s = reduce_ev->%s;" % (field, field), msgfuncs)
            self.pushmany([
                "if (reduce_ev->sending) {",
                " /* Receive asynchronously from our children. */",
                "if ((sendrank+1)*2-1 < num_send_peers) {",
                "recvev.source = send_peerlist[(sendrank+1)*2-1];",
                "conc_arecv_msg (cstate, &recvev);",
                "if ((sendrank+1)*2 < num_send_peers) {",
                "recvev.source = send_peerlist[(sendrank+1)*2];",
                "conc_arecv_msg (cstate, &recvev);",
                "}",
                "conc_wait_all (cstate);",
                "}",
                "",
                " /* Send synchronously to our parent. */",
                "if (sendrank > 0) {",
                "sendev.dest = send_peerlist[(sendrank-1)/2];",
                "conc_send_msg (cstate, &sendev);",
                "}",
                "else {",
                " /* The root of the reduction sends to the root of the multicast. */",
                "if (send_peerlist[0] != recv_peerlist[0]) {",
                "sendev.dest = recv_peerlist[0];",
                "conc_send_msg (cstate, &sendev);",
                "}"
                "}"
                "}"],
                          stack=msgfuncs)
            self.pushmany([
                "",
                " /* Implement a multicast tree to multicast from the first receiver. */",
                "if (reduce_ev->receiving) {",
                "if (recvrank == 0 && send_peerlist[0] != recv_peerlist[0]) {",
                " /* The root of the multicast receives from the root of the reduction. */",
                "recvev.source = send_peerlist[0];",
                "conc_recv_msg (cstate, &recvev);",
                "}",
                "",
                "if (recvrank > 0) {",
                " /* Receive synchronously from our parent. */",
                "recvev.source = recv_peerlist[(recvrank-1)/2];",
                "conc_recv_msg (cstate, &recvev);",
                "}",
                "if ((recvrank+1)*2-1 < num_recv_peers) {",
                " /* Send asynchronously to our left child. */",
                "sendev.dest = recv_peerlist[(recvrank+1)*2 - 1];",
                "conc_asend_msg (cstate, &sendev);",
                "if ((recvrank+1)*2 < num_recv_peers) {",
                " /* Send asynchronously to our right child. */",
                "sendev.dest = recv_peerlist[(recvrank+1)*2];",
                "conc_asend_msg (cstate, &sendev);",
                "}",
                "",
                " /* Wait for any blocked sends to complete. */",
                "conc_wait_all (cstate);",
                "}",
                "}",
                "}"],
                          stack=msgfuncs)

        # Return the list of function definitions.
        return msgfuncs


    # -------------- #
    # Initialization #
    # -------------- #

    def code_define_functions_INIT_COMM_1(self, localvars):
        "Define extra initialization to be performed after ncptl_init()."
        return [
            " /* Prevent exiting children from killing their parent. */",
            "ncptl_permit_signal(SIGCHLD);"]

    def code_def_init_cmd_line_PRE_PARSE(self, localvars):
        "Toggle the abnormal_exit flag."
        return ['abnormal_exit = 0;     /* Let "--help" exit normally. */']

    def code_def_init_cmd_line_POST_PARSE(self, localvars):
        "Toggle the abnormal_exit flag."
        return ['abnormal_exit = 1;']

    def code_define_functions_INIT_COMM_3(self, localvars):
        "Generate code to initialize the c_udgram backend."
        initcode = []

        # Create a unique name for every socket we plan to use.
        self.pushmany([
            " /* Create names for all of the sockets every task will need. */",
            "socketinfo = (struct sockaddr_un ***) ncptl_malloc (NUMCHANNELSETS*sizeof (struct sockaddr_un **), 0);",
            "for (cset=0; cset<NUMCHANNELSETS; cset++) {"],
                      stack=initcode)
        self.code_declare_var(name="src", comment="Source task ID",
                              stack=initcode)
        self.code_declare_var(name="dest", comment="Destination task ID",
                              stack=initcode)
        self.pushmany([
            "socketinfo[cset] = (struct sockaddr_un **) ncptl_malloc (var_num_tasks*sizeof (struct sockaddr_un *), 0);",
            "for (dest = 0; dest < var_num_tasks; dest++) {",
            "socketinfo[cset][dest] = (struct sockaddr_un *) ncptl_malloc (var_num_tasks*sizeof (struct sockaddr_un), 0);",
            "for (src = 0; src < var_num_tasks; src++) {"],
                      stack=initcode)
        self.code_declare_var(type="int", name="tempfd",
                              comment="File descriptor returned by mkstemp() (not used)",
                              stack=initcode)
        self.pushmany([
            "socketinfo[cset][dest][src].sun_family = AF_UNIX;",
            "strcpy (socketinfo[cset][dest][src].sun_path, SOCKET_TEMPLATE);",
            "if ((tempfd=mkstemp(socketinfo[cset][dest][src].sun_path)) == -1)",
            'CONC_SYSTEM_ERROR ("Failed to create a unique filename");',
            "if (close (tempfd) == -1)",
            'CONC_SYSTEM_ERROR ("Failed to close an open file");',
            "}",
            "}",
            "}",
            ""],
                      stack=initcode)

        # Spawn child tasks.
        self.pushmany([
            " /* Spawn var_num_tasks-1 processes (one per task excluding the master). */",
            "physrank = 0;",
            "if (setpgid (0, 0) == -1)",
            'CONC_SYSTEM_ERROR ("Failed to start a new process group");',
            "for (i=1; i<var_num_tasks; i++) {",
            " /* Spawn a child task and assign it a virtual task ID.  While",
            "  * this could be done in a tree pattern instead of linearly,",
            "  * we expect var_num_tasks to be small; plus, a simple mapping",
            "  * from PIDs to tasks may help debug deadlocks and other",
            "  * problems. */"],
                      stack=initcode)
        self.code_declare_var(type="int", name="newpid",
                              comment="0=child; other=parent",
                              stack=initcode)
        self.pushmany([
            "if ((newpid=fork()) == -1)",
            'CONC_SYSTEM_ERROR ("Failed to spawn a child process");',
            "else",
            "if (!newpid) {",
            " /* Child */",
            "physrank = (ncptl_int) i;",
            "break;",
            "}",
            "}",
            ""],
                      stack=initcode)

        # Create and bind socket connections to every other task.
        self.pushmany([
            " /* Create and bind sockets for inter-task communication. */",
            "for (cset=0; cset<NUMCHANNELSETS; cset++) {"],
                      stack=initcode)
        self.code_declare_var(type="COMMSTATE *", name="cstate",
                              rhs="&commstate[cset]", comment="Current channel set",
                              stack=initcode)
        self.pushmany([
            "cstate->channels = (int *) ncptl_malloc (var_num_tasks*sizeof (int), 0);",
            "for (taskID=0; taskID<var_num_tasks; taskID++) {",
            "if ((cstate->channels[taskID] = socket (PF_UNIX, SOCK_DGRAM, 0)) == -1)",
            'CONC_SYSTEM_ERROR ("Socket creation failed");',
            "if (unlink (socketinfo[cset][physrank][taskID].sun_path) == -1)",
            'CONC_SYSTEM_ERROR ("File deletion failed");',
            "if (bind (cstate->channels[taskID],",
            "(const struct sockaddr *) &socketinfo[cset][physrank][taskID],",
            "SUN_LEN (&socketinfo[cset][physrank][taskID])) == -1)",
            'CONC_SYSTEM_ERROR ("Failed to bind a socket");',
            "}",
            "}",
            ""],
                      stack=initcode)

        # Connect all of the sockets we created.
        self.pushmany([
            " /* Connect to each of our peers in turn. */",
            "for (cset=0; cset<NUMCHANNELSETS; cset++) {"],
                      stack=initcode)
        self.code_declare_var(type="COMMSTATE *", name="cstate",
                              rhs="&commstate[cset]", comment="Current channel set",
                              stack=initcode)
        self.pushmany([
            "for (taskID=0; taskID<var_num_tasks; taskID++) {",
            " /* Keep trying to connect until the socket we want",
            "  * to connect to exists and is, in fact, a socket. */",
            "while (connect (cstate->channels[taskID],",
            "(const struct sockaddr *) &socketinfo[cset][taskID][physrank],",
            "SUN_LEN (&socketinfo[cset][taskID][physrank])) == -1) {",
            "if (errno!=ECONNREFUSED && errno!=ENOENT)",
            'CONC_SYSTEM_ERROR ("Failed to connect a socket");',
            "usleep (1000);",
            "}",
            "",
            " /* Now that we're connected, put the socket in nonblocking mode. */",
            "CONC_SET_BLOCKING (cstate, taskID, 0);",
            "}",
            "}",
            ""],
                      stack=initcode)

        # Clean up temporary resources.
        self.pushmany([
            " /* Free all of the resources we no longer need. */",
            "for (cset=0; cset<NUMCHANNELSETS; cset++) {",
            "for (taskID=0; taskID<var_num_tasks; taskID++) {",
            "(void) unlink (socketinfo[cset][taskID][physrank].sun_path);",
            "ncptl_free (socketinfo[cset][taskID]);",
            "}",
            "ncptl_free (socketinfo[cset]);",
            "}",
            ""],
                      stack=initcode)

        # Determine the maximum packet length.
        self.pushmany([
            " /* Determine the maximum packet length. */",
            "maxpacketlen = conc_find_max_packet_len (&commstate[0]);",
            'sprintf (maxpacketlen_str, "%" NICS " bytes", maxpacketlen);',
            'ncptl_log_add_comment ("Maximum payload per datagram", maxpacketlen_str);'],
                      stack=initcode)
        return initcode

    def code_def_init_misc_EXTRA(self, localvars):
        "Initialize everything else that needs to be initialized."
        initcode = []
        self.push("for (cset=0; cset<NUMCHANNELSETS; cset++) {", initcode)
        self.code_declare_var(type="COMMSTATE *", name="cstate",
                              rhs="&commstate[cset]", comment="Current channel set",
                              stack=initcode)
        self.pushmany([
            "cstate->blockedsendQ = ncptl_malloc (var_num_tasks*sizeof(NCPTL_QUEUE *), 0);",
            "cstate->blockedrecvQ = ncptl_malloc (var_num_tasks*sizeof(NCPTL_QUEUE *), 0);",
            "for (taskID=0; taskID<var_num_tasks; taskID++) {",
            "cstate->blockedsendQ[taskID] = ncptl_queue_init (sizeof (CONC_SEND_EVENT));",
            "cstate->blockedrecvQ[taskID] = ncptl_queue_init (sizeof (CONC_RECV_EVENT));",
            "}",
            "cstate->sendsblocked = 0;",
            "cstate->recvsblocked = 0;",
            "}",
            "",
            "alltasksQ = ncptl_queue_init (sizeof(int));",
            "for (i=0; i<(int)var_num_tasks; i++)",
            "ncptl_queue_push (alltasksQ, &i);"],
                      stack=initcode)
        return initcode

    def code_def_init_reseed_BCAST(self, localvars):
        '"Broadcast" a random-number seed to all tasks.'
        # We don't need to do anything because the random-number seed
        # is selected before we fork() the worker tasks.
        return []

    def code_def_init_uuid_BCAST(self, locals):
        '"Broadcast" logfile_uuid to all tasks.'
        # We don't need to do anything because the UUID is generated
        # before we fork() the worker tasks.
        pass


    # ------------ #
    # Finalization #
    # ------------ #

    def code_def_finalize_DECL(self, localvars):
        "Declare variables needed by code_def_finalize_POST."
        declcode = []
        self.code_declare_var(type="int", name="childstatus",
                              comment="Exit status of a child process",
                              stack=declcode)
        self.code_declare_var(type="COMMSTATE *", name="cstate",
                              comment="Pointer into commstate[]",
                              stack=declcode)
        self.code_declare_var(name="i",
                              comment="Loop over child task IDs",
                              stack=declcode)
        return declcode

    def code_def_finalize_POST(self, localvars):
        "Finish up cleanly."
        # Process 0 blocks until all of its children exit.
        return [
            "conc_synchronize (&commstate[COMMSTATE_COLL],",
            "ncptl_queue_contents (alltasksQ, 0),",
            "ncptl_queue_length (alltasksQ) - 1,",
            "physrank);",
            "if (physrank == 0)",
            "for (i=1; i<var_num_tasks; i++)",
            "if (wait (&childstatus)==-1 || !WIFEXITED(childstatus))",
            "exitcode = 1;",
            "for (cstate=commstate; cstate<commstate+NUMCHANNELSETS; cstate++) {",
            "for (i=0; i<var_num_tasks; i++) {",
            "ncptl_queue_empty (cstate->blockedsendQ[i]);",
            "ncptl_queue_empty (cstate->blockedrecvQ[i]);",
            "}",
            "ncptl_free (cstate->channels);",
            "ncptl_free (cstate->blockedsendQ);",
            "ncptl_free (cstate->blockedrecvQ);",
            "}",
            "abnormal_exit = 0;"]

    def code_def_exit_handler_BODY(self, localvars):
        """
            Terminate all processes in the program if we exited
            without calling conc_finalize().
        """
        return [
            "if (abnormal_exit)",
            "(void) killpg (0, SIGTERM);"]


    # ---------------------------- #
    # Point-to-point communication #
    # ---------------------------- #

    def n_send_stmt_BODY(self, localvars):
        "Disallow nonzero tags."
        return self.code_reject_nonzero_tag(localvars["struct"], "SEND")

    def n_recv_stmt_BODY(self, localvars):
        "Disallow nonzero tags."
        return self.code_reject_nonzero_tag(localvars["struct"], "RECEIVE")

    def code_def_procev_send_BODY(self, localvars):
        "Send a message down a given channel (blocking)."
        return ["conc_send_msg (&commstate[COMMSTATE_PT2PT], &thisev->s.send);"]

    def code_def_procev_recv_BODY(self, localvars):
        "Receive a message from a given channel (blocking)."
        return ["conc_recv_msg (&commstate[COMMSTATE_PT2PT], &thisev->s.recv);"]

    def code_def_procev_asend_BODY(self, localvars):
        "Perform an asynchronous send."
        return [
            "conc_asend_msg (&commstate[COMMSTATE_PT2PT], &thisev->s.send);"]

    def code_def_procev_arecv_BODY(self, localvars):
        "Perform an asynchronous receive."
        return [
            "conc_arecv_msg (&commstate[COMMSTATE_PT2PT], &thisev->s.recv);"]

    def code_def_procev_wait_BODY_SENDS(self, localvars):
        "Retry all of the sends that blocked."
        return ["conc_wait_all (&commstate[COMMSTATE_PT2PT]);"]

    def code_def_procev_wait_BODY_RECVS(self, localvars):
        "Retry all of the receives that blocked."
        return ["conc_wait_all (&commstate[COMMSTATE_PT2PT]);"]


    # ------------------------ #
    # Collective communication #
    # ------------------------ #

    def code_mcast_sync_datatypes(self, operation, op):
        "Declare fields needed for a multicast or a synchronization event."
        newfields = []
        self.code_declare_var(type="NCPTL_QUEUE *", name="peerqueue",
                              comment="Map from %s rank to physical rank" %
                              operation,
                              stack=newfields)
        self.code_declare_var(type="int", name="%srank" % op,
                              comment="This task's rank in the %s" % operation,
                              stack=newfields)
        return newfields

    def code_mcast_sync_declarations(self, source_task):
        "Declare variables needed by n_mcast_stmt_INIT or n_sync_stmt_INIT."
        newdecls = []
        if source_task[0] != 'task_expr' and source_task[1]:
            self.mcast_sync_loop_var = source_task[1]
        else:
            self.mcast_sync_loop_var = self.code_declare_var(suffix="task",
                                                             comment="Each (virtual) rank in turn",
                                                             stack=newdecls)
        return newdecls

    def code_mcast_sync_initialize(self, operation, op, source_task):
        "Store all the state needed to multicast data or synchronize a set of tasks."
        initcode = []

        # Loop over each virtual task, adding its physical equivalent
        # to a list if it's in the multicast/synchronization set.
        self.pushmany([
            " /* Construct a list of (physical) tasks involved in the operation. */",
            "thisev->s.%s.peerqueue = ncptl_queue_init (sizeof(int));" % op,
            "for (%s=0; %s<var_num_tasks; %s++) {" %
            (self.mcast_sync_loop_var, self.mcast_sync_loop_var, self.mcast_sync_loop_var)],
                      stack=initcode)
        if source_task[0] == "let_task":
            source_task, srenamefrom, srenameto = self.task_group_to_task(source_task)
            if srenamefrom != None:
                self.code_declare_var(name=srenameto, rhs=srenamefrom, stack=mcastcode)
        if source_task[0] == 'task_expr':
            # Collectives involving a single task are fairly pointless
            # but we retain this case because task_restricted may
            # refer to a single task, anyway.
            self.push("if (%s == (%s)) {" % (self.mcast_sync_loop_var, source_task[1]),
                      stack=initcode)
        elif source_task[0] == 'task_all':
            pass
        elif source_task[0] == 'task_restricted':
            self.push("if (%s) {" % source_task[2], initcode)
        else:
            self.errmsg.error_internal('unknown source task type "%s"' % source_task[0])

        # Add a task to an ordered list.
        self.code_declare_var(type="int *", name="physnode_ptr",
                              rhs="(int *) ncptl_queue_allocate(thisev->s.%s.peerqueue)" % op,
                              comment="Physical node number of one of our peers (or us)",
                              stack=initcode)
        self.push("*physnode_ptr = (int) ncptl_virtual_to_physical (procmap, %s);" % self.mcast_sync_loop_var,
                  initcode)
        if op == "mcast":
            # Include extra code for a multicast to move the sender to the front.
            self.pushmany([
                "if (%s == %s) {" %
                (self.mcast_sync_loop_var, self.mcast_source_var),
                " /* Swap the sending task to the front of the list. */"],
                          stack=initcode)
            swapvar = self.code_declare_var(type="int *", suffix="task",
                                            rhs="(int *)ncptl_queue_contents (thisev->s.%s.peerqueue, 0)" % op,
                                            stack=initcode)
            self.pushmany([
                "*physnode_ptr = *%s;" % swapvar,
                "*%s = (int) ncptl_virtual_to_physical (procmap, %s);" % (swapvar, self.mcast_sync_loop_var),
                "",
                " /* Store or adjust our rank in the multicast. */",
                "if (virtrank == %s)" % self.mcast_sync_loop_var,
                "thisev->s.%s.%srank = 0;" % (op, op),
                "else",
                "if (ncptl_virtual_to_physical(procmap, virtrank) == *physnode_ptr)",
                "thisev->s.%s.%srank = ncptl_queue_length(thisev->s.%s.peerqueue) - 1;" %
                (op, op, op),
                "}",
                "else"],
                          stack=initcode)
        self.pushmany([
            "if (%s == virtrank)" % self.mcast_sync_loop_var,
            " /* Store our offset into the %s peer list. */" % operation,
            "thisev->s.%s.%srank = ncptl_queue_length(thisev->s.%s.peerqueue) - 1;" %
            (op, op, op)],
                      stack=initcode)

        # End the loop and return our accumulated code.
        if source_task[0] in ["task_expr", "task_restricted"]:
            self.push("}", initcode)
        self.push("}", initcode)
        return initcode


    def code_declare_datatypes_SYNC_STATE(self, localvars):
        "Declare fields in the CONC_SYNC_EVENT structure for synchronization events."
        return self.code_mcast_sync_datatypes("barrier", "sync")

    def n_sync_stmt_DECL(self, localvars):
        "Declare variables needed by n_sync_stmt_INIT."
        return self.code_mcast_sync_declarations(localvars["source_task"])

    def n_sync_stmt_INIT(self, localvars):
        "Store all state needed to synchronize a set of tasks."
        return self.code_mcast_sync_initialize("barrier", "sync", localvars["source_task"])

    def code_def_procev_sync_BODY(self, localvars):
        "Synchronize a set of tasks."
        return [
            "conc_synchronize (&commstate[COMMSTATE_COLL], ",
            "ncptl_queue_contents (thisev->s.sync.peerqueue, 0),",
            "ncptl_queue_length (thisev->s.sync.peerqueue) - 1,",
            "thisev->s.sync.syncrank);"]

    def n_for_count_SYNC_ALL(self, localvars):
        "Prepare to synchronize all of the tasks in the job."
        return [
            "thisev_sync->s.sync.peerqueue = alltasksQ;",
            "thisev_sync->s.sync.syncrank = physrank;"]

    def code_synchronize_all_BODY(self, localvars):
        "Immediately synchronize all of the tasks in the job."
        return [
            "conc_synchronize (&commstate[COMMSTATE_COLL], ",
            "ncptl_queue_contents (alltasksQ, 0),",
            "ncptl_queue_length (alltasksQ) - 1,",
            "physrank);"]

    def code_declare_datatypes_MCAST_STATE(self, localvars):
        "Declare fields in the CONC_MCAST_EVENT structure for multicast events."
        return self.code_mcast_sync_datatypes("multicast", "mcast")

    def n_mcast_stmt_DECL(self, localvars):
        "Declare variables needed by n_mcast_stmt_INIT."
        mcastdecls = []
        self.pushmany(self.code_mcast_sync_declarations(localvars["target_or_source"]),
                      stack=mcastdecls)
        self.mcast_source_var = localvars["sourcevar"]
        return mcastdecls

    def n_mcast_stmt_INIT(self, localvars):
        "Store all state needed to multicast a message a set of tasks."
        mcastcode = []
        self.pushmany(self.code_reject_nonzero_tag(localvars["struct"], "MULTICAST"), stack=mcastcode)
        self.push("", stack=mcastcode)
        self.pushmany(self.code_mcast_sync_initialize("multicast", "mcast", localvars["target_or_source"]),
                      stack=mcastcode)
        return mcastcode

    def code_def_procev_mcast_BODY(self, localvars):
        "Multicast a message to a set of tasks."
        return ["conc_multicast (&commstate[COMMSTATE_COLL], &thisev->s.mcast);"]

    def code_def_procev_etime_REDUCE_MIN(self, localvars):
        "Find the global minimum of the elapsedtime variable."
        reducecode = []
        self.push("{", reducecode)
        self.code_declare_var(name="parent", rhs="(physrank-1)/2",
                              comment="Our parent's task ID",
                              stack=reducecode)
        self.code_declare_var(name="lchild", rhs="physrank*2 + 1",
                              comment="Our left child's task ID",
                              stack=reducecode)
        self.code_declare_var(name="rchild", rhs="physrank*2 + 2",
                              comment="Our right child's task ID",
                              stack=reducecode)
        self.code_declare_var(type="CONC_SEND_EVENT", name="sendev",
                              comment="Send event to pass to conc_send_msg()",
                              stack=reducecode)
        self.code_declare_var(type="CONC_RECV_EVENT", name="recvev",
                              comment="Receive event to pass to conc_recv_msg()",
                              stack=reducecode)
        self.pushmany([
            "",
            " /* Each task reduces its children's values",
            "  * and sends the result to its parent. */",
            "minelapsedtime = elapsedtime;",
            "memset ((void *)&sendev, 0, sizeof(CONC_SEND_EVENT));",
            "sendev.size = sizeof(uint64_t);",
            "memset ((void *)&recvev, 0, sizeof(CONC_RECV_EVENT));",
            "recvev.size = sizeof(uint64_t);",
            "recvev.buffer = (void *) &elapsedtime;",
            "if (rchild < var_num_tasks) {",
            "recvev.source = rchild;",
            "conc_recv_msg (&commstate[COMMSTATE_COLL], &recvev);",
            "minelapsedtime = (minelapsedtime>elapsedtime) ? elapsedtime : minelapsedtime;",
            "}",
            "if (lchild < var_num_tasks) {",
            "recvev.source = lchild;",
            "conc_recv_msg (&commstate[COMMSTATE_COLL], &recvev);",
            "minelapsedtime = (minelapsedtime>elapsedtime) ? elapsedtime : minelapsedtime;",
            "}",
            "sendev.buffer = recvev.buffer = (void *) &minelapsedtime;",
            "if (physrank > 0) {",
            "sendev.dest = parent;",
            "conc_send_msg (&commstate[COMMSTATE_COLL], &sendev);",
            "}",
            "",
            " /* The root propagates the minimum value back down the tree. */",
            "if (physrank > 0) {",
            "recvev.source = parent;",
            "conc_recv_msg (&commstate[COMMSTATE_COLL], &recvev);",
            "}",
            "if (rchild < var_num_tasks) {",
            "sendev.dest = rchild;",
            "conc_send_msg (&commstate[COMMSTATE_COLL], &sendev);",
            "}",
            "if (lchild < var_num_tasks) {",
            "sendev.dest = lchild;",
            "conc_send_msg (&commstate[COMMSTATE_COLL], &sendev);",
            "}",
            "}"],
                      stack=reducecode)
        return reducecode

    def code_declare_datatypes_REDUCE_STATE(self, localvars):
        "Declare fields in the CONC_REDUCE_EVENT structure for reduction events."
        newfields = []
        self.code_declare_var(type="NCPTL_QUEUE *", name="all_senders",
                              comment="Map from reduction rank to physical rank (reduce step)",
                              stack=newfields)
        self.code_declare_var(type="NCPTL_QUEUE *", name="all_receivers",
                              comment="Map from reduction rank to physical rank (multicast step)",
                              stack=newfields)
        self.code_declare_var(type="int", name="sendrank",
                              comment="This task's rank in the reduction (reduce step)",
                              stack=newfields)
        self.code_declare_var(type="int", name="recvrank",
                              comment="This task's rank in the reduction (multicast step)",
                              stack=newfields)
        return newfields

    def n_reduce_stmt_INIT2(self, localvars):
        "Store our peer list in the reduce event."
        struct = localvars["struct"]
        reducecode = []
        self.pushmany(self.code_reject_nonzero_tag(localvars["struct"], "REDUCE"),
                      stack=reducecode)
        self.pushmany([
            "",
            " /* Store the list of senders and receivers and our offset into each list. */",
            "%s.all_senders = ncptl_queue_init (sizeof(ncptl_int));" % struct,
            "%s.all_receivers = ncptl_queue_init (sizeof(ncptl_int));" % struct,
            "for (i=0; i<var_num_tasks; i++) {"],
                  reducecode)
        self.code_declare_var(name="physrank_i", rhs="ncptl_virtual_to_physical (procmap, i)",
                              comment="Physical rank corresponding to virtual task ID i",
                              stack=reducecode)
        self.pushmany([
            "if (reduce_senders[i]) {",
            "ncptl_queue_push (%s.all_senders, (void *) &physrank_i);" % struct,
            "if (i == virtrank)",
            "%s.sendrank = ncptl_queue_length (%s.all_senders) - 1;" % (struct, struct),
            "}",
            "if (reduce_receivers[i]) {",
            "ncptl_queue_push (%s.all_receivers, (void *) &physrank_i);" % struct,
            "if (i == virtrank)",
            "%s.recvrank = ncptl_queue_length (%s.all_receivers) - 1;" % (struct, struct),
            "}",
            "}"],
                      stack=reducecode)
        return reducecode

    def code_def_procev_reduce_BODY(self, localvars):
        "Perform a reduction operation."
        return ["conc_reduce (&commstate[COMMSTATE_COLL], &thisev->s.reduce);"]
