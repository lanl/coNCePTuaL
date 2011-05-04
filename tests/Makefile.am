######################################
# Define a test suite for coNCePTuaL #
# By Scott Pakin <pakin@lanl.gov>    #
######################################

# ----------------------------------------------------------------------
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
# ----------------------------------------------------------------------

@DEFINE_RM@
EXTRA_DIST = regresstest.ncptl

# If we don't have a run-time library we don't need to check it.
if BUILD_RUN_TIME_LIBRARY

USERFUNC_TESTS = userfunc_sqrt userfunc_cbrt userfunc_bits userfunc_power  \
		 userfunc_modulo userfunc_round userfunc_random		   \
		 userfunc_factor10 userfunc_topologies
RUNTIME_TESTS = runtime_init runtime_time runtime_malloc runtime_verify    \
		runtime_walk runtime_queue runtime_set runtime_cmdline     \
		runtime_logfile runtime_random

check_PROGRAMS = $(USERFUNC_TESTS) $(RUNTIME_TESTS)

userfunc_sqrt_SOURCES = userfunc_sqrt.c ncptl_test.h
userfunc_sqrt_LDADD = $(top_builddir)/libncptl.la

userfunc_cbrt_SOURCES = userfunc_cbrt.c ncptl_test.h
userfunc_cbrt_LDADD = $(top_builddir)/libncptl.la

userfunc_bits_SOURCES = userfunc_bits.c ncptl_test.h
userfunc_bits_LDADD = $(top_builddir)/libncptl.la

userfunc_power_SOURCES = userfunc_power.c ncptl_test.h
userfunc_power_LDADD = $(top_builddir)/libncptl.la

userfunc_modulo_SOURCES = userfunc_modulo.c ncptl_test.h
userfunc_modulo_LDADD = $(top_builddir)/libncptl.la

userfunc_round_SOURCES = userfunc_round.c ncptl_test.h
userfunc_round_LDADD = $(top_builddir)/libncptl.la

userfunc_factor10_SOURCES = userfunc_factor10.c ncptl_test.h
userfunc_factor10_LDADD = $(top_builddir)/libncptl.la

userfunc_random_SOURCES = userfunc_random.c ncptl_test.h
userfunc_random_LDADD = $(top_builddir)/libncptl.la

userfunc_topologies_SOURCES = userfunc_topologies.c ncptl_test.h
userfunc_topologies_LDADD = $(top_builddir)/libncptl.la

runtime_init_SOURCES = runtime_init.c ncptl_test.h
runtime_init_LDADD = $(top_builddir)/libncptl.la

runtime_malloc_SOURCES = runtime_malloc.c ncptl_test.h
runtime_malloc_LDADD = $(top_builddir)/libncptl.la

runtime_verify_SOURCES = runtime_verify.c ncptl_test.h
runtime_verify_LDADD = $(top_builddir)/libncptl.la

runtime_walk_SOURCES = runtime_walk.c ncptl_test.h
runtime_walk_LDADD = $(top_builddir)/libncptl.la

runtime_queue_SOURCES = runtime_queue.c ncptl_test.h
runtime_queue_LDADD = $(top_builddir)/libncptl.la

runtime_set_SOURCES = runtime_set.c ncptl_test.h
runtime_set_LDADD = $(top_builddir)/libncptl.la

runtime_cmdline_SOURCES = runtime_cmdline.c ncptl_test.h
runtime_cmdline_LDADD = $(top_builddir)/libncptl.la

runtime_logfile_SOURCES = runtime_logfile.c ncptl_test.h
runtime_logfile_LDADD = $(top_builddir)/libncptl.la

runtime_time_SOURCES = runtime_time.c ncptl_test.h
runtime_time_LDADD = $(top_builddir)/libncptl.la

runtime_random_SOURCES = runtime_random.c ncptl_test.h
runtime_random_LDADD = $(top_builddir)/libncptl.la

## Matches "if BUILD_RUN_TIME_LIBRARY".
endif

###########################################################################

if BUILD_PYMODULE
# The Python interface to the C run-time library was built and
# therefore needs to be tested.  We do this testing via the coNCePTuaL
# interpreter backend.
BACKEND_INTERPRET_FILE = backend_interpret
endif

mostlyclean-local:
	-$(RM) -r build lib ncptl.py*
	-$(RM) backend-interpret-tmp.*

###########################################################################

# Specify all of the scripts we intend to run.
BACKEND_SCRIPT_FILES = backend_dot_ast $(BACKEND_INTERPRET_FILE)
COMPILER_TESTS = $(BACKEND_SCRIPT_FILES)
check_SCRIPTS = $(BACKEND_SCRIPT_FILES)

# Define the tests to perform.
TESTS = $(USERFUNC_TESTS) $(RUNTIME_TESTS) $(COMPILER_TESTS)
