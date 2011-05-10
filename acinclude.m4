dnl ----------------------------------------------------------------------
dnl
dnl Helper macros for coNCePTuaL's configure.ac script
dnl
dnl By Scott Pakin <pakin@lanl.gov>
dnl
dnl ----------------------------------------------------------------------
dnl
dnl Copyright (C) 2011, Los Alamos National Security, LLC
dnl All rights reserved.
dnl 
dnl Copyright (2011).  Los Alamos National Security, LLC.  This software
dnl was produced under U.S. Government contract DE-AC52-06NA25396
dnl for Los Alamos National Laboratory (LANL), which is operated by
dnl Los Alamos National Security, LLC (LANS) for the U.S. Department
dnl of Energy. The U.S. Government has rights to use, reproduce,
dnl and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
dnl MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
dnl FOR THE USE OF THIS SOFTWARE. If software is modified to produce
dnl derivative works, such modified software should be clearly marked,
dnl so as not to confuse it with the version available from LANL.
dnl 
dnl Additionally, redistribution and use in source and binary forms,
dnl with or without modification, are permitted provided that the
dnl following conditions are met:
dnl 
dnl   * Redistributions of source code must retain the above copyright
dnl     notice, this list of conditions and the following disclaimer.
dnl 
dnl   * Redistributions in binary form must reproduce the above copyright
dnl     notice, this list of conditions and the following disclaimer
dnl     in the documentation and/or other materials provided with the
dnl     distribution.
dnl 
dnl   * Neither the name of Los Alamos National Security, LLC, Los Alamos
dnl     National Laboratory, the U.S. Government, nor the names of its
dnl     contributors may be used to endorse or promote products derived
dnl     from this software without specific prior written permission.
dnl 
dnl THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
dnl EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
dnl IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
dnl PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
dnl LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
dnl OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
dnl OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
dnl BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
dnl WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
dnl OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
dnl EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
dnl
dnl ----------------------------------------------------------------------


dnl @synopsis AX_CPU_MINIMUM_DATA_ALIGNMENT (BYTE-OFFSETS)
dnl
dnl Some CPUs can access data from any address.  Others requires addresses
dnl to be a multiple of the word size or some other number of bytes.
dnl AX_CPU_MINIMUM_DATA_ALIGNMENT helps find what addresses are allowed.
dnl The BYTE-OFFSETS parameter is a monotonically decreasing,
dnl space-separated list of constants (no shell variables!) representing
dnl byte offsets from known-valid alignments.  Typical usage is as
dnl follows:
dnl
dnl     AX_CPU_MINIMUM_DATA_ALIGNMENT([16 8 4 2 1])
dnl
dnl This says to try accessing memory 16 bytes after a valid address, then
dnl 8 bytes after a valid address, then 4, then 2, then 1.
dnl CPU_MINIMUM_ALIGNMENT_BYTES will be #define'd to the smallest of these
dnl that doesn't result in a bus error (or #undef'd if they all produce
dnl bus errors).  For example, the x86 family of processors can access
dnl memory from any location so they #define CPU_MINIMUM_ALIGNMENT_BYTES
dnl to 1.  The UltraSPARC, in contrast, can access only memory that is
dnl 4-byte aligned, so it #defines CPU_MINIMUM_ALIGNMENT_BYTES to 4.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_CPU_MINIMUM_DATA_ALIGNMENT],
[AC_CACHE_CHECK([minimum required data alignment (in bytes)],
  [ax_cv_cpu_minimum_alignment],
  [ax_cv_cpu_minimum_alignment=unknown
   while true ; do
     AC_FOREACH([misalignment_const], [$1],
      [
       AC_TRY_RUN(
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#ifdef HAVE_STDLIB_H
# include <stdlib.h>
#endif

int
main()
{
  int alignment = misalignment_const;
  void *malloced_buffer;
  void *buffer;

  /* Allocate enough memory for padding and for storing the unpadded
   * address. */
  malloced_buffer = buffer = (void *) malloc (alignment + sizeof(uint64_t));
  if (!buffer)
    return 1;

  /* Align the buffer appropriately and store the unpadded address. */
  buffer = (void *) ((char *)buffer + alignment + sizeof(uint64_t));
  if (alignment)
    buffer = (void *) (alignment * ((uintptr_t)buffer/alignment));
  ((uint64_t *)buffer)@<:@-1@:>@ = 12345;

  return 0;
}
        ,
        [ax_cv_cpu_minimum_alignment=misalignment_const],
        [break],
        [break])
      ])
     break
   done])
if test "$ax_cv_cpu_minimum_alignment" != unknown ; then
  AC_DEFINE_UNQUOTED([CPU_MINIMUM_ALIGNMENT_BYTES],
    [$ax_cv_cpu_minimum_alignment],
    [Define as the minimum number of bytes that a memory address can be
     misaligned without causing a bus error.])
fi
])


dnl @synopsis AX_APPEND_TO_FILE (FILENAME, BODY)
dnl
dnl Append BODY, which can contain multiple lines of text, to file FILENAME.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_APPEND_TO_FILE],
[cat >> $1 <<AX_APPEND_TO_FILE_EOF
$2
AX_APPEND_TO_FILE_EOF
])


