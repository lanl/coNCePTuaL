/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * header shared across all run-time-library files
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2011, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2011).  Los Alamos National Security, LLC.  This software
 * was produced under U.S. Government contract DE-AC52-06NA25396
 * for Los Alamos National Laboratory (LANL), which is operated by
 * Los Alamos National Security, LLC (LANS) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR LANS
 * MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
 * FOR THE USE OF THIS SOFTWARE. If software is modified to produce
 * derivative works, such modified software should be clearly marked,
 * so as not to confuse it with the version available from LANL.
 * 
 * Additionally, redistribution and use in source and binary forms,
 * with or without modification, are permitted provided that the
 * following conditions are met:
 * 
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 * 
 *   * Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer
 *     in the documentation and/or other materials provided with the
 *     distribution.
 * 
 *   * Neither the name of Los Alamos National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY LANS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LANS OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
 * OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
 * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * ----------------------------------------------------------------------
 */

#ifndef _RUNTIMELIB_H_
#define _RUNTIMELIB_H_


/********************
 * Header inclusion *
 ********************/

#define NCPTL_LIBRARY_INTERNALS
#include "config.h"
/* Avoid redefining NCPTL_INT_MIN and NCPTL_INT_MAX. */
#undef NCPTL_INT_MIN
#undef NCPTL_INT_MAX
#include "ncptl.h"


/**********
 * Macros *
 **********/

/* Call ncptl_fatal() with a message and a system error code or name. */
#ifdef HAVE_STRERROR
# define NCPTL_SYSTEM_ERROR(MSG)                        \
  do {                                                  \
    if (strerror(errno))                                \
      ncptl_fatal (MSG " (%s)", strerror(errno));       \
    else                                                \
      ncptl_fatal (MSG " (errno=%d)", errno);           \
  }                                                     \
  while (0)
#elif HAVE_DECL_SYS_ERRLIST
# define NCPTL_SYSTEM_ERROR(MSG)                        \
  do {                                                  \
    if (errno < sys_nerr)                               \
      ncptl_fatal (MSG " (%s)", sys_errlist[errno]);    \
    else                                                \
      ncptl_fatal (MSG " (errno=%d)", errno);           \
  }                                                     \
  while (0)
#else
# define NCPTL_SYSTEM_ERROR(MSG)                        \
  ncptl_fatal (MSG " (errno=%d)", errno)
#endif

/* Deal with systems that can't malloc() or realloc() a zero-byte buffer. */
#define malloc0(S) malloc((S) ? (size_t)(S) : sizeof(int))
#define realloc0(B,S) realloc((B), (S) ? (size_t)(S) : sizeof(int))

/* If necessary, use strtoq(), _strtoi64(), or strtol() as a
 * replacement for strtoll(). */
#ifndef HAVE_STRTOLL
# if defined(HAVE_STRTOQ)
#  define strtoll strtoq
#  define strtoull strtouq
# elif defined(HAVE__STRTOI64)
#  define strtoll _strtoi64
#  define strtoull _strtoui64
# elif defined(STRTOL_IS_STRTOLL)
#  define strtoll strtol
#  define strtoull strtoul
# endif
#endif

/* Assume that no line from a file contains more than this many characters. */
#define NCPTL_MAX_LINE_LEN 4096

/* Specify an upper bound on the number of signals the OS supports. */
#ifndef NUM_SIGNALS
# ifdef NSIG
#  define NUM_SIGNALS NSIG
# else
#  define NUM_SIGNALS 256
# endif
#endif

/* Define an arbitrary 64-bit number to use for testing memory
 * allocation. */
#define ALLOC_MAGIC_COOKIE UINT64_C(0x636F4E4365505475)    /* "coNCePTu" */

/* Define a string to precede a list of signals specified by --no-trap. */
#define SIGNAL_CMDLINE_DESC "List of signals that should not be trapped"

#if defined(MAXDOUBLE)
# define LARGEST_DOUBLE_VALUE MAXDOUBLE
#elif defined(DBL_MAX)
# define LARGEST_DOUBLE_VALUE DBL_MAX
#else
# error cannot determine the largest double value
#endif

#ifdef HAVE_ASM_VOLATILE_CYCLES
  /* We know we have a GCC-like compiler, so it should be safe to use asm volatile. */
# if defined (HAVE_IA32_CPU)
#  define READ_CYCLE_COUNTER(VAR)          \
    do {                                   \
      asm volatile ("rdtsc" : "=A" (VAR)); \
    } while (0)
