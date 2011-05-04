# ----------------------------------------------------------------------
#
# Configure the coNCePTuaL compiler
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
# ----------------------------------------------------------------------

# Initialize Autoconf.
AC_INIT([coNCePTuaL], [1.2], [pakin@lanl.gov], [conceptual])

# The following files are deleted by "make distclean" but checked
# early in configure for their existence.  Hence, we create them right
# away before we even know what they should contain.
touch substitutions.dat.in
touch ncptl.pc.in
# Finish initializing Autoconf.
AC_PREREQ([2.53])
AC_REVISION($Revision: 3.205 $)
AC_CONFIG_SRCDIR([yacc.py])
AC_COPYRIGHT([PUT_LICENSE_][TEXT_HERE])
AX_SAVE_WARNINGS

# Ensure that Libtool can find a make program.  We've used an
# OpenSolaris system whose default path lacked make
# (/usr/ccs/bin/make) but included gmake.
AC_CHECK_PROGS([MAKE], [gmake make], [no])
if test "$MAKE" = no ; then
  AC_MSG_ERROR([$PACKAGE_NAME can't build without a make program])
fi

# Initialize Automake.
AM_INIT_AUTOMAKE([1.6])dnl Later versions than this are needed to pass "make distcheck".
AM_CONFIG_HEADER(config.h)dnl Brackets screw up the "missing" script.
AM_MAINTAINER_MODE
dnl Automake 1.6 incorrectly generates *two* ncptl.h.ni targets if
dnl ncptl.h:ncptl.h.ni is listed in AM_CONFIG_HEADER and
dnl ncptl.h.ni:ncptl.h.in is listed in AC_CONFIG_FILES.  The following
dnl line is a kludge to hide a call to AC_CONFIG_HEADERS from Automake so
dnl that it doesn't generate an extraneous ncptl.h.ni target.
m4_substr([XAC_CONFIG_HEADERS], 1)([ncptl.h:ncptl.h.ni])

# Facilitate cross-compiling to the same architecture/operating system.
AC_ARG_WITH([cross-compilation],
  [AC_HELP_STRING([--with-cross-compilation],
    [force cross-compilation])],
  [cross_compiling=yes])

# Try to expand the CC filename.
AM_PROG_CC_STDC
if test ! -z "$CC" ; then
  AC_PATH_PROG([full_CC], [$CC], [$CC])
  AC_MSG_CHECKING([if we can expand \"$CC\"])
  set dummy $CC
  shift
  shift
  full_CC="$full_CC $*"
  AC_MSG_RESULT([$full_CC])
fi

# Libtool's default ar program is "false", which produces puzzling
# "Error 1" messages  when trying to build on a system lacking ar.
# We therefore preemptively check for ar with a default of "ar" so
# we can at least get a "command not found" error message.
AC_CHECK_TOOL([AR], [ar], [ar])
# Skip all of Libtool's checks for C++ and Fortran.
ac_cv_prog_ac_ct_CXX=no
ac_cv_cxx_compiler_gnu=no
ac_cv_prog_cxx_g=no
ac_cv_prog_ac_ct_F77=no
ac_cv_f77_compiler_gnu=no
ac_cv_prog_f77_g=no
am__fastdepCXX_FALSE='#'
if test "${with_tags+set}" != set; then
  with_tags=
fi
# Initialize and sanity-check Libtool.
AC_PROG_LIBTOOL
AC_SUBST([LIBTOOL_DEPS])
if test `./libtool --features | grep -c 'enable shared'` -ge 1 ; then
  ncptl_run_time_library_is_dynamic=yes
  if test "$lt_cv_prog_cc_can_build_shared" = no ; then
    AC_MSG_WARN([Libtool claims it can build shared libraries while the compiler and/or linker claims it can't; you may need to reconfigure with --disable-shared])
  fi
else
  ncptl_run_time_library_is_dynamic=no
fi
AC_SUBST([LIBTOOL_CURRENT],  [5])  dnl  Most recent library interface supported
AC_SUBST([LIBTOOL_REVISION], [0])  dnl  Interface implementation number
AC_SUBST([LIBTOOL_AGE],      [3])  dnl  Number of older interfaces supported

# Specify the RPM release number.
AC_SUBST([RELEASE], [1])

# ----------------------------------------------------------------------
# ---------------- Define some configure-time options -----------------

# Some versions of the standard C header files require time.h to be included
# before sys/stat.h or sys/stat.h will fail to declare "struct itimerval".
ac_includes_default="#if TIME_WITH_SYS_TIME
# include <sys/time.h>
# include <time.h>
#else
# if HAVE_SYS_TIME_H
#  include <sys/time.h>
# else
#  include <time.h>
# endif
#endif
$ac_includes_default"

# Let the user force a line of code into the list of default includes
# and into an extra_config.h file which is included by config.h.
AC_ARG_WITH([header-code],
  [AC_HELP_STRING([--with-header-code=STRING],
    [force STRING into C header files])],
  [ac_includes_default="$withval
$ac_includes_default"
   AC_MSG_NOTICE([adding `$withval' to extra_config.h])])
cat > extra_config.h <<EXTRA_CONFIG
/* extra_config.h.  Generated by configure. */

/* ----------------------------------------------------------------------
 *
 * coNCePTuaL supplemental configuration-specific header file
 *
 * ----------------------------------------------------------------------
 */

#ifndef _EXTRA_CONFIG_H_
#define _EXTRA_CONFIG_H_

AC_INCLUDES_DEFAULT

#endif
EXTRA_CONFIG

# Let the user prevent the use of arbitrary libraries.
AC_ARG_WITH([ignored-libs],
  [AC_HELP_STRING([--with-ignored-libs=LIBRARIES],
    [don't utilize any of the given libraries (space-separated) even if they're available])],
  [ignored_libs="$ignored_libs $withval"])

# Let the user prevent the use of getopt_long.
AC_ARG_ENABLE([getopt-long],
  [AC_HELP_STRING([--disable-getopt-long],
    [don't parse the command line with getopt_long, even if it's available])],
  [USE_GETOPT_LONG=no],
  [USE_GETOPT_LONG=yes])

# Let the user inhibit building libncptlmodule.so.
AC_ARG_ENABLE([pymodule],
  [AC_HELP_STRING([--disable-pymodule],
    [don't build a Python interface to the coNCePTuaL run-time library, even if we can])],
  [BUILD_PYMODULE=no],
  [BUILD_PYMODULE=yes])

# Let the user prevent HPET from being used as the timer mechanism
# even if it's available.
AC_ARG_ENABLE([hpet],
  [AC_HELP_STRING([--enable-hpet=DEVICE or
  --disable-hpet],
    [specify the High-Precision Event Timer (HPET) device to use or inhibit the use of HPET [/dev/hpet]])],
  [hpet_device=$enableval],
  [hpet_device=/dev/hpet])
if test "$hpet_device" != no ; then
  AC_DEFINE_UNQUOTED([HPET_DEVICE],
    ["$hpet_device"],
    [Define as a memory-mappable HPET device.])
fi

# Let the user force the use of gettimeofday() in ncptl_time().
AC_ARG_WITH([gettimeofday],
  [AC_HELP_STRING([--with-gettimeofday],
    [force the use of gettimeofday(), even if another microsecond timer is available])],
  [FORCE_GETTIMEOFDAY=yes],
  [FORCE_GETTIMEOFDAY=no])
if test "$FORCE_GETTIMEOFDAY" = yes ; then
  AC_DEFINE([FORCE_GETTIMEOFDAY], ,
    [Define if the microsecond timer should be forced to use gettimeofday().])
fi

# Let the user force the use of MPI_Wtime() in ncptl_time().
AC_ARG_WITH([mpi-wtime],
  [AC_HELP_STRING([--with-mpi-wtime],
    [force the use of MPI_Wtime(), even if another microsecond timer is available])],
  [FORCE_MPI_WTIME=yes],
  [FORCE_MPI_WTIME=no])
if test "$FORCE_MPI_WTIME" = yes ; then
  AC_DEFINE([FORCE_MPI_WTIME], ,
    [Define if the microsecond timer should be forced to use MPI_Wtime().])
fi

# The user can't force two different ncptl_time() timers at once.
if test "$FORCE_GETTIMEOFDAY" = yes -a "$FORCE_MPI_WTIME" = yes ; then
  AC_MSG_ERROR([the --with-gettimeofday and --with-mpi-wtime options are mutually exclusive])
fi

# Let the user disable the use of all functions that invoke fork(),
# including, for example, popen() and system().  This is important for
# early InfiniBand software stacks that randomly corrupt memory when a
# process spawns a child.
AC_ARG_WITH([fork],
  [AC_HELP_STRING([--without-fork],
    [disable the use of fork(), popen(), system(), and any other process-spawning function])],
  [ac_cv_func_fork_works=no
   ac_cv_func_vfork_works=no])

# Let the user specify the name of the MPI C compiler and library.
AC_ARG_VAR([MPICC],
  [C compiler to use for MPI programs])
AC_ARG_VAR([MPICPPFLAGS],
  [extra C preprocessor flags (e.g., "-I<include dir>") to use when compiling MPI programs])
AC_ARG_VAR([MPICFLAGS],
  [C flags (e.g., "-g -O2") to use when compiling MPI programs])
AC_ARG_VAR([MPILDFLAGS],
  [extra linker flags to use when linking MPI programs])
AC_ARG_VAR([MPILIBS],
  [extra linker arguments to use when linking MPI programs])

# Let the user override the datatype and constant suffix used for ncptl_int.
AC_ARG_WITH([datatype],
  [AC_HELP_STRING([--with-datatype=INTTYPE],
    [designate an integer datatype to use for most variables in a coNCePTuaL program [int64_t]])],
  [NCPTL_INT=$withval],
  [NCPTL_INT=int64_t])
AC_SUBST([NCPTL_INT])
AC_ARG_WITH([const-suffix],
  [AC_HELP_STRING([--with-const-suffix=STRING],
    [designate a suffix to attach to constants of type ncptl_int [LL]])],
  [NCPTL_INT_SUFFIX=$withval],
  [NCPTL_INT_SUFFIX=LL])
AC_DEFINE_UNQUOTED([NCPTL_INT_SUFFIX],
  [$NCPTL_INT_SUFFIX],
  [Define as a suffix to attach to constants of type ncptl_int.])

# Let the user override the printf() conversion specifier used for ncptl_int.
AC_ARG_WITH([printf-format],
  [AC_HELP_STRING([--with-printf-format=STRING],
    [specify a printf() conversion specifier (e.g., "ld" or "lld") to use for outputting a coNCePTuaL integer [PRId64]])],
  [NICS=$withval],
  [NICS=PRId64])
AC_SUBST([NICS])

# Let the user specify a particular datatype alignment.
AC_ARG_WITH([alignment],
  [AC_HELP_STRING([--with-alignment=INTEGER],
    [specify the byte alignment for data [auto]])],
  [data_alignment=$withval])

# Let the user specify a particular OS page size.
AC_ARG_WITH([page-size],
  [AC_HELP_STRING([--with-page-size=INTEGER],
    [specify the operating system's page size in bytes [auto]])],
  [AC_DEFINE_UNQUOTED([OS_PAGE_SIZE],
    [$withval],
    [Define as the operating system's page size in bytes (only if it can't be determined automatically).])])

# Provide a mechanism for the user to force all AM_CONDITIONALS to be true.
maybe_break=break
AC_ARG_ENABLE([broken-components],
  [AC_HELP_STRING([--enable-broken-components],
    [force "make" to attempt to build everything, even things expected to fail])],
  [broken_components=yes
   maybe_break='echo "$as_me: forging ahead because --enable-broken-components was specified" >&2'],
  [broken_components=no])
if test "$maybe_break" = break ; then
  AC_CACHE_CHECK([if "eval break" successfully breaks out of a loop],
    [ax_cv_prog_eval_break_works],
    [for ax_cv_prog_eval_break_works in yes no ; do
       eval break 2>&AS_MESSAGE_LOG_FD
     done])
  if test "$ax_cv_prog_eval_break_works" = no ; then
    maybe_break="ncptl_build_run_time_library=no_but_we_cant_break"
  fi
fi

# Let the user determine if log files should contain information
# from /proc/interrupts.
read_proc_interrupts=yes
if test "$cross_compiling" = no -a ! -f /proc/interrupts ; then
  # If we're not cross compiling and the build system lacks
  # /proc/interrupts, assume the target system lacks /proc/interrupts
  # as well.
  read_proc_interrupts=no
fi
AC_ARG_ENABLE([proc-interrupts],
  [AC_HELP_STRING([--enable-proc-interrupts or
  --disable-proc-interrupts],
    [force or inhibit coNCePTuaL programs from attempting to open /proc/interrupts during initialization [guessed]])],
  [read_proc_interrupts=$enableval])
if test $read_proc_interrupts = yes ; then
  AC_DEFINE([USE_PROC_INTERRUPTS], ,
    [Define if it\'s okay for all processes to attempt to read /proc/interrupts during initialization.])
  AC_MSG_NOTICE([including support for reading /proc/interrupts at initialization time])
else
  AC_MSG_NOTICE([omitting support for /proc/interrupts])
fi

# Remind the user that he can override LIBS.
AC_ARG_VAR([LIBS], [extra libraries to link with])

# Flush the configure cache to disk.
AC_CACHE_SAVE

# ----------------------------------------------------------------------
# ------ Find various programs we need or can take advantage of. -------

# Find a Python interpreter.
AC_ARG_VAR([PYTHON], [name of the Python executable])
AM_PATH_PYTHON([2.2])
if test -z "$PYTHON" ; then
  AC_MSG_ERROR([The coNCePTuaL compiler requires Python])
fi

# Find a Perl interpreter that can handle the ncptl-logextract script.
AC_ARG_VAR([PERL], [name of the Perl executable])
AC_PATH_PROG([PERL], [perl], [no])
if test "$PERL" = no ; then
  ax_cv_prog_perl_logextract=no
  AC_MSG_WARN([The ncptl-logextract script requires Perl])
else
  AC_CACHE_CHECK([if $PERL can run ncptl-logextract],
    [ax_cv_prog_perl_logextract],
    [
      $PERL $srcdir/ncptl-logextract.in --options-tree > /dev/null 2>&1
      if test $? = 0 ; then
        ax_cv_prog_perl_logextract=yes
      else
        _AS_ECHO([$as_me: Perl error message follows:], [AS_MESSAGE_LOG_FD])
        $PERL $srcdir/ncptl-logextract.in --options-tree 1>&AS_MESSAGE_LOG_FD 2>&AS_MESSAGE_LOG_FD
        ax_cv_prog_perl_logextract=no
      fi
    ])
  if test "$ax_cv_prog_perl_logextract" = no ; then
    AC_MSG_WARN([You will not be able to run ncptl-logextract on this system])
  fi
fi
AM_CONDITIONAL([LOGEXTRACT_WORKS], [test "$ax_cv_prog_perl_logextract" = yes])
LOGEXTRACT_KEYWORDS=logextract_keywords
AC_SUBST_FILE([LOGEXTRACT_KEYWORDS])

# Determine how to get a list of dynamically loaded libraries.
dynlib_cmd_fmt=no
dynlib_ext=no
AC_PATH_PROG([LDD], [ldd], [no])
if test "$ac_cv_path_LDD" != no ; then
  dynlib_cmd_fmt="$ac_cv_path_LDD %s 2>/dev/null"
  dynlib_ext=".so"
else
  AC_PATH_PROG([OTOOL], [otool], [no])
  if test "$ac_cv_path_OTOOL" != no ; then
    dynlib_cmd_fmt="$ac_cv_path_OTOOL -L %s 2>/dev/null"
    dynlib_ext=".dylib"
  fi
fi
if test "$dynlib_cmd_fmt" != no -a "$dl_string" != no ; then
  AC_DEFINE_UNQUOTED([DYNLIB_CMD_FMT],
    ["$dynlib_cmd_fmt"],
    [Define as a template for a Bourne-shell command that gets a list of shared objects.])
  AC_DEFINE_UNQUOTED([DYNLIB_EXT],
    ["$dynlib_ext"],
    [Define as the file extension (including the leading ".") of a dynamic library])
fi

# Abort if we don't have AWK (as is the case for default installation
# of the Syllable OS, at least version 0.6.4).
AC_PROG_AWK
if test "$AWK" = "" ; then
  AC_MSG_ERROR([$PACKAGE_NAME can't build without an AWK interpreter])
fi

# See if we have a working SWIG and, if not, if the supplied
# libncptl_wrap.c.in is compatible with our version of Python.
AC_PATH_PROG([SWIG], [swig], [no])
if test "$SWIG" != no ; then
  AC_CACHE_CHECK([if swig works],
    [ax_cv_prog_swig_works],
    [ax_cv_prog_swig_works=no
     echo "int dummyvar = 123;" > conftest.i
     $SWIG -python -module conftest conftest.i > /dev/null 2>&1
     if test $? = 0 ; then
       ax_cv_prog_swig_works=yes
     fi
     rm -f conftest*])
  if test "$ax_cv_prog_swig_works" = yes ; then
    AC_DEFINE([SWIG_WORKS], ,
      [Define if `swig' is usable.])
  fi
fi
AM_CONDITIONAL([HAVE_SWIG], [test "$ax_cv_prog_swig_works" = yes])
if test "$SWIG" = no -o "$ax_cv_prog_swig_works" = no ; then
  AC_CACHE_CHECK([the version of SWIG which produced libncptl_wrap.c.in],
    [ax_cv_prog_swig_version],
    [ax_cv_prog_swig_version=`cat $srcdir/libncptl_wrap.c.in | $AWK '/Version/ {print $3}'`])
  if $AWK 'END {if (0+SWIGVER>1.1 && 0+PYVER<2.0) exit 0; exit 1}' SWIGVER=$ax_cv_prog_swig_version PYVER=$PYTHON_VERSION /dev/null ; then
    AC_MSG_WARN([SWIG v$ax_cv_prog_swig_version is unlikely to work with Python v$PYTHON_VERSION; you may need to reconfigure with --disable-pymodule])
  fi
else
  AC_CACHE_CHECK([swig version],
    [ax_cv_prog_swig_version],
    [ax_cv_prog_swig_version=`$SWIG -version 2>&1 | $AWK '/Version/ {print [$]3}'`])
fi
SWIGVERSION=$ax_cv_prog_swig_version
AC_SUBST([SWIGVERSION])
SWIGFLAGS=`$AWK 'END {if (0+SWIGVER>=1.3) print "-addextern"; else print "-dnone"}' SWIGVER=$SWIGVERSION /dev/null`
AC_SUBST([SWIGFLAGS])

# See if the compiler used to build Python extensions is compatible
# with the compiler used to build C libraries.
PYTHON_MAKEFILE=`_AC_EVAL_STDERR(["$PYTHON -c 'from distutils.sysconfig import *; print get_makefile_filename()'"])`
if test "$ac_status" -eq 0 -a "$PYTHON_MAKEFILE" -a -f "$PYTHON_MAKEFILE" ; then
  AX_PYTHON_C_COMPATIBILITY(,
    [BUILD_PYMODULE=no_not_compatible
     PYTHON_CC=`$PYTHON -c 'from distutils.sysconfig import *; print get_config_var("CC")'`])
else
  BUILD_PYMODULE=no_no_makefile
  PYTHON_MAKEFILE=${PYTHON_MAKEFILE:-config/Makefile}
fi

# See if jar exists and supports the -e option.
AC_CHECK_PROGS([JAR], [jar], [no])
if test "$ac_cv_prog_JAR" = no ; then
  JAR=jar
else
  AC_CACHE_CHECK([if $JAR supports -e],
    [ax_cv_prog_jar_e],
    [touch conftest.dat
     if $JAR cfe conftest.jar gov.lanl.c3.conftest conftest.dat > /dev/null 2>&1 ; then
       ax_cv_prog_jar_e=yes
     else
       ax_cv_prog_jar_e=no
     fi])
fi
AM_CONDITIONAL([JAR_SUPPORTS_E], [test "$ax_cv_prog_jar_e" = yes])

# Find some other useful tools.
AC_PROG_CPP
AC_PROG_LN_S
AC_PATH_PROG([JYTHONC], [jythonc], [jythonc])
AC_CHECK_PROGS([JAVAC], [javac jikes guavac], [javac])
AM_PATH_LISPDIR
AC_PATH_PROG([GPERF], [gperf], [no])
if test "$ac_cv_path_GPERF" != no ; then
  AC_CACHE_CHECK([if gperf is sufficiently recent],
    [ax_cv_prog_gperf_recent],
    [if test `echo Testing | \
         $ac_cv_path_GPERF --key-positions="*" --includes --language=ANSI-C \
           --initializer-suffix=", 0" --lookup-fn-name=ncptl_sig2num --enum 2>&1 |
         grep -c -i unrecognized` -eq 0 ; then
       ax_cv_prog_gperf_recent=yes
     else
       ax_cv_prog_gperf_recent=no
     fi])
fi
AM_CONDITIONAL([HAVE_GPERF],
  [test "$ac_cv_path_GPERF" != no -a "$ax_cv_prog_gperf_recent" = yes])
AC_PATH_PROG([GS], [gs], [gs])
AC_PATH_PROG([DOT], [dot], [no])
AM_CONDITIONAL([HAVE_DOT], [test "$ac_cv_path_DOT" != no])
if test "$ac_cv_path_DOT" = no ; then
  DOT=dot
fi
AC_PATH_PROG([HTMLTIDY], [tidy], [echo])
if test "$ac_cv_path_HTMLTIDY" != echo ; then
  HTMLTIDY="${HTMLTIDY} -asxml -modify"
fi
AC_CHECK_PROGS([TEX], [etex tex], [no])
AM_CONDITIONAL([HAVE_TEX], [test "$TEX" != no])
if test "$TEX" = no ; then
  TEX=tex
  LATEX=latex
  PDFTEX=pdftex
else
  AC_CHECK_PROGS([LATEX], [elatex latex], [no])
  AC_CHECK_PROGS([PDFTEX], [pdfetex pdftex], [pdftex])
fi
AC_CHECK_PROGS([INDENT], [indent], [no])
AC_CHECK_PROGS([MSGDIGEST], [sha512sum sha1sum md5sum], [no])
AM_CONDITIONAL([HAVE_MSGDIGEST], [test "$MSGDIGEST" != no])
AC_CHECK_PROGS([MAKEPACKAGE], [makepackage makeinstaller], [makepackage])
AC_CHECK_PROGS([PKGCONFIG], [pkg-config], [:])
if test "$ncptl_run_time_library_is_dynamic" = yes -a \
        "$ac_cv_path_LDD" != no ; then
  AC_CACHE_CHECK([for the name of the dynamic linker],
    [ax_cv_prog_ld_so],
    [ax_cv_prog_ld_so=`$ac_cv_path_LDD /bin/sh 2>&1 | $AWK '/ld.*\.so/ {print $1}; END {print "/lib/ld.so"}' | head -1`])
fi
AC_DEFINE_UNQUOTED([DYNAMIC_LINKER],
  ["$ax_cv_prog_ld_so"],
  [Define as the name of the dynamic linker.])

# Define the complete backend list for use with --enable-broken-components.
ALL_BACKENDS="codegen_c_mpi.py codegen_c_generic.py codegen_c_udgram.py \
              codegen_c_trace.py codegen_c_seq.py codegen_dot_ast.py    \
              codegen_interpret.py codegen_picl.py codegen_latex_vis.py \
              codegen_c_profile.py codegen_c_stats.py"

# Assume we can build only the DOT parse-tree backend.
BACKENDS=codegen_dot_ast.py

# Flush the configure cache to disk.
AC_CACHE_SAVE

# ----------------------------------------------------------------------
# -------------- See if we can build the run-time library --------------

ncptl_build_run_time_library=no

while true ; do
  # Determine if AM_PROG_CC_STDC was able to provide us with an ANSI
  # C compiler, ANSI C header files, and an ANSI C preprocessor.
  AC_CACHE_CHECK([if $CC supports some basic ANSI C features],
    [ax_cv_prog_cc_ansic],
    [AC_TRY_COMPILE([
/* The following file is required by ANSI C but absent from pre-ANSI C. */
#include <stdarg.h>

/* Pre-ANSI C should choke on the following. */
void *kill_pre_ansi_c (const char *somestring, const int somenumber)
{
  return (void *)(somestring+somenumber);
}
      ],
      [
/* Pre-ANSI C lacked volatile and the preprocessor lacked string
 * concatenation. */
volatile void *try_to_kill = kill_pre_ansi_c ("Die, old" " C compilers!", 123);
      ],
      [ax_cv_prog_cc_ansic=yes],
      [ax_cv_prog_cc_ansic=no])])
  if test "$ax_cv_prog_cc_ansic" != yes ; then
    AC_MSG_WARN([AC_PACKAGE_NAME's run-time library requires ANSI C])
    eval $maybe_break
  fi
  AC_C_CONST
  AC_C_INLINE

  # Ensure that libtool isn't completely broken.
  AX_PROG_LIBTOOL_WORKS(, [eval $maybe_break])

  # Find a library (and headers) for parsing the command line.
  USE_POPT=no
  # Step 1: Check for popt.
  AC_CHECK_HEADER([popt.h])
  if test "$ac_cv_header_popt_h" = yes ; then
    AX_CHECK_LIB([popt], [poptGetContext])
    if test "$ac_cv_lib_popt_poptGetContext" = yes ; then
      USE_POPT=yes
      AC_DEFINE([USE_POPT], ,
        [Define if popt should be used to parse the command line.])
    fi
  fi
  if test "$USE_POPT" = no ; then
    # Step 2: Check for getopt_long.
    AC_CHECK_HEADERS([gnugetopt.h getopt.h])
    if test "$USE_GETOPT_LONG" = yes ; then
      USE_GETOPT_LONG=no
      if test "$ac_cv_header_getopt_h" = yes -o \
              "$ac_cv_header_gnugetopt_h" = yes ; then
        AX_CHECK_LIB([gnugetopt], [getopt_long])
        AC_CHECK_FUNCS([getopt_long])
        if test "$ac_cv_func_getopt_long" = yes ; then
          USE_GETOPT_LONG=yes
          AC_DEFINE([USE_GETOPT_LONG], ,
            [Define if getopt_long should be used to parse the command line.])
        fi
      fi
    fi
    if test "$USE_GETOPT_LONG" = no ; then
      # Step 3: Check for getopt.
      AC_CHECK_FUNCS([getopt])
      if test "$ac_cv_func_getopt" = no ; then
        eval $maybe_break
      fi
    fi
  fi

  # Look for a way to read the program's original command line (as
  # argv[] may be modified by, say, MPI_Init()).
  AX_FILE_PROC_CMDLINE

  # Check for libraries, functions, and headers that we need/want.
  for ax_func in log10 floor ceil sqrt trunc ; do
    AX_CHECK_REQUIRES_LIBM([$ax_func],
      [volatile double have_$ax_func = $ax_func(1.0);])
  done
  for ax_func in pow fmod ; do
    AX_CHECK_REQUIRES_LIBM([$ax_func],
      [volatile double have_$ax_func = $ax_func(1.0, 2.0);])
  done
  AC_CHECK_FUNCS([setitimer], ,
    [AC_MSG_WARN([Using the FOR <time> construct will result in a run-time error])])
  AC_CHECK_FUNCS([getrusage], ,
    [AC_MSG_WARN([Log files will not report process resource utilization])])
  AX_SEARCH_LIBS([nanosleep], [rt],
    [AC_CHECK_FUNCS([nanosleep])],
    [AC_MSG_WARN([The SLEEPS FOR construct will produce a run-time error])])
  AC_CHECK_FUNCS([getpwuid])
  AC_CHECK_TYPES([ssize_t])
  AX_REQUIRE_ONE_FUNC([vfprintf], , [eval $maybe_break])
  AC_CHECK_FUNCS([getpagesize sysconf])
  AX_REQUIRE_ONE_FUNC([time], , [eval $maybe_break])
  AX_REQUIRE_ONE_FUNC([sigaction signal], , [eval $maybe_break])
  AX_REQUIRE_ONE_FUNC([strtok], , [eval $maybe_break])
  AC_TYPE_SIGNAL
  RETSIGVALUE=
  if test "$ac_cv_type_signal" != void ; then
    RETSIGVALUE="(RETSIGTYPE) 0"
  fi
  AC_DEFINE_UNQUOTED([RETSIGVALUE], [$RETSIGVALUE],
    [Define as a value that a signal handler should return.])
  AC_CHECK_HEADERS([unistd.h time.h sys/time.h signal.h errno.h sys/mman.h])
  if test "$ac_cv_header_signal_h" = no -o \
          "$ac_cv_errno_h" = no ; then
    eval $maybe_break
  fi
  AC_CHECK_HEADERS([sys/utsname.h sys/resource.h sys/select.h ieeefp.h])
  AC_HEADER_TIME
  AC_CHECK_FUNCS([strerror uname llabs cbrt strsignal])
  if test "$ac_cv_func_strerror" = yes ; then
    AC_CHECK_DECLS([strsignal], , ,
      [
#if defined(__GNUC__) && !defined(_GNU_SOURCE)
# define _GNU_SOURCE
#endif
#ifdef HAVE_STRING_H
# include <string.h>
#endif
      ])
  fi
  AC_CHECK_DECLS([sys_errlist])
  AC_TYPE_UID_T
  # The installation of OpenBSD 3.5 I tested lacks a trunc() function,
  # as does Microsoft Windows.
  AX_REQUIRE_ONE_FUNC([trunc floor fmod], , [eval $maybe_break])
  AC_CHECK_FUNCS([popen])
  AC_CHECK_HEADERS([sys/wait.h])
  AC_CHECK_HEADERS([sys/sysmp.h])
  AC_CHECK_FUNCS([sysmp])
  AX_FUNC_VA_COPY
  AC_CHECK_HEADERS([uuid/uuid.h],
    [AX_CHECK_LIB([uuid], [uuid_unparse])])
  # The Cell BE's SPUs lack a getcwd() function.
  AC_CHECK_FUNCS([getcwd])
  AC_CHECK_FUNCS([sched_getaffinity])
  if test "$ac_cv_func_sched_getaffinity" = yes ; then
    AC_CHECK_HEADERS([sched.h])
  fi

  # Flush the configure cache to disk.
  AC_CACHE_SAVE

  # Check for some relatively obscure features.
  AC_MSG_NOTICE([checking for various network- and machine-specific features])

  # Check for QsNet features.
  AC_CHECK_HEADER([rms/rmscall.h],
    [AX_CHECK_LIB([rmscall], [rms_getcap],
      [# Preclude ancient distributions of Quadrics's software.
       AC_CHECK_MEMBERS([ELAN_CAPABILITY.cap_version],
         [LIBS="-lrmscall -lelan $LIBS"
          AC_DEFINE([HAVE_LIBELAN], ,
            [Define if QsNet Elan information is available.])],
         ,
         [#include <rms/rmscall.h>])])])

  # Check for BlueGene/P features.
  AC_CHECK_HEADERS([common/bgp_personality.h],
    [AX_CHECK_LIB([SPI.cna], [Kernel_GetPersonality],
       [LIBS="-lSPI.cna $LIBS"
        AC_DEFINE([HAVE_BGPPERSONALITY], ,
          [Define if BlueGene/P personality information is available.])])])

  # Check for BlueGene/L features.
  AC_CHECK_HEADER([bglpersonality.h],
    [AX_CHECK_LIB([rts.rts], [rts_get_personality],
       [LIBS="-lrts.rts -ldevices.rts $LIBS"
        AC_DEFINE([HAVE_BGLPERSONALITY], ,
          [Define if BlueGene/L personality information is available.])],
       ,
       [-ldevices.rts])])

  # Check for Cray XT features.
  AC_CACHE_CHECK([if _my_pnid is defined],
    [ax_cv_var__my_pnid],
    [AC_TRY_LINK(,
      [extern unsigned int _my_pnid; _my_pnid=0;],
      [ax_cv_var__my_pnid=yes],
      [ax_cv_var__my_pnid=no])])
  if test "$ax_cv_var__my_pnid" = yes ; then
    AC_DEFINE([HAVE__MY_PNID], ,
      [Define if the Cray XT node ID is available in _my_pnid.])
    AC_CHECK_HEADERS([rsms/rs_id.h],
      [AX_SEARCH_LIBS([rs_format_phys],
        [rsmsevent],
        [AC_DEFINE([HAVE_RSMSEVENT], ,
           [Define if Cray XT event data is available.])])])
    AC_CHECK_HEADERS([rca_lib.h rsms/rs_meshcoord.h])
    if test "$ac_cv_header_rca_lib_h" = yes -a "$ac_cv_header_rsms_rs_meshcoord_h" = yes ; then
      AX_SEARCH_LIBS([rca_get_meshcoord],
        [rca],
        [AC_DEFINE([HAVE_RCAMESHCOORD], ,
           [Define if Cray XT mesh coordinates are available.])])
    fi
    AC_CACHE_CHECK([if __cpu_mhz is defined],
      [ax_cv_var___cpu_mhz],
      [AC_TRY_LINK(,
        [extern unsigned int __cpu_mhz; __cpu_mhz=0;],
        [ax_cv_var___cpu_mhz=yes],
        [ax_cv_var___cpu_mhz=no])])
    if test "$ax_cv_var___cpu_mhz" = yes ; then
      AC_DEFINE([HAVE___CPU_MHZ], ,
        [Define if the Cray XT clock frequency is available in __cpu_mhz.])
    fi
  fi

  # Check for SGI features.
  AC_CHECK_HEADERS([sys/syssgi.h invent.h])
  AC_CHECK_FUNCS([syssgi getinvent])

  # Check for AIX features.
  AC_CHECK_HEADERS([odmi.h cf.h sys/cfgodm.h])
  AC_CHECK_MEMBER([struct CuAt.name],
    [AC_DEFINE([HAVE_STRUCT_CUAT], ,
      [Define if you have the `CuAt' struct.])
     AX_CHECK_LIB([odm], [odm_initialize])
     AX_CHECK_LIB([cfg], [getattr])],
    ,
    [
#ifdef HAVE_ODMI_H
# include <odmi.h>
#endif
#ifdef HAVE_CF_H
# include <cf.h>
#endif
#ifdef HAVE_SYS_CFGODM_H
# include <sys/cfgodm.h>
#endif
    ])

  # Check for OpenIB InfiniBand headers and libraries.
  AC_CHECK_HEADERS([infiniband/verbs.h],
    [AX_CHECK_LIB([sysfs], [sysfs_open_class])
     AX_CHECK_LIB([ibverbs], [ibv_query_device])
     AX_REQUIRE_ONE_FUNC([ibv_get_device_list ibv_get_devices],
       [AC_DEFINE([HAVE_OPENIB], ,
         [Define if OpenIB headers and library files are available.])])])

  # The C compiler on ASCI Red claims to support ANSI C but lacks a
  # number of symbols and functions which coNCePTuaL expects to find.
  AX_CHECK_SYMBOLS([optopt getppid], [int], [
#if defined(HAVE_GETOPT_H)
# include <getopt.h>
#endif])
  AX_CHECK_SYMBOLS([environ], [char **])
  AC_CHECK_FUNCS([realpath])
  AX_REQUIRE_ONE_FUNC([vsnprintf vsprintf], , [eval $maybe_break])

  # Check for the PCI Utilities interface to the PCI bus.
  AC_CHECK_HEADERS([pci/pci.h],
    [AX_SEARCH_LIBS([pci_scan_bus],
      [pci pciutils],
      [AC_DEFINE([HAVE_PCIUTILS],
        ,
        [Define if you have the PCI Utilities library (-lpci or -lpciutils)])])])

  # Check for the Hardware Abstraction Layer interface to hardware
  # characteristics.
  prev_CPPFLAGS="$CPPFLAGS"
  prev_CFLAGS="$CFLAGS"
  prev_LDFLAGS="$LDFLAGS"
  prev_LIBS="$LIBS"
  CPPFLAGS="$CPPFLAGS `$PKGCONFIG --silence-errors --cflags-only-I hal`"
  CFLAGS="`$PKGCONFIG --silence-errors --cflags-only-other hal` $CFLAGS"
  LDFLAGS="$LDFLAGS `$PKGCONFIG --silence-errors --libs-only-L hal`"
  LDFLAGS="$LDFLAGS `$PKGCONFIG --silence-errors --libs-only-other hal`"
  LIBS="$LIBS `$PKGCONFIG --silence-errors --libs-only-l hal`"
  AC_CHECK_HEADERS([libhal.h],
    [AX_CHECK_LIB([hal], [libhal_ctx_init],
      [AC_DEFINE([HAVE_HAL], ,
        [Define if the Hardware Abstraction Layer headers and libraries are available.])])])
  if test "$ac_cv_lib_hal_libhal_ctx_init" != yes ; then
    LIBS="$prev_LIBS"
    LDFLAGS="$prev_LDFLAGS"
    CFLAGS="$prev_CFLAGS"
    CPPFLAGS="$prev_CPPFLAGS"
  fi

  # Check if we can explicitly stick a symbol into an ELF object's .interp
  # section.  Note that we pass the symbol and function declarations in
  # AC_TRY_LINK's INCLUDE argument, not its BODY argument, because section
  # attributes aren't allowed within function bodies.
  if test "$enable_shared" = yes ; then
    AC_CACHE_CHECK([if we can store symbols in .interp],
      [ax_cv_prog_ld_interp],
      [prev_LDFLAGS="$LDFLAGS"
       LDFLAGS="$LDFLAGS -Wl,-e,lib_entry_point"
       AC_TRY_LINK([
  char ldso[] __attribute__((section(".interp"))) = "/lib/ld.so";

  void lib_entry_point (void)
  {
    exit (0);
  }
	 ],
	 ,
	 [ax_cv_prog_ld_interp=yes],
	 [ax_cv_prog_ld_interp=no])
       LDFLAGS="$prev_LDFLAGS"])
    if test "$ax_cv_prog_ld_interp" = yes ; then
      AC_DEFINE([CAN_WRITE_INTERP], ,
	[Define if the compiler and linker can write explicitly into the target binary's .interp section.])
      AC_SUBST([LIBRARY_ENTRY_POINT], [-Wl,-e,ncptl_log_output_dataless_log])
    fi
  fi

  # Flush the configure cache to disk.
  AC_CACHE_SAVE

  # Find unsigned {8,16,32,64}-bit datatypes, a signed 64-bit datatype,
  # and an unsigned integer type with the same size as a pointer.
  AC_MSG_NOTICE([checking for definitions of various integer datatypes])
  AC_CHECK_HEADERS([inttypes.h stdint.h sys/types.h])
  AC_DEFINE_INTEGER_BITS([uint8_t],
    [u_int8_t], [unsigned char], [unsigned __int8])
  if test "$uint8_t" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_INTEGER_BITS([uint16_t],
    [u_int16_t], [unsigned short], [unsigned __int16])
  if test "$uint16_t" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_INTEGER_BITS([uint32_t],
    [u_int32_t], [unsigned int], [unsigned __int32])
  if test "$uint32_t" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_INTEGER_BITS([uint64_t],
    [u_int64_t], [unsigned long long], [unsigned __int64], [unsigned long])
  if test "$uint64_t" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_INTEGER_BITS([int64_t],
    [long long], [__int64], [long])
  if test "$int64_t" = no ; then
    eval $maybe_break
  fi
  AC_CHECK_TYPE([uintptr_t], , [eval $maybe_break])

  # Find an unsigned 128-bit datatype.  Because such a datatype is
  # currently rather rare and because the run-time library needs a 128-bit
  # datatype only to touch 128-bit dummy values, we also check for "long
  # double" and finally settle on a 128-bit struct.
  AC_DEFINE_INTEGER_BITS([uint128_t],
    [u_int128_t], [unsigned long long long], [unsigned __int128], [long double])
  if test "$uint128_t" = no ; then
    AC_DEFINE([MUST_FAKE_UINT128], ,
      [Define if a uint128_t must be fabricated out of two uint64_t values.])
  fi

  # We need to be able to convert a string to an ncptl_int.  If strtoll(),
  # strtoq(), and _strtoi64() are all unavailable (e.g., when using the
  # native Alpha C compiler), we can still use strtol() if a long is both
  # large enough to contain an ncptl_int and at least 64 bits in size.
  AX_REQUIRE_ONE_FUNC([strtoll strtoq _strtoi64], ,
    [AC_MSG_NOTICE([checking if strtol can serve as a replacement for strtoll])
     AX_REQUIRE_ONE_FUNC([strtol], , [eval $maybe_break])
     AC_CACHE_CHECK([if a long can hold both an int64_t and an ncptl_int type],
       [ax_cv_type_long_big_enough],
       [AC_TRY_RUN([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif

int
main()
{
  return !(sizeof(long) >= sizeof($NCPTL_INT) && sizeof(long) >= 8);
}
         ],
         [ax_cv_type_long_big_enough=yes],
         [ax_cv_type_long_big_enough=no],
         [ax_cv_type_long_big_enough=yes])])
     if test "$ax_cv_type_long_big_enough" = yes ; then
       AC_DEFINE([STRTOL_IS_STRTOLL], ,
         [Define if `strtol' can correctly take the place of `strtoll'.])
     else
       eval $maybe_break
     fi])

  # Find a function for reading a high-resolution timer.
  if test "$FORCE_GETTIMEOFDAY" = yes ; then
    AX_REQUIRE_ONE_FUNC([gettimeofday], ,
      [AC_MSG_WARN([The --with-gettimeofday option was specified but the gettimeofday function is not available])
       break])
  elif test "$FORCE_MPI_WTIME" = yes ; then
    AX_REQUIRE_ONE_FUNC([MPI_Wtime], ,
      [AC_MSG_WARN([The --with-mpi-wtime option was specified but the MPI_Wtime function is not available])
       break])
  else
    AX_FIND_HI_RES_TIMER(, [eval $maybe_break])
  fi
  if false ; then
    # Include a template in config.h for the user's convenience.
    AC_DEFINE([CYCLES_PER_USEC], ,
      [Define as the number of times the cycle counter increments per microsecond (often equal to the clock speed in MHz).])
  fi

  # By this point in the configuration process we should have
  # checked for all of the libraries we need.  We now check that we can
  # not only link a trivial program but run it as well.  This detects a
  # problem I encountered in which /usr/local/bin/gcc was able to locate
  # /usr/local/lib/libpopt.so.0 but no programs could be run because
  # /usr/local/lib was not in the LD_LIBRARY_PATH.  The problem manifested
  # itself as configure being unable to determine the number of words of
  # random-number-generator state -- a test that needs to run a generated
  # program.
  AC_MSG_CHECKING([if we can run a trivial program linked with \"$LIBS\"])
  AC_TRY_RUN([
int
main (int argc, char *argv[])
{
  return 0;
}],
    [AC_MSG_RESULT([yes])],
    [AC_MSG_RESULT([no])
     eval $maybe_break],
    [AC_MSG_RESULT([N/A])])

  # Ensure that NCPTL_INT_SUFFIX is valid.
  AC_CACHE_CHECK([if $NCPTL_INT_SUFFIX is a valid suffix for an ncptl_int constant],
    [ax_cv_decl_suffix_valid],
    [AC_TRY_RUN([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#include <stdarg.h>

typedef $NCPTL_INT ncptl_int;

#define VAL0 0x10203040$NCPTL_INT_SUFFIX
#define VAL1 0xFEEF1F00$NCPTL_INT_SUFFIX

int
check_stdarg (int dummy, ...)
{
  va_list ap;
  ncptl_int params[2];

  va_start (ap, dummy);
  params[0] = va_arg (ap, ncptl_int);
  params[1] = va_arg (ap, ncptl_int);
  va_end (ap);
  return !(params[0]==VAL0 && params[1]==VAL1);
}

int
main (int argc, char *argv[])
{
  return check_stdarg (123, VAL0, VAL1);
}
      ],
    [ax_cv_decl_suffix_valid=yes],
    [ax_cv_decl_suffix_valid=no],
    [ax_cv_decl_suffix_valid=yes])])
  if test "$ax_cv_decl_suffix_valid" != yes ; then
    AC_MSG_WARN(["$NCPTL_INT_SUFFIX" is not a valid suffix for a constant of type $NCPTL_INT])
    eval $maybe_break
  fi

  # Ensure that NICS is valid.
  AC_CACHE_CHECK([if $NICS is a valid printf conversion specifier for ncptl_int],
    [ax_cv_const_nics_valid],
    [AC_TRY_COMPILE([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#include <stdio.h>
      ],
      [
$NCPTL_INT somenum = -12345$NCPTL_INT_SUFFIX;
printf ("I like the number %" $NICS " -- do you?\n", somenum);
      ],
      [ax_cv_const_nics_valid=yes],
      [ax_cv_const_nics_valid=no])])
  if test "$ax_cv_const_nics_valid" != yes ; then
    AC_MSG_WARN([$NICS is not a valid printf conversion specifier for values of type $NCPTL_INT])
    eval $maybe_break
  fi

  # Determine the minimum (i.e., most negative) ncptl_int value.
  AC_CACHE_CHECK([if we can find the minimum ncptl_int value],
    [ax_cv_type_ncptl_int_min],
    [AC_TRY_RUN([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#include <stdio.h>

typedef $NCPTL_INT ncptl_int;

int
main (int argc, char *argv[])
{
  if (argc > 1)
    printf ("(-%" $NICS "$NCPTL_INT_SUFFIX-1)\n",
            ((ncptl_int)1 << (8*sizeof(ncptl_int)-1)) - 1);
  return 0;
}
     ],
     [ax_cv_type_ncptl_int_min=`./conftest$ac_exeext show`],
     [ax_cv_type_ncptl_int_min=no],
     [ax_cv_type_ncptl_int_min="(INT64_C(-9223372036854775807)-1)"])])
  if test "$ax_cv_type_ncptl_int_min" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_UNQUOTED([NCPTL_INT_MIN],
    [$ax_cv_type_ncptl_int_min],
    [Define as the minimum (i.e., most negative) value an ncptl_int can accept.])

  # Find a rounding function.  The Cray C compiler I tested has
  # round() but it appears to be an identity function.  Weird.
  # If none of rint(), nearbyint(), and round() works we can define
  # rounding in terms of trunc() (whose existence was previously tested).
  AC_CHECK_FUNCS([rint nearbyint round])
  if test "$ac_cv_func_round" = yes ; then
    AC_CACHE_CHECK([if round is likely to work],
      [ax_cv_func_round_works],
      [AC_TRY_RUN([
#include <math.h>

int
main (void)
{
  double number = 444.4;

  return number-round(number) < 0.3;
}
        ],
        [ax_cv_func_round_works=yes],
        [ax_cv_func_round_works=no],
        [ax_cv_func_round_works=yes])])
    if test "$ax_cv_func_round_works" = yes ; then
      AC_DEFINE([ROUND_WORKS], ,
        [Define if the `round' function is likely to work.])
    fi
  fi

  # Figure out whether to use PATH_MAX, MAXPATHLEN, or FILENAME_MAX.
  AC_CHECK_HEADERS([sys/param.h])
  AC_CACHE_CHECK([what the maximum pathname length is called],
    [ac_cv_decl_path_max],
    [ac_cv_decl_path_max=no
     for path_max_name in PATH_MAX MAXPATHLEN FILENAME_MAX ; do
     AC_EGREP_CPP([yes],
       [
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#ifdef HAVE_SYS_PARAM_H
# include <sys/param.h>
#endif
#ifdef $path_max_name
  yes
#endif
       ],
       [ac_cv_decl_path_max=$path_max_name ; break])
     done])
  if test "$ac_cv_decl_path_max" = no ; then
    eval $maybe_break
  fi
  AC_DEFINE_UNQUOTED([PATH_MAX_VAR], [$ac_cv_decl_path_max],
    [Define as PATH_MAX, MAXPATHLEN, or whatever else refers to the
     maximum filename size in characters.])

  # Perform a number of checks needed for MinGW (and possibly other
  # compilers which target Microsoft Windows).  Ideally, we should also
  # check for QueryPerformanceCounter() but the link-time argument check
  # thwarts Autoconf's attempts to find this symbol.
  AC_CHECK_HEADERS([windows.h pwd.h])
  AC_CHECK_FUNCS([kill sleep getuid geteuid])

  # Figure out whether to use HOST_NAME_MAX or MAXHOSTNAMELEN and
  # whether we can use gethostbyname().
  AC_CHECK_HEADERS([netdb.h],
    [AC_CHECK_MEMBERS([struct hostent.h_name],
      [AC_CHECK_FUNCS([gethostbyname])],
      ,
      [#include <netdb.h>])])
  if test "$ac_cv_header_sys_utsname_h" = no -o "$ac_cv_func_uname" = no ; then
    AC_CACHE_CHECK([what the maximum hostname length is called],
      [ac_cv_decl_host_name_max],
      [ac_cv_decl_host_name_max=unknown
       for host_name_max in HOST_NAME_MAX MAXHOSTNAMELEN ; do
       AC_EGREP_CPP([yes],
         [
#if HAVE_UNISTD_H
# include <sys/types.h>
# include <unistd.h>
#endif
#include <limits.h>
#ifdef HAVE_SYS_PARAM_H
# include <sys/param.h>
#endif
#ifdef HAVE_NETDB_H
# include <netdb.h>
#endif
#ifdef $host_name_max
  yes
#endif
         ],
         [ac_cv_decl_host_name_max=$host_name_max ; eval $maybe_break])
       done])
    if test "$ac_cv_decl_host_name_max" != unknown ; then
      AC_DEFINE_UNQUOTED([HOST_NAME_MAX_VAR], [$ac_cv_decl_host_name_max],
        [Define as HOST_NAME_MAX, MAXHOSTNAMELEN, or whatever else refers to the
         maximum hostname size in characters.])
    fi
  fi

  # See if the null device is called NUL: (Windows) or /dev/null (Unix).
  AC_CACHE_CHECK([what the null device is called],
    [ax_cv_sys_null_device],
    [ax_cv_sys_null_device=unknown
     for nulldev in NUL: /dev/null ; do
       if test -w $nulldev ; then
         ax_cv_sys_null_device=$nulldev
         break
       fi
     done])
  if test "$ax_cv_sys_null_device" = unknown ; then
    eval $maybe_break
  fi
  AC_DEFINE_UNQUOTED([NULL_DEVICE_NAME],
    ["$ax_cv_sys_null_device"],
    [Define as the name of a file that discards all data written to it.])

  # Determine how big an MT_STATE struct is so we can define an opaque
  # equivalent.  When cross-compiling, we conservatively assume 64-bit
  # integers.  The typedef appearing in the following must be kept
  # consistent with the one defined in mt19937-64-sdp.c.
  AC_CACHE_CHECK([the number of words of random-number-generator state],
    [ax_cv_type_MT_STATE_size],
    [NNDEFINITION=`grep '#define NN' $srcdir/mt19937-64-sdp.c | sed 's/#define NN//'`
     AC_TRY_RUN([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#include <stdio.h>

typedef struct {
  uint64_t mt[$NNDEFINITION];
  int mti;
} MT_STATE;

int
main (int argc, char *argv[])
{
  if (argc > 1)
    (void) printf ("%d\n", 1+sizeof(MT_STATE)/sizeof(uint64_t));
  return 0;
}],
       [ax_cv_type_MT_STATE_size=`./conftest$ac_exeext show`],
       [ax_cv_type_MT_STATE_size=indeterminate],
       [ax_cv_type_MT_STATE_size=320])])
  if test "$ax_cv_type_MT_STATE_size" = "indeterminate" ; then
    eval $maybe_break
  fi
  AC_DEFINE_UNQUOTED([RNG_STATE_WORDS], [$ax_cv_type_MT_STATE_size],
    [Define as the number of words occupied by an MT_STATE structure.])

  # Find a value that we can pretend is out-of-bounds.
  AC_CACHE_CHECK([for a definition of the largest double value],
    [ax_cv_decl_double_smallest],
    [AC_EGREP_CPP([yes],
      [
#include <math.h>
#include <float.h>

#if defined(MAXDOUBLE) || defined(DBL_MAX)
  yes
#endif
      ],
      [ax_cv_decl_double_smallest=yes],
      [ax_cv_decl_double_smallest=no])])
  if test "$ax_cv_decl_double_smallest" = no ; then
    eval $maybe_break
  fi

  # Now that GCC's #cpu is deprecated, define some macros to
  # indicate the CPU type.
  AC_DEFINE_UNQUOTED([CPU_TYPE], ["$host_cpu"],
    [Define as the name of the CPU on which coNCePTuaL applications will run.])
  case "$host_cpu" in
    alpha*)
      AC_DEFINE([HAVE_ALPHA_CPU], ,
        [Define if we're running on a CPU in the Alpha family.])
    ;;

    i?86)
      AC_DEFINE([HAVE_IA32_CPU], ,
        [Define if we're running on a CPU in the IA-32 family.])
    ;;

    x86_64)
      AC_DEFINE([HAVE_X86_64_CPU], ,
        [Define if we're running on a CPU in the IA-32 family with 64-bit extensions.])
    ;;

    ia64)
      AC_DEFINE([HAVE_IA64_CPU], ,
        [Define if we're running on a CPU in the IA-64 family.])
    ;;

    powerpc*|ppc*)
      AC_DEFINE([HAVE_PPC_CPU], ,
        [Define if we're running on a CPU in the PowerPC family.])
    ;;

    mips)
      AC_DEFINE([HAVE_MIPS_CPU], ,
        [Define if we're running on a CPU in the MIPS family.])
    ;;

    sparc|sun*)
      AC_DEFINE([HAVE_SPARC_CPU], ,
        [Define if we're running on a CPU in the SPARC family.])
    ;;
  esac
  AX_CHECK_TIMER_WRAPAROUND

  # See how well the architecture can handle misaligned memory accesses.
  if test "$data_alignment" ; then
    ax_cv_cpu_minimum_alignment=$data_alignment
    AX_CPU_MINIMUM_DATA_ALIGNMENT([])   dnl Set CPU_MINIMUM_ALIGNMENT_BYTES.
  else
    AX_CPU_MINIMUM_DATA_ALIGNMENT([16 8 4 2 1])
  fi
  if test "$ax_cv_cpu_minimum_alignment" = unknown ; then
    AC_MSG_NOTICE([Assuming a minimum message alignment of $ax_cv_cpu_minimum_alignment bytes (use --with-alignment to specify otherwise)])
    ax_cv_cpu_minimum_alignment=8
    AX_CPU_MINIMUM_DATA_ALIGNMENT([])   dnl Set CPU_MINIMUM_ALIGNMENT_BYTES.
  fi
  if test "$ax_cv_cpu_minimum_alignment" -gt 1 ; then
    AC_MSG_WARN([Messages must be aligned on a multiple-of-$ax_cv_cpu_minimum_alignment-byte boundary or your programs will abort during initialization])
  fi

  # If we made it this far the run-time library should build
  # properly, unless we got this far because "eval break wouldn't let us
  # stop.
  if test "$ncptl_build_run_time_library" = no ; then
    ncptl_build_run_time_library=yes
  fi

  # Given a proper run-time library, we ought to be able to compile
  # the C-based backends.
  BACKENDS="${BACKENDS} codegen_c_trace.py codegen_c_profile.py codegen_c_mpi.py codegen_c_udgram.py codegen_c_seq.py codegen_c_generic.py"
  break
done

# Warn the user if we can't build the run-time library.
if test "$ncptl_build_run_time_library" != yes ; then
  prevcheck=`cat config.log | \
               $AWK 'BEGIN {finalcheck="very early on"}; \
                     /checking/ {$1=""; finalcheck="while" $0}; \
                     END {print finalcheck}'`
  AC_MSG_WARN([Not building the C run-time library (failed $prevcheck)])
fi
AM_CONDITIONAL([BUILD_RUN_TIME_LIBRARY],
  [test "$ncptl_build_run_time_library" = yes])

# Warn the user if we can't build the Python interface to the
# run-time library.
if test "$BUILD_PYMODULE" = no ; then
  AC_MSG_WARN([Not building the Python interface to the coNCePTuaL run-time library because --disable-pymodule was passed to $0])
elif test "$ncptl_build_run_time_library" != yes ; then
  BUILD_PYMODULE=no
  AC_MSG_WARN([Not building the Python interface to the coNCePTuaL run-time library because the library itself can't be built])
elif test "$BUILD_PYMODULE" = no_no_makefile ; then
  BUILD_PYMODULE=no
  AC_MSG_WARN([Not building the Python interface to the coNCePTuaL run-time library because the Python development tools (e.g., $PYTHON_MAKEFILE) could not be found])
elif test "$BUILD_PYMODULE" = no_not_compatible ; then
  BUILD_PYMODULE=no
  AC_MSG_WARN([Not building the Python interface to the coNCePTuaL run-time library because the C compiler used for Python extension modules ($PYTHON_CC) can't link against the output of $CC])
fi
AM_CONDITIONAL([BUILD_PYMODULE], [test "$BUILD_PYMODULE" = yes])
if test "$BUILD_PYMODULE" = yes ; then
  BACKENDS="${BACKENDS} codegen_interpret.py codegen_picl.py codegen_latex_vis.py codegen_stats.py"
fi

# Warn the user about backends that are useless without the Python
# interface to the run-time library.
if test "$BUILD_PYMODULE" = no ; then
  AC_MSG_WARN([Not installing the coNCePTuaL interpreter because it depends upon the Python interface to the coNCePTuaL run-time library])
  AC_MSG_WARN([Not installing the statistics backend because it depends upon the coNCePTuaL interpreter])
  AC_MSG_WARN([Not installing the PICL backend because it depends upon the coNCePTuaL interpreter])
  AC_MSG_WARN([Not installing the LaTeX visualization backend because it depends upon the coNCePTuaL interpreter])
fi

# ----------------------------------------------------------------------

# If instructed, force "make" to attempt to build everything, even
# things that we've already determined aren't going to work.
if test "$broken_components" = yes ; then
  # Force all of our Automake conditionals to true.
  for conditional in LOGEXTRACT_WORKS HAVE_SWIG HAVE_GPERF \
                     BUILD_RUN_TIME_LIBRARY BUILD_PYMODULE ; do
    if test "AS_VAR_GET([${conditional}_TRUE])" = "#" ; then
      AS_VAR_SET([${conditional}_TRUE], [])
      AS_VAR_SET([${conditional}_FALSE], ['#'])
      AC_MSG_WARN([--enable-broken-components has forced $conditional to "true"])
    fi
  done

  # Determine which backends we're re-enabling.
  reenabled_backends=`\
    echo $BACKENDS $ALL_BACKENDS | \
    sed 's/codegen_//g' | sed 's/\.py//g' | \
    $AWK '{for (f=1; f<=NF; f++) seen[[$f]]++; \
           for (s in seen) if (seen[[s]]==1) printf "%s ", s}'`
  if test "$reenabled_backends" ; then
    BACKENDS="$ALL_BACKENDS"
    AC_MSG_WARN([--enable-broken-components has forced the following backends to be installed: $reenabled_backends])
  fi
fi

# Abort if we can't build *any* backends.
if test -z "$BACKENDS" ; then
  AC_MSG_ERROR([none of the compiler backends can be built])
fi
AC_SUBST([BACKENDS])

# Insert the list of backends into the ncptl man page.
BACKEND_BULLET_LIST=conftest.backends
echo $BACKENDS | sed 's%codegen_%%g' | sed 's%\.py%%g' | \
  $AWK '{for (i=1; i<=NF; i++) print ".IP \\(bu\n\\fC" $i "\\fR"}' > $BACKEND_BULLET_LIST
AC_SUBST_FILE([BACKEND_BULLET_LIST])

# If we're building the C+MPI backend, try to determine how to
# compile C programs with calls to an MPI library.
if test "`echo $BACKENDS | grep codegen_c_mpi.py`" ; then
  # Find an mpicc program (default: $CC).
  AC_MSG_NOTICE([determining how to compile and link MPI programs])
  MPICC_is_CC=no
  if test -z "$MPICC" ; then
    AC_CHECK_PROGS([MPICC], [mpicc], [no])
    if test "$MPICC" = no ; then
      MPICC="$CC"
      MPICC_is_CC=yes
    fi
  fi

  # Unless MPILIBS was specified explicitly, assign a reasonable value to it.
  if test `set | egrep -c ^MPILIBS=` -eq 0 ; then
    prev_CC="$CC"
    prev_CPPFLAGS="$CPPFLAGS"
    prev_LDFLAGS="$LDFLAGS"
    prev_LIBS="$LIBS"
    # Some mpicc implementations invoke $CC, which is an infinite loop if
    # we simply set CC="$MPICC".
    CC="env CC=$CC $MPICC"
    CPPFLAGS="$CPPFLAGS $MPICPPFLAGS"
    LDFLAGS="$LDFLAGS $MPILDFLAGS"
    AC_CHECK_HEADER([mpi.h],
      [AX_SEARCH_LIBS([MPI_Init], [mpi mpich],
        [test "$ac_cv_search_MPI_Init" = "none required" || MPILIBS="$ac_cv_search_MPI_Init $MPILIBS"],
        [AC_MSG_WARN([The c_mpi backend may fail to link your applications])])],
      [AC_MSG_WARN([The c_mpi backend may fail to compile your applications])])
    LIBS="$prev_LIBS"
    LDFLAGS="$prev_LDFLAGS"
    CPPFLAGS="$prev_CPPFLAGS"
    CC="$prev_CC"
  fi

  # Sometimes, mpicc uses a different compiler/linker from $CC.  The
  # math library is the typical thing that fails.
  if test "$MPICC_is_CC" = no ; then
    orig_CC=$CC
    # Some mpicc implementations invoke $CC, which is an infinite loop if
    # we simply set CC="$MPICC".
    CC="env CC=$CC $MPICC"
    AC_CACHE_CHECK([if $MPICC wants the math library to be linked explicitly],
      [ax_cv_func_mpicc_requires_libm],
      [dnl
       # Construct a string of function uses.
       ax_math_func_uses=""
       for ax_func in log10 floor ceil sqrt trunc ; do
         if test "AS_VAR_GET([ac_cv_func_$ax_func])" = yes ; then
           ax_math_func_uses="$ax_math_func_uses
volatile double have_$ax_func = $ax_func(12.34);"
         fi
       done
       for ax_func in pow fmod ; do
         if test "AS_VAR_GET([ac_cv_func_$ax_func])" = yes ; then
           ax_math_func_uses="$ax_math_func_uses
volatile double have_$ax_func = $ax_func(12.34, 56.78);"
         fi
       done

       # See if we can link the generated string.
       AC_TRY_LINK([#include <math.h>],
        [$ax_math_func_uses],
        [ax_cv_func_mpicc_requires_libm=no],
        [ax_cv_func_mpicc_requires_libm=yes])])
    if test "$ax_cv_func_mpicc_requires_libm" = yes ; then
      MPILIBS="-lm $MPILIBS"
    fi
    CC=$orig_CC
  fi

  AC_SUBST([MPICC])
  AC_SUBST([MPICPPFLAGS])
  AC_SUBST([MPICFLAGS])
  AC_SUBST([MPILDFLAGS])
  AC_SUBST([MPILIBS])
fi

# Determine if "make" predefines RM.  We used to write "RM ?= rm -f"
# in the Makefile but this broke on an AIX/PPC machine on which IBM's
# "make" program neither predefines RM nor supports the "?=" construct.
DEFINE_RM=
AC_SUBST([DEFINE_RM])
AC_CACHE_CHECK([if $am_make supports `?='],
  [ax_cv_prog_make_RM_qeq],
  [echo " " | ${AWK} 'END {print "RM ?= rm -f\n\ntest:\n\t$(RM) conftest.zero"}' > conftest.make
   touch conftest.zero
   $am_make -f conftest.make > /dev/null 2>&1
   if test -f conftest.zero ; then
     ax_cv_prog_make_RM_qeq=no
   else
     ax_cv_prog_make_RM_qeq=yes
   fi])
if test "$ax_cv_prog_make_RM_qeq" = yes ; then
  DEFINE_RM="RM ?= rm -f"
else
  AC_CACHE_CHECK([if $am_make predefines \$(RM)],
    [ax_cv_prog_make_RM],
    [echo " " | ${AWK} 'END {print "test:\n\t$(RM) conftest.zero"}' > conftest.make
     touch conftest.zero
     $am_make -f conftest.make > /dev/null 2>&1
     if test -f conftest.zero ; then
       ax_cv_prog_make_RM=no
     else
       ax_cv_prog_make_RM=yes
     fi])
  if test "$ax_cv_prog_make_RM" = no ; then
    DEFINE_RM="RM = rm -f"
  fi
fi

# The "make" program on NetBSD (x86-netbsd1.sf.net, at least) doesn't
# expand file globs so we need to help it out.
EXAMPLEFILES="`cd $srcdir ; echo examples/*.ncptl`"
AC_SUBST([EXAMPLEFILES])

# Create a template for a pkgconfig-style ncptl.pc file.
cat <<EOF > ncptl.pc.in
prefix=@prefix@
exec_prefix=@exec_prefix@
includedir=@includedir@
libdir=@libdir@

Name: @PACKAGE_NAME@
Description: @PACKAGE_NAME@ run-time library
Version: @VERSION@
Cflags: -I\${includedir} @CPPFLAGS@ @CFLAGS@
Libs: -L\${libdir} @LDFLAGS@ @LIBS@
EOF

# The following definitions could be produced automatically with GNU
# Make substitution rules.  However, in hopes of building with other
# Make utilities, we have configure do all of the substitution work
# itself.  sample-AST and backend-deps have to be handled specially
# because they aren't generated from LaTeX sources.
for imagebase in mesh1D mesh2D mesh3D tree2 tree3 2nomial 3nomial latex_vis ; do
  TEXTIMAGES="$TEXTIMAGES ${imagebase}.txt"
  TEXIMAGES="$TEXIMAGES ${imagebase}.tex"
  LOGIMAGES="$LOGIMAGES ${imagebase}.log"
  AUXIMAGES="$LOGIMAGES ${imagebase}.aux"
  DVIIMAGES="$DVIIMAGES ${imagebase}.dvi"
  EPSIMAGES="$EPSIMAGES ${imagebase}.eps"
  PDFIMAGES="$PDFIMAGES ${imagebase}.pdf"
  JPEGIMAGES="$JPEGIMAGES ${imagebase}.jpg"
  PNGIMAGES="$PNGIMAGES ${imagebase}.png"
done
for imagebase in sample-AST backend-deps gui ; do
  TEXTIMAGES="$TEXTIMAGES ${imagebase}.txt"
  EPSIMAGES="$EPSIMAGES ${imagebase}.eps"
  PDFIMAGES="$PDFIMAGES ${imagebase}.pdf"
  JPEGIMAGES="$JPEGIMAGES ${imagebase}.jpg"
  PNGIMAGES="$PNGIMAGES ${imagebase}.png"
done
BUILTIMAGES="$PDFIMAGES $EPSIMAGES $JPEGIMAGES $PNGIMAGES"
BUILTIMAGES=`echo $BUILTIMAGES | sed -e 's,sample-AST.eps,,' -e 's,gui\.\(eps\|png\),,g'`
if test "$ac_cv_path_DOT" = no ; then
  BUILTIMAGES=`echo $BUILTIMAGES | sed s,backend-deps.eps,,`
fi
AC_SUBST([TEXIMAGES])
AC_SUBST([TEXTIMAGES])
AC_SUBST([LOGIMAGES])
AC_SUBST([AUXIMAGES])
AC_SUBST([DVIIMAGES])
AC_SUBST([EPSIMAGES])
AC_SUBST([PDFIMAGES])
AC_SUBST([JPEGIMAGES])
AC_SUBST([PNGIMAGES])
AC_SUBST([BUILTIMAGES])

# Fully expand the CC variable.
CC="$full_CC"

# Export to the run-time library the ./configure command line.
AC_SUBST([CONFIGURE_COMMAND],
  [`echo "$SHELL "$0"$ac_configure_args" | $PYTHON $srcdir/makehelper.py quote`])

# Write to a file a list of all AC_SUBSTed variables.
set > conftest.shvars
m4_ifdef([_AC_SUBST_VARS],
  [# Handle newer versions of Autoconf.
cat <<SUBST_EOF > conftest.subst
_AC_SUBST_VARS
SUBST_EOF
  ],
  [# Handle older versions of Autoconf.
cat <<SUBST_EOF > conftest.subst
_AC_SUBST_SED_PROGRAM
SUBST_EOF
  ])
$PYTHON $srcdir/makehelper.py ac_subst conftest.shvars conftest.subst > substitutions.dat.in
rm -f conftest.shvars conftest.subst

# ----------------------------------------------------------------------

# Define some extra text to include at the top and bottom of config.h.
AH_TOP(dnl
[/* ----------------------------------------------------------------------
 *
 * coNCePTuaL configuration-specific header file
 *
 * ----------------------------------------------------------------------
 *
 * PUT_LICENSE_][TEXT_HERE
 *
 * ----------------------------------------------------------------------
 */

#ifndef _CONFIG_H_
#define _CONFIG_H_])
  AH_BOTTOM([/*----- There should be no need to modify anything beyond this point. -----*/

/* Include a few extra function prototypes if we're using GNU C. */
#if defined(__GNUC__) && !defined(_GNU_SOURCE)
# define _GNU_SOURCE
#endif

/* Include standard headers and user-defined code provided by
 * --with-header-code. */
#include "extra_config.h"

/* Include all of the header files we require. */
#include <stdarg.h>
#include <signal.h>
#include <errno.h>
#include <math.h>
#include <fcntl.h>
#include <ctype.h>
#include <float.h>
#if defined(HAVE_LINUX_TIMEX_H) && defined(HAVE_GET_CYCLES)
# include <linux/timex.h>
#endif]
AX_AUTO_INCLUDE_HEADERS([sys/resource.h sys/syssgi.h invent.h])dnl
AX_AUTO_INCLUDE_HEADERS([sys/sysinfo.h sys/mman.h uuid/uuid.h pci/pci.h])dnl
AX_AUTO_INCLUDE_HEADERS([odmi.h cf.h sys/cfgodm.h infiniband/verbs.h])dnl
AX_AUTO_INCLUDE_HEADERS([machine/hal_sysinfo.h kstat.h sys/sysmp.h])dnl
AX_AUTO_INCLUDE_HEADERS([sys/param.h sys/wait.h ieeefp.h sys/sysctl.h])dnl
AX_AUTO_INCLUDE_HEADERS([c_asm.h nx.h pwd.h windows.h sched.h])dnl
[#ifdef HAVE_HAL
# include <libhal.h>
#endif
#ifdef HAVE_LIBELAN
# include <rms/rmscall.h>
#endif
#ifdef HAVE_BGPPERSONALITY
# include <spi/kernel_interface.h>
# include <common/bgp_personality.h>
#endif
#ifdef HAVE_BGLPERSONALITY
# include <bglpersonality.h>
# include <rts.h>
#endif
#ifdef HAVE_RSMS_RS_ID_H
# include <rsms/rs_id.h>
#endif
#ifdef HAVE_RCAMESHCOORD
# include <rca_lib.h>
# include <rsms/rs_meshcoord.h>
#endif
#ifdef USE_POPT
# include <popt.h>
  /* Older versions of popt don't define POPT_TABLEEND. */
# ifndef POPT_TABLEEND
#  define POPT_TABLEEND { NULL, '\0', 0, 0, 0, NULL, NULL }
# endif
#endif
#ifdef USE_GETOPT_LONG
# if defined(HAVE_GNUGETOPT_H)
#  include <gnugetopt.h>
# elif defined(HAVE_GETOPT_H)
#  include <getopt.h>
# endif
#elif defined(HAVE_GETOPT_H)
# include <getopt.h>
#endif
#ifdef USE_PAPI
# include <papi.h>
#endif
#ifdef FORCE_MPI_WTIME
# include <mpi.h>
#endif

#endif])


# Determine the architecture to use for the Autopackage specification
# file.  We assume that AC_PROG_LIBTOOL has already invoked
# AC_CANONICAL_HOST.
case $host_cpu in
  i?86)
    AP_ARCH=x86
    ;;
  *)
    AP_ARCH=$host_cpu
    ;;
esac
AC_SUBST([AP_ARCH])

# Create a customized Makefile and other files.
AC_CONFIG_COMMANDS([config.status],
  [],
  [AWK="$AWK"])dnl This is needed for AX_MSG_WARN to work.
AC_CONFIG_FILES([Makefile tests/Makefile doc/Makefile Makefile.simple      \
                 gui/Makefile ncptl.h.ni:ncptl.h.in doc/ncptl.1            \
                 doc/ncptl-replaytrace.1 conceptual.spec substitutions.dat \
                 ncptl.pc conceptual.apspec gui/ncptlGUI.html])
AC_CONFIG_FILES([tests/backend_dot_ast],
  [chmod +x tests/backend_dot_ast])
AC_CONFIG_FILES([tests/backend_interpret],
  [chmod +x tests/backend_interpret])
AC_CONFIG_FILES([ncptl-logextract],
  [chmod +x ncptl-logextract],
  [$PYTHON $srcdir/ncptl_keywords.py > ncptl-logextract_keywords])
AC_OUTPUT

# Output the values of some key configuration variables.
echo
$am_make showenv
echo

# Redisplay all of the warning messages we've issued up to this point.
AX_SHOW_WARNINGS