dnl @synopsis AX_REQUIRE_ONE_FUNC (FUNCTION..., [ACTION-IF-ANY-FOUND], [ACTION-IF-NONE-FOUND])
dnl
dnl AX_REQUIRE_ONE_FUNC is a simple wrapper for AC_CHECK_FUNCS.  It calls
dnl AC_CHECK_FUNCS on the list of functions named in the first argument,
dnl then invokes ACTION-IF-ANY-FOUND if at least one of the functions
dnl exists or ACTION-IF-NONE-FOUND if none of the functions exist.
dnl
dnl Here's an example:
dnl
dnl     AX_REQUIRE_ONE_FUNC([posix_memalign memalign valloc], ,
dnl       [AC_MSG_ERROR([unable to allocate page-aligned memory])])
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_REQUIRE_ONE_FUNC],
[m4_define([ax_1func_cv], [AS_TR_SH(ax_cv_func_any_$1)])
AC_CACHE_VAL([ax_1func_cv],
  [ax_1func_cv=no
   AC_CHECK_FUNCS([$1],
     [ax_1func_cv="$ax_1func_cv $ac_func"])])
AS_IF([test "$ax_1func_cv" = no],
  [$3],
  [ax_1func_cv=`echo $ax_1func_cv | sed 's/^no //'`
   for ax_1func in $ax_1func_cv ; do
     AC_DEFINE_UNQUOTED(AS_TR_CPP([HAVE_$ax_1func]))
   done
   $2])
])


dnl @synopsis AC_DEFINE_INTEGER_BITS (TYPE [, CANDIDATE-TYPE]...)
dnl
dnl Given a TYPE of the form "int##_t" or "uint##_t", see if the datatype
dnl TYPE is predefined.  If not, then define TYPE -- both with AC_DEFINE
dnl and as a shell variable -- to the first datatype of exactly ## bits in
dnl a list of CANDIDATE-TYPEs.  If none of the CANDIDATE-TYPEs contains
dnl exactly ## bits, then set the TYPE shell variable to "no".
dnl
dnl For example, the following ensures that uint64_t is defined as a
dnl 64-bit datatype:
dnl
dnl     AC_DEFINE_INTEGER_BITS(uint64_t, unsigned long long, unsigned __int64, long)
dnl     if test "$uint64_t" = no; then
dnl       AC_MSG_ERROR([unable to continue without a 64-bit datatype])
dnl     fi
dnl
dnl You should then put the following in your C code to ensure that all
dnl datatypes defined by AC_DEFINE_INTEGER_BITS are visible to your program:
dnl
dnl     #include "config.h"
dnl
dnl     #if HAVE_INTTYPES_H
dnl     # include <inttypes.h>
dnl     #elif HAVE_STDINT_H
dnl     # include <stdint.h>
dnl     #elif HAVE_SYS_TYPES_H
dnl     # include <sys/types.h>
dnl     #endif
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@uiuc.edu>
dnl

AC_DEFUN([AC_DEFINE_INTEGER_BITS],
[m4_define([ac_datatype_bits], [m4_translit($1, [a-zA-Z_])])
m4_define([ac_datatype_bytes], [m4_eval(ac_datatype_bits/8)])
AC_CHECK_TYPE($1, ,
 [
  AC_MSG_NOTICE([trying to find a suitable ]ac_datatype_bytes[-byte replacement for $1])
  $1=no
  find_$1 ()
  {
    _AC_DEFINE_INTEGER_BITS_HELPER($@)
    :
  }
  find_$1
  AC_DEFINE_UNQUOTED($1, $$1,
    [If not already defined, then define as a datatype of *exactly* ]ac_datatype_bits[ bits.])
 ])
])

dnl Iterate over arguments $2..$N, trying to find a good match for $1.
m4_define([_AC_DEFINE_INTEGER_BITS_HELPER],
[ifelse($2, , ,
 [m4_define([ac_datatype_bits], [m4_translit($1, [a-zA-Z_])])
  m4_define([ac_datatype_bytes], [m4_eval(ac_datatype_bits/8)])
  AC_CHECK_SIZEOF($2)
  if test "$AS_TR_SH(ac_cv_sizeof_$2)" -eq ac_datatype_bytes; then
    $1="$2"
    return
  fi
  _AC_DEFINE_INTEGER_BITS_HELPER($1, m4_shift(m4_shift($@)))
 ])
])


dnl @synopsis AX_FIND_HI_RES_TIMER ([ACTION-IF-DEFINED], [ACTION-IF-NOT-DEFINED])
dnl
dnl Every platform has a different set of mechanisms for reading a
dnl high-resolution timer.  This macro tries to determine what's
dnl available.  If the USE_PAPI environment variable is "yes", we use the
dnl PAPI library to read the timer.  Otherwise, we use a trial-and-error
dnl approach.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_FIND_HI_RES_TIMER],
[
  AC_MSG_NOTICE([checking for a way to map cycles to microseconds])
  _AX_TRY_MAP_CYCLES_USECS

  AC_MSG_NOTICE([checking for a high-resolution timer])
  have_some_timer=no
  _AX_TRY_TIMER_PAPI([have_some_timer=yes])
  _AX_TRY_TIMER_CYCLE_ASM(dnl
    [have_some_timer=yes],
    [_AX_TRY_TIMER_CYCLE_LINUX(dnl
      [have_some_timer=yes],
      [_AX_TRY_TIMER_CYCLE_CCC_ALPHA(dnl
        [have_some_timer=yes])])])
  _AX_TRY_TIMER_CLOCK_GETTIME(dnl
    [have_some_timer=yes],
    [_AX_TRY_TIMER_DCLOCK(dnl
      [have_some_timer=yes],
      [AC_CHECK_HEADERS([windows.h],dnl Defines QueryPerformanceCounter().
        [have_some_timer=yes],
        [AX_REQUIRE_ONE_FUNC([gettimeofday], [have_some_timer=yes])])])])
  AS_IF([test "$have_some_timer" = yes], [$1], [$2])
])