# elif defined (HAVE_X86_64_CPU)
#  define READ_CYCLE_COUNTER(VAR)                       \
    do {                                                \
      uint32_t lo, hi;                                  \
      asm volatile("rdtsc" : "=a" (lo), "=d" (hi));     \
      VAR = ((uint64_t)hi <<32) | lo;                   \
    } while(0)
# elif defined (HAVE_IA64_CPU)
#  define READ_CYCLE_COUNTER(VAR)                                \
    do {                                                         \
      asm volatile ("mov %0 =ar.itc" : "=r" (VAR) : : "memory"); \
    } while (0)
# elif defined (HAVE_ALPHA_CPU)
#  define READ_CYCLE_COUNTER(VAR)                           \
    do {                                                    \
      asm volatile ("rpcc %0 ; zapnot %0, 15, %0"           \
        : "=r" (VAR) : : "memory");                         \
    } while (0)
# elif defined (HAVE_PPC_CPU)
#  define READ_CYCLE_COUNTER(VAR)                               \
    do {                                                        \
      uint32_t tbu1, tbu2, tbl;                                 \
      asm volatile ("\n"                                        \
                    "0:\n"                                      \
                    "\tmftbu\t%0\n"                             \
                    "\tmftb\t%2\n"                              \
                    "\tmftbu\t%1\n"                             \
                    "\tcmpw\t%1,%0\n"                           \
                    "\tbne\t0b"                                 \
                    : "=r" (tbu1), "=r" (tbu2), "=r" (tbl));    \
      VAR = ((uint64_t)tbu1 << 32) | tbl;                       \
    } while (0)
# else
#  error Reading the cycle counter is not defined on this architecture
# endif
#elif defined(HAVE_CCC_ALPHA_RPCC)
  /* Special case for ccc on Alpha */
# define READ_CYCLE_COUNTER(VAR)                                \
    do {                                                        \
      VAR = asm ("rpcc %v0");                                   \
      VAR &= 0xFFFFFFFF;   /* Lousy 32-bit cycle counter */     \
    } while (0)
#endif

/* Determine if we'll be able to find the number of CPU cycles per
 * microsecond. */
#if !defined(FORCE_GETTIMEOFDAY) && !defined(FORCE_MPI_WTIME)
# if defined(USE_PAPI) || \
     (defined(HAVE_INVENT_H) && defined(HAVE_GETINVENT)) || \
     (defined(HAVE_MACHINE_HAL_SYSINFO_H) && defined(GSI_CPU_INFO)) || \
     (defined(HAVE_SYSCTL) && defined(CTL_HW) && \
      (defined(HW_CPUSPEED) || defined(HW_TB_FREQ))) || \
     defined(TIMEBASE_FREQUENCY_FILENAME) || \
     defined(HAVE_PROC_CPUINFO_FREQ) || \
     defined(HAVE_KSTAT_DATA_LOOKUP) || \
     defined(_WIN32) || \
     defined(CYCLES_PER_USEC)
#  define HAVE_CYCLES_PER_USEC
# endif
#endif

/* Determine the type of timer that ncptl_time() should use.  These
 * definitions must be kept up-to-date with both ncptl_time() and
 * log_write_prologue_timer(). */
#if defined(FORCE_GETTIMEOFDAY)
# define NCPTL_TIMER_TYPE 1         /* gettimeofday() (forced by the user) */
#elif defined(FORCE_MPI_WTIME)
# define NCPTL_TIMER_TYPE 9         /* MPI_Wtime() (forced by the user) */
#elif defined(READ_CYCLE_COUNTER) && defined(HAVE_CYCLES_PER_USEC) && !defined(_WIN32)
# ifdef HAVE_32BIT_CYCLE_COUNTER
#  define NCPTL_TIMER_TYPE 2        /* Inline assembly language + gettimeofday() */
# else
#  define NCPTL_TIMER_TYPE 3        /* Inline assembly language */
# endif
#elif defined(HAVE_GET_CYCLES) && defined(HAVE_CYCLES_PER_USEC)
# define NCPTL_TIMER_TYPE 4         /* Linux's get_cycles() function */
#elif defined(USE_PAPI)
# define NCPTL_TIMER_TYPE 5         /* PAPI's PAPI_get_real_usec() function */
#elif defined(HAVE_CLOCK_GETTIME) && defined(CLOCKID)
# define NCPTL_TIMER_TYPE 6         /* SysV's clock_gettime() function */
#elif defined(HAVE_DCLOCK)
# define NCPTL_TIMER_TYPE 7         /* Intel supercomputers' dclock() function */
#elif defined(_WIN32)
# define NCPTL_TIMER_TYPE 8         /* Microsoft Windows' QueryPerformanceCounter() function */
#else
# define NCPTL_TIMER_TYPE 1         /* gettimeofday() (nothing else available) */
#endif