dnl See if PAPI is available.  Define USE_PAPI if it is.
dnl First argument is ACTION-IF-DEFINED.  Second argument is
dnl ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_PAPI],
[
USE_PAPI=no
AC_CHECK_HEADERS([papi.h])
if test "$ac_cv_header_papi_h" = yes ; then
  AC_CHECK_LIB([lipr], [IprStart])
  AC_CHECK_LIB([perfctr], [main])
  AC_CHECK_LIB([papi], [PAPI_get_real_usec])
  if test "$ac_cv_lib_papi_PAPI_get_real_usec" = yes ; then
    USE_PAPI=yes
    AC_DEFINE([USE_PAPI], ,
      [Define to use the Performance API (PAPI).])
  fi
fi
AS_IF([test "$USE_PAPI" = yes], [$1], [$2])
])


dnl See if we both recognize the architecture name and can insert inline
dnl assembly language into a C program.  Define HAVE_ASM_VOLATILE_CYCLES
dnl if both conditions are true.  First argument is ACTION-IF-DEFINED.
dnl Second argument is ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_CYCLE_ASM],
[
AC_CACHE_CHECK([if we can read the $host_cpu cycle counter with "asm volatile"],
  [ax_cv_c_asm_volatile],
  [
case "$host_cpu" in
  i?86|x86_64|ia64|powerpc*|ppc*|alpha*)
    AC_TRY_LINK(
      [],
      [asm volatile ("");],
      [ax_cv_c_asm_volatile=yes],
      [ax_cv_c_asm_volatile=no])
    ;;

  *)
    ax_cv_c_asm_volatile=no
    ;;
esac
  ])
AS_IF([test "$ax_cv_c_asm_volatile" = yes],
  [AC_DEFINE([HAVE_ASM_VOLATILE_CYCLES], ,
     [Define if `asm volatile' works and coNCePTuaL supports reading the cycle counter on this CPU architecture.])
   $1],
  [$2])
])


dnl Linux defines a get_cycles() interface to the cycle timer.  Define
dnl HAVE_GET_CYCLES if that's available.  First argument is
dnl ACTION-IF-DEFINED.  Second argument is ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_CYCLE_LINUX],
[
AC_CACHE_VAL([ax_cv_func_get_cycles],
  [ax_cv_func_get_cycles=no
   AC_CHECK_HEADERS([linux/timex.h],
     [if test "$ac_header_compiler:$ac_header_preproc" = "yes:yes" ; then
        AC_MSG_CHECKING([if get_cycles exists and works])
        AC_RUN_IFELSE([AC_LANG_PROGRAM(dnl
          [dnl
#if TIME_WITH_SYS_TIME
# include <sys/time.h>
# include <time.h>
#else
# if HAVE_SYS_TIME_H
#  include <sys/time.h>
# else
#  include <time.h>
# endif
#endif
#include <linux/timex.h>
          ],
          [dnl
  clock_t numcycles = get_cycles();
  exit (numcycles == 0);
          ])],
          [ax_cv_func_get_cycles=yes],
          [ax_cv_func_get_cycles=no],
          [ax_cv_func_get_cycles=no])
        AC_MSG_RESULT([$ax_cv_func_get_cycles])
      fi])])
AS_IF([test "$ax_cv_func_get_cycles" = yes],
  [AC_DEFINE([HAVE_GET_CYCLES], [1],
     [Define to 1 if you have the `get_cycles' function.])
   $1],
  [$2])
])


dnl ccc/Alpha has its own "asm" construct for reading the PCC.  Define
dnl HAVE_CCC_ALPHA_RPCC if that's available.  First argument is
dnl ACTION-IF-DEFINED.  Second argument is ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_CYCLE_CCC_ALPHA],
[
AC_CACHE_VAL([ax_cv_func_asm_ccc_alpha],
  [ax_cv_func_asm_ccc_alpha=no
   AC_CHECK_HEADERS([c_asm.h],
     [if test "$ac_header_compiler:$ac_header_preproc" = "yes:yes" ; then
        AC_MSG_CHECKING([if we can use ccc/Alpha's asm construct])
        AC_TRY_RUN([
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif
#include <c_asm.h>

int
main()
{
  uint64_t now = asm ("rpcc %v0");
  exit (now == 0);
}
          ],
          [ax_cv_func_asm_ccc_alpha=yes])
        AC_MSG_RESULT([$ax_cv_func_asm_ccc_alpha])
      fi])])
AS_IF([test "$ax_cv_func_asm_ccc_alpha" = yes],
  [AC_DEFINE([HAVE_CCC_ALPHA_RPCC], [1],
     [Define to 1 if you can read the Alpha PCC using the ccc compiler's `asm' construct.])
   $1],
  [$2])
])


dnl If we're reading a cycle counter we need a way to map to microseconds.
dnl Define some macros saying what our alternatives are.
m4_define([_AX_TRY_MAP_CYCLES_USECS],
[
AC_MSG_CHECKING([if the OS defines a timebase-frequency file])
if test ! -d /proc/device-tree ; then
  AC_MSG_RESULT([no])
elif test "`find /proc/device-tree -name timebase-frequency | wc -l`" -gt 0 ; then
  TIMEBASE_FREQUENCY_FILENAME="`find /proc/device-tree -name timebase-frequency | head -1`"
  AC_DEFINE_UNQUOTED([TIMEBASE_FREQUENCY_FILENAME],
    ["$TIMEBASE_FREQUENCY_FILENAME"],
    [Define as a filename from which the timebase frequency can be read in hertz as a binary integer.])
  AC_MSG_RESULT([$TIMEBASE_FREQUENCY_FILENAME])
fi
AC_MSG_CHECKING([if we can read the CPU/timer frequency from /proc/cpuinfo])
if test -r /proc/cpuinfo ; then
  if test "`egrep -c '^(cpu MHz|itc MHz|timebase|cycle frequency .Hz.|clock)[[^-A-Za-z0-9_:]]*: ' /proc/cpuinfo`" -gt 0 ; then
    AC_MSG_RESULT([yes])
    AC_DEFINE([HAVE_PROC_CPUINFO_FREQ], ,
      [Define if /proc/cpuinfo lists the CPU/timer frequency.])
  else
    AC_MSG_RESULT([no])
  fi
else
  AC_MSG_RESULT([no])
fi
AC_CHECK_HEADERS([sys/syssgi.h invent.h sys/sysinfo.h machine/hal_sysinfo.h])
AC_CHECK_FUNCS([sysctl],
  [dnl On BSD systems, sys/sysctl.h seems to require sys/param.h.
   AC_CHECK_HEADERS([sys/param.h])
   AC_CHECK_HEADERS([sys/sysctl.h], , ,
     [#if HAVE_SYS_PARAM_H
# include <sys/param.h>
#endif])])
AC_SEARCH_LIBS([kstat_data_lookup],
   [kstat],
   [AC_CHECK_FUNCS([kstat_data_lookup])
    AC_CHECK_HEADERS([kstat.h])])
])


dnl Check the availability of a given clock_gettime() clock type.
m4_define([_AX_CHECK_CLOCKID],
[
  AC_MSG_CHECKING([if $1 is defined])
  AC_EGREP_CPP([yes],
    [
#if TIME_WITH_SYS_TIME
# include <sys/time.h>
# include <time.h>
#else
# if HAVE_SYS_TIME_H
#  include <sys/time.h>
# else
#  include <time.h>
# endif
#endif

#ifdef $1
  yes
#endif
    ],

    dnl UNICOS -- at least the 2.4.22 installation I was using -- defines a
    dnl CLOCK_SGI_CYCLE macro but fails at runtime when it's used.  Even
    dnl worse, a NetBSD 2.0.2 system provides a CLOCK_MONOTONIC that
    dnl increments only once per quantum.  We therefore have to verify that
    dnl the given clock returns successfully and exhibits acceptable
    dnl granularity.
    [AC_MSG_RESULT([yes])
     AC_MSG_CHECKING([if $1 is usable])
     AC_TRY_RUN([
#if TIME_WITH_SYS_TIME
# include <sys/time.h>
# include <time.h>
#else
# if HAVE_SYS_TIME_H
#  include <sys/time.h>
# else
#  include <time.h>
# endif
#endif
#if HAVE_INTTYPES_H
# include <inttypes.h>
#elif HAVE_STDINT_H
# include <stdint.h>
#elif HAVE_SYS_TYPES_H
# include <sys/types.h>
#endif

int
main (void)
{
  uint64_t totaltime = 0;       /* Time deltas in nanoseconds */
  uint64_t numsamples = 0;      /* # of samples represented by totaltime */

#ifdef HAVE_SLEEP
  sleep (0);                    /* Start at the beginning of a quantum. */
#endif
  while (numsamples < 100) {
    struct timespec now1, now2; /* Adjacent time samples */
    uint64_t timedelta;         /* Difference in nanoseconds between samples */

    if (clock_gettime($1, &now1) == -1
        || clock_gettime($1, &now2) == -1)
      return 1;
    timedelta = 1000000000*((uint64_t)now2.tv_sec - (uint64_t)now1.tv_sec)
                + (uint64_t)now2.tv_nsec - (uint64_t)now1.tv_nsec;
    if (timedelta > 0) {
      totaltime += timedelta;
      numsamples++;
    }
  }
  if (totaltime/numsamples > 1000000)
    return 1;   /* Average delta of more than 1ms */
  return 0;
}
      ],
      [AC_MSG_RESULT([yes])
       $2
      ],
      [AC_MSG_RESULT([no])
       $3
      ],
      [AC_MSG_RESULT([assuming yes])
       $2
      ])
    ],
    [AC_MSG_RESULT([no])
     $3
    ])
])


dnl See if the clock_gettime() exists and what the most accurate timer
dnl available to it is.  Defines CLOCKID as the argument to
dnl clock_gettime() and CLOCKID_STRING as a C string equivalent.  First
dnl argument is ACTION-IF-DEFINED.  Second argument is
dnl ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_CLOCK_GETTIME],
[
AC_SEARCH_LIBS([clock_gettime], [rt],
  [AC_DEFINE([HAVE_CLOCK_GETTIME], [1],
     [Define to 1 if you have the `clock_gettime' function.])
   CLOCKID=""
   AC_CHECK_FUNCS([sleep])
   _AX_CHECK_CLOCKID([CLOCK_MONOTONIC],
     [CLOCKID=CLOCK_MONOTONIC],
     [_AX_CHECK_CLOCKID([CLOCK_HIGHRES],
       [CLOCKID=CLOCK_HIGHRES],
       [_AX_CHECK_CLOCKID([CLOCK_SGI_CYCLE],
         [CLOCKID=CLOCK_SGI_CYCLE],
         [_AX_CHECK_CLOCKID([CLOCK_REALTIME],
           [CLOCKID=CLOCK_REALTIME])
         ])
       ])
     ])
  ])
AS_IF([test "$CLOCKID"],
  [AC_DEFINE_UNQUOTED([CLOCKID], [$CLOCKID],
     [Define as the type of clock that `clock_gettime' should use.])
   AC_DEFINE_UNQUOTED([CLOCKID_STRING], ["$CLOCKID"],
     [Define to be the same as CLOCKID but within double quotes.])
   $1],
  [$2])
])


dnl See if the dclock() function exists.  First argument is
dnl ACTION-IF-DEFINED.  Second argument is ACTION-IF-NOT-DEFINED.
m4_define([_AX_TRY_TIMER_DCLOCK],
[
AC_CHECK_FUNCS([dclock],
  [AC_CHECK_HEADERS([nx.h])
   $1],
  [$2])
])


dnl @synopsis AX_CHECK_TIMER_WRAPAROUND
dnl
dnl Set ax_cv_func_timer_wraps to "no" if the cycle timer has a 64-bit
dnl range, "yes" if it has only a 32-bit range (and is therefore
dnl susceptible to premature wraparounds).  This macro should not be
dnl called if FORCE_GETTIMEOFDAY or FORCE_MPI_WTIME is set.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_CHECK_TIMER_WRAPAROUND],
[
AC_CACHE_CHECK([if the high-resolution timer wraps around too quickly],
  [ax_cv_func_timer_wraps],
  [ax_cv_func_timer_wraps=no
   AC_TRY_RUN([
int
main()
{
#ifdef HAVE_GET_CYCLES
  if (sizeof(get_cycles()) < 8)
    exit (1);
#elif defined(HAVE_SYS_SYSSGI_H) && defined(HAVE_SYSSGI)
  if (syssgi(SGI_CYCLECNTR_SIZE) < 64)
    exit (1);
#elif defined(HAVE_ALPHA_CPU) && \
    (defined(HAVE_ASM_VOLATILE_CYCLES) || defined(HAVE_CCC_ALPHA_RPCC))
    exit (1);
#endif
    exit (0);
}
     ],
     [ax_cv_func_timer_wraps=no],
     [ax_cv_func_timer_wraps=yes],
     [ax_cv_func_timer_wraps=no])])
if test "$ax_cv_func_timer_wraps" = yes ; then
  AC_DEFINE([HAVE_32BIT_CYCLE_COUNTER], ,
    [Define if the cycle counter contains only 32 bits of accuracy.])
fi
])


dnl @synopsis AX_AUTO_INCLUDE_HEADERS(INCLUDE-FILE ...)
dnl
dnl Given a space-separated list of INCLUDE-FILEs, AX_AUTO_INCLUDE_HEADERS
dnl will output a conditional #include for each INCLUDE-FILE.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_AUTO_INCLUDE_HEADERS], [dnl
AC_FOREACH([AX_Header], [$1], [dnl
m4_pushdef([AX_IfDef], AS_TR_CPP(HAVE_[]AX_Header))dnl
[#]ifdef AX_IfDef
[#] include <AX_Header>
[#]endif
m4_popdef([AX_IfDef])dnl
])])


dnl @synopsis AX_FILE_PROC_CMDLINE
dnl
dnl Define PROC_CMD_LINE as the name of a file that represents the calling
dnl process's original command line if such a file exists.  Define
dnl PROC_CMD_LINE_TYPE as 0 if PROC_CMD_LINE is not to be used; 1 if it's
dnl a template that replaces %d with the process ID; or, 2 for a complete
dnl filename.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_FILE_PROC_CMDLINE], [dnl
  AC_CACHE_CHECK([how to read a process's original command line],
    [ax_cv_file_proc_cmdline],
    [ax_cv_file_proc_cmdline=unknown
     for proc_id in self curproc ; do
       if test -r /proc/$proc_id/cmdline ; then
         ax_cv_file_proc_cmdline=/proc/$proc_id/cmdline
         break
       fi
     done
     if test "$ax_cv_file_proc_cmdline" = unknown -a \
             -r /proc/$$/cmdline ; then
       ax_cv_file_proc_cmdline="/proc/%d/cmdline"
     fi])
  if test "$ax_cv_file_proc_cmdline" != unknown ; then
    AC_DEFINE_UNQUOTED([PROC_CMD_LINE],
      ["$ax_cv_file_proc_cmdline"],
      [Define as the name of file that contains a process's original command line.])
  fi
  case "$ax_cv_file_proc_cmdline" in
    unknown)
      proc_cmdline_type=0
      ;;

    "*%d*")
      proc_cmdline_type=1
      ;;

    *)
      proc_cmdline_type=2
      ;;
  esac
  AC_DEFINE_UNQUOTED([PROC_CMD_LINE_TYPE],
    [$proc_cmdline_type],
    [Define as 0 if PROC_CMD_LINE is not to be used; 1 if it's a template that replaces %d with the process ID; or, 2 for a complete filename.])
])


dnl @synopsis AX_SAVE_WARNINGS
dnl
dnl Redefine the AC_MSG_WARN macro so that it not only outputs a
dnl warning message to screen and to config.log but also to a new
dnl config.warn file.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_SAVE_WARNINGS], [dnl
AC_REQUIRE([AC_PROG_AWK])
m4_copy([AC_MSG_WARN], [AX_MSG_WARN_ORIGINAL])
m4_copy_force([AX_MSG_WARN], [AC_MSG_WARN])
rm -f config.warn
])

dnl @synopsis AX_MSG_WARN(PROBLEM)
dnl
dnl Do most of the work for AX_SAVE_WARNINGS.  This macro should not be
dnl called directly but only through AC_MSG_WARN.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_MSG_WARN], [dnl
AC_REQUIRE([AC_PROG_AWK])
if true ; then
  AX_MSG_WARN_ORIGINAL([$1])
  if test ! -e config.warn ; then
    touch config.warn
  fi
  echo "_AS_QUOTE([$1])" | \
    [$]AWK 'NR==1 {sub(/^ */, ""); print " * " [$]0}; \
            NR>1 {sub(/^ */, ""); print "   " [$]0}' >> config.warn
fi
])