/* Determine if we can use AIX's Object Data Manager. */
#if defined(HAVE_STRUCT_CUAT) && defined(HAVE_LIBODM) && defined(HAVE_LIBCFG)
# define ODM_IS_SUPPORTED
#endif

/* When building under Windows with MinGW, symbols for some of the
 * critical signals are not defined.  Define them here with "likely"
 * values. */
#ifndef SIGKILL
# define SIGKILL 9
#endif
#ifndef SIGALRM
# define SIGALRM 14
#endif
#ifndef SIGCHLD
# define SIGCHLD 17
#endif

/* va_copy() was added late to the C standard (i.e., not until C99).
 * Some pre-C99 C compilers define __va_copy().  The Autoconf manual
 * recommends using a memcpy() if neither is defined. */
#ifndef HAVE_VA_COPY
# ifdef HAVE___VA_COPY
#  define va_copy __va_copy
# else
#  define va_copy(DEST,SRC) memcpy(&DEST, &SRC, sizeof(va_list))
# endif
#endif

/* Determine if we can use the High-Precision Event Timer (HPET). */
#if defined(HPET_DEVICE) && defined(HAVE_SYS_MMAN_H) && \
    !defined(FORCE_GETTIMEOFDAY) && !defined(FORCE_MPI_WTIME)
# define USE_HPET
#endif

/* Define EXIT_SUCCESS and EXIT_FAILURE if not already defined. */
#ifndef EXIT_SUCCESS
# define EXIT_SUCCESS 0
#endif
#ifndef EXIT_FAILURE
# define EXIT_FAILURE 1
#endif

/* Define lowercase required_argument and no_argument if all we have
 * are their uppercase counterparts (as is the case in some versions
 * of getopt.h). */
#ifndef required_argument
# define required_argument REQUIRED_ARG
#endif
#ifndef no_argument
# define no_argument NO_ARG
#endif

/* The Cell BE's SPUs lack a getcwd() function. */
#ifndef HAVE_GETCWD
# define getcwd(BUF,SIZE) NULL
#endif


/*********************
 * Type declarations *
 *********************/

/* Define a type for pointers to signal handler functions. */
typedef RETSIGTYPE (*SIGHANDLER) (int);


/* Describe in the detail the system we're using. */
typedef struct {
  char *hostname;            /* Machine name */
  char *arch;                /* System architecture */
  char *os;                  /* Operating system */
  char *osdist;              /* Operating system distribution */
  char *computer;            /* Computer make and model */
  char *bios;                /* BIOS vendor and version */
  int contexts_per_node;     /* Total number of compute contexts (threads*cores*dies*sockets) per node */
  int threads_per_core;      /* Number of hardware threads per CPU core */
  int cores_per_socket;      /* Number of cores in each CPU socket */
  int sockets_per_node;      /* Number of sockets in the node */
  char *cpu_vendor;          /* Name of the CPU vendor */
  char *cpu_model;           /* Name of the CPU model */
  double cpu_freq;           /* CPU frequency in hertz */
  char *cpu_flags;           /* CPU flags (hardwired or bios-settable) */
  double timer_freq;         /* Cycle-counter frequency in hertz */
  uint64_t pagesize;         /* OS page size in bytes */
  uint64_t physmem;          /* Physical memory size in bytes */
  NCPTL_QUEUE *networks;     /* List of network devices */
} SYSTEM_INFORMATION;


/* Describe a single recyclable message buffer. */
typedef struct {
  void *buffer;              /* Unaligned version of the buffer */
  ncptl_int bytes;           /* # of bytes in BUFFER */
} MESSAGE_MEM;


/* Define a bijection between (virtual) task IDs to (physical)
 * processor IDs. */
typedef struct {
  ncptl_int numtasks;       /* Number of entries in the following arrays */
  ncptl_int *virt2phys;     /* Map from virtual to physical */
  ncptl_int *phys2virt;     /* Map from physical to virtual */
} NCPTL_VIRT_PHYS_MAP;

#endif