dnl @synopsis AX_SHOW_WARNINGS
dnl
dnl When configure is finished, AX_SHOW_WARNINGS should be called to
dnl output (and subsequently delete) the list of accumulated warning
dnl messages.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_SHOW_WARNINGS], [dnl
m4_copy_force([AX_MSG_WARN_ORIGINAL], [AC_MSG_WARN])
_AS_ECHO([===========================================================================])
if test -e config.warn ; then
  _AS_ECHO([The following warning messages were issued during configuration:])
  _AS_ECHO()
  cat config.warn >&AS_MESSAGE_FD
  _AS_ECHO()
  if test `wc -l config.warn | $AWK '{print [$]1}'` -eq 1 ; then
    _AS_ECHO([The warning message shown above is also included in config.log where it is preceded by a detailed technical explanation.])
  else
    _AS_ECHO([Each of the warning messages shown above is also included in config.log where it is preceded by a detailed technical explanation.])
  fi
  _AS_ECHO()
  _AS_ECHO([In addition, the Troubleshooting chapter of the coNCePTuaL User's Guide lists common warning messages and explains how to address them.])
  rm -f config.warn
else
  _AS_ECHO([Configuration completed without any errors or warnings.])
fi
_AS_ECHO([===========================================================================])
])


dnl @synopsis AX_CHECK_SYMBOLS(SYMBOL..., TYPE, [INCLUDES],
dnl                            [ACTION-IF-FOUND], [ACTION-IF-NOT-FOUND])
dnl
dnl For each space-separated symbol SYMBOL, define HAVE_SYMBOL if SYMBOL
dnl exists at link time.  TYPE is the symbol type (e.g., "int").  INCLUDES
dnl is a list of #include lines to utilize.  ACTION-IF-FOUND is shell code
dnl to execute if SYMBOL is defined.  ACTION-IF-NOT-FOUND is shell code to
dnl execute if SYMBOL is not defined.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_CHECK_SYMBOLS], [dnl
  AC_FOREACH([AX_Symbol],
    [$1],
    [AC_CACHE_CHECK([if ]AX_Symbol[ is defined],
      [ax_cv_decl_]AX_Symbol,
      [AC_TRY_LINK([$3],
        [
extern $2 ]AX_Symbol[;

(void) printf ("I see %p.\n", (void *)&]AX_Symbol[);
        ],
        [ax_cv_decl_]AX_Symbol[=yes],
        [ax_cv_decl_]AX_Symbol[=no])])
    AS_IF([test "$ax_cv_decl_]AX_Symbol[" = yes],
      [AC_DEFINE(AS_TR_CPP(HAVE_[]AX_Symbol), ,
         [Define unless using the symbol `]AX_Symbol[' results in a link error.])
       $4],
      [$5])
  ])
])


dnl @synopsis AX_PYTHON_C_COMPATIBILITY([ACTION-IF-COMPATIBLE],
dnl                                     [ACTION-IF-NOT-COMPATIBLE])
dnl
dnl Determine if a Python extension module written in C and compiled
dnl using Python's distutils module (and therefore whatever C compiler and
dnl flags Python favors) can successfully link with and invoke a library
dnl function compiled with whatever the C compiler and flags are known to
dnl Autoconf.  If a sample extension module is invoked successfully, the
dnl commands in ACTION-IF-COMPATIBLE are executed.  Otherwise, the
dnl commands in ACTION-IF-NOT-COMPATIBLE are executed.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_PYTHON_C_COMPATIBILITY], [dnl
  AC_REQUIRE([AC_PROG_CC])
  AC_CACHE_CHECK([if the Python-extension C compiler is compatible with $CC],
    [ax_cv_prog_python_c_compat],
    [ax_cv_prog_python_c_compat=no
     # Python extensions, step 1: Compile a tiny C library (conftest2.c).
     orig_CC="$CC"
     CC="./libtool --mode=compile $CC"
     rm -f .libs/conftest.$ac_objext > /dev/null 2>&1
     AC_COMPILE_IFELSE([int return_123 (void) {return 123;}],
       [can_compile_c=yes
        cp conftest.$ac_objext conftest.$ac_objext.BAK > /dev/null 2>&1
        cp .libs/conftest.$ac_objext conftest.$ac_objext.BAK > /dev/null 2>&1
        cp conftest.$ac_ext conftest.$ac_ext.BAK > /dev/null 2>&1],
       [AC_MSG_WARN([Not building the Python interface to the coNCePTuaL run-time library because the two would be incompatible])
        BUILD_PYMODULE=no])
     CC="$orig_CC"
     if test "$can_compile_c" = yes ; then
       cp conftest.$ac_objext.BAK conftest2.$ac_objext
       cp conftest.$ac_ext.BAK conftest2.$ac_ext

       # Python extensions, step 2: Create a Python setup file
       # (conftest-setup.py) and a Python extension module (conftest.c).
       cat <<SETUP_PY > conftest-setup.py
from distutils.core import setup, Extension
setup(ext_modules=@<:@Extension("conftest", @<:@"conftest.$ac_ext"@:>@,
                             extra_objects=@<:@"conftest2.$ac_objext"@:>@)@:>@)
SETUP_PY
       cat <<EXTMOD > conftest.c
  #include <Python.h>

  extern int return_123 (void);

  PyObject *do_something (PyObject *self, PyObject *args)
  {
    return Py_BuildValue("i", return_123());
  }

  static PyMethodDef methods@<:@@:>@ = {
    {"do_something", do_something, METH_VARARGS},
    {NULL, NULL}
  };

  void initconftest()
  {
      (void) Py_InitModule("conftest", methods);
  }
EXTMOD

       # Python extensions, step 3: Build and install the Python module
       # in a subdirectory of the current directory.
       AC_TRY_COMMAND([$PYTHON conftest-setup.py install --install-platlib=conftest-install >&2])
       if test "$?" -eq 0 ; then
         # Python extensions, step 4: Import, invoke, and validate the
         # extension emodule.
         cat <<IMPEXT > conftest.sh
  PYTHONPATH=conftest-install:$PYTHONPATH
  export PYTHONPATH
  $PYTHON -c 'import sys, conftest; sys.exit(conftest.do_something() != 123)'
IMPEXT
         AC_TRY_COMMAND([$SHELL -x conftest.sh >&2])
         if test "$?" -eq 0 ; then
           # Success!
           ax_cv_prog_python_c_compat=yes
         fi
       fi
     fi
     rm -rf build conftest-install
     rm -f conftest.$ac_ext conftest2.$ac_ext conftest2.$ac_objext conftest.sh
  ])
  AS_IF([test "$ax_cv_prog_python_c_compat" = yes], [$1], [$2])
])


dnl @synopsis AX_FUNC_VA_COPY
dnl
dnl If stdarg.h defines va_copy(), define HAVE_VA_COPY.  Otherwise, if
dnl stdarg.h defines __va_copy(), define HAVE___VA_COPY.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_FUNC_VA_COPY], [dnl
  AC_CACHE_CHECK([if we have va_copy()],
    [ax_cv_func_va_copy],
    [AC_EGREP_CPP([yes],
      [
#include <stdarg.h>
#ifdef va_copy
yes
#else
no
#endif
      ],
      [ax_cv_func_va_copy=yes],
      [ax_cv_func_va_copy=no])])
  if test "$ax_cv_func_va_copy" = yes ; then
    AC_DEFINE([HAVE_VA_COPY], ,
      [Define if stdarg.h defines a va_copy() macro.])
  else
    AC_CACHE_CHECK([if we have __va_copy()],
      [ax_cv_func___va_copy],
      [AC_EGREP_CPP([yes],
        [
  #include <stdarg.h>
  #ifdef __va_copy
  yes
  #else
  no
  #endif
        ],
        [ax_cv_func___va_copy=yes],
        [ax_cv_func___va_copy=no])])
    if test "$ax_cv_func___va_copy" = yes ; then
      AC_DEFINE([HAVE___VA_COPY], ,
        [Define if stdarg.h defines a __va_copy() macro.])
    fi
  fi
])


dnl @synopsis AX_PROG_LIBTOOL_WORKS([ACTION-IF-TRUE], [ACTION-IF-FALSE])
dnl
dnl Test if libtool is able to compile and link a simple library.  If it
dnl can, the commands in ACTION-IF-TRUE are executed.  If not, the
dnl commands in ACTION-IF-FALSE are executed.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_PROG_LIBTOOL_WORKS], [dnl
  AC_REQUIRE([AC_PROG_CC])
  AC_REQUIRE([AC_PROG_LIBTOOL])
  AC_CACHE_CHECK([if libtool can create a simple library],
    [ax_cv_prog_libtool_works],
    [ax_cv_prog_libtool_works=no
     echo 'int dummy (void) {return 123;}' > conftest.c
     AC_TRY_COMMAND([./libtool --mode=compile $CC -c $CFLAGS $CPPFLAGS conftest.c -o conftest.lo >&AS_MESSAGE_LOG_FD])
     if test $ac_status -eq 0 ; then
       AC_TRY_COMMAND([./libtool --mode=link $CC -rpath `pwd` -version-info 0:0:0 -o libconftest.la $CFLAGS $CPPFLAGS $LDFLAGS conftest.lo >&AS_MESSAGE_LOG_FD])
       if test $ac_status -eq 0 ; then
         AC_TRY_COMMAND([./libtool --mode=install cp libconftest.la `pwd` >&AS_MESSAGE_LOG_FD])
         if test $ac_status -eq 0 ; then
           ax_cv_prog_libtool_works=yes
         fi
       fi
     fi
     rm -f *conftest* .libs/*conftest* >/dev/null 2>&1
     rmdir .libs >/dev/null 2>&1])
  AS_IF([test "$ax_cv_prog_libtool_works" = yes], [$1], [$2])
])


dnl @synopsis AX_CHECK_LIB (LIBRARY, FUNCTION, [ACTION-IF-FOUND], [ACTION-IF-NOT-FOUND], [OTHER-LIBRARIES])
dnl
dnl Modify AC_CHECK_LIB by subtracting off $ignored_libs from LIBRARY.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_CHECK_LIB], [dnl
  m4_ifval([$3], , [AH_CHECK_LIB([$1])])dnl
  AS_LITERAL_IF([$1],
		[AS_VAR_PUSHDEF([ac_Lib], [ac_cv_lib_$1_$2])],
		[AS_VAR_PUSHDEF([ac_Lib], [ac_cv_lib_$1''_$2])])dnl
  remaining_libs=`$PYTHON $srcdir/makehelper.py list-diff "$1" "$ignored_libs" nonexistent`
  AC_CACHE_CHECK([for $2 in -l$remaining_libs], [ac_Lib],
  [ac_check_lib_save_LIBS=$LIBS
  LIBS="-l$remaining_libs $5 $LIBS"
  AC_LINK_IFELSE([AC_LANG_CALL([], [$2])],
		 [AS_VAR_SET([ac_Lib], [yes])],
		 [AS_VAR_SET([ac_Lib], [no])])
  LIBS=$ac_check_lib_save_LIBS])
  AS_IF([test AS_VAR_GET([ac_Lib]) = yes],
	[m4_default([$3], [AC_DEFINE_UNQUOTED(AS_TR_CPP(HAVE_LIB$remaining_libs))
    LIBS="-l$remaining_libs $LIBS"
  ])],
	[$4])dnl
  AS_VAR_POPDEF([ac_Lib])dnl
])


dnl @synopsis AX_SEARCH_LIBS (FUNCTION, SEARCH-LIBS, [ACTION-IF-FOUND], [ACTION-IF-NOT-FOUND], [OTHER-LIBRARIES])
dnl
dnl Modify AC_SEARCH_LIBS by subtracting off $ignored_libs from SEARCH-LIBS.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_SEARCH_LIBS], [dnl
  remaining_libs=`$PYTHON $srcdir/makehelper.py list-diff "$2" "$ignored_libs"`
  AC_SEARCH_LIBS([$1], [$remaining_libs], [$3], [$4], [$5])
])


dnl @synopsis AX_CHECK_REQUIRES_LIBM (FUNCTION, STATEMENT)
dnl
dnl Append "-lm" to LIBS if required to link STATEMENT.
dnl
dnl @version $Id: acinclude.m4,v 3.32 2010-08-10 03:06:25 pakin Exp $
dnl @author Scott Pakin <pakin@lanl.gov>
dnl
AC_DEFUN([AX_CHECK_REQUIRES_LIBM], [dnl
  AC_REQUIRE([AC_PROG_EGREP])
  AC_MSG_CHECKING([for $1])
  ax_func_to_define=no
  AC_TRY_LINK([#include <math.h>],
   [$2],
   [dnl
    # Function $1 was found either as an intrinsic
    # or as a definition in math.h.
    AC_MSG_RESULT([yes])
    ax_func_to_define=$1],
   [dnl
    # Function $1 may be a library function.  Look for it in -lm.
    AC_MSG_RESULT([no])
    if test `echo " $LIBS " | $EGREP -c " -lm "` -eq 0 ; then
      AC_CHECK_LIB([m], [$1])
    fi])
  if test "$ax_func_to_define" != no ; then
    AC_DEFINE_UNQUOTED(AS_TR_CPP([HAVE_$ax_func_to_define]))
  fi
])
