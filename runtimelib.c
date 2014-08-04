/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * core operations
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2014, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2014).  Los Alamos National Security, LLC.  This software
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
 *
 * ----------------------------------------------------------------------
 */

#include "runtimelib.h"


/**********
 * Macros *
 **********/

/* ASCI Red lacks a getppid() function. */
#ifndef HAVE_GETPPID
# define getppid() (-1)
#endif

/* Define a macro to abort the program with an internal error. */
#define NCPTL_FATAL_INTERNAL()                                          \
do {                                                                    \
  ncptl_fatal ("Internal error in %s, line %d", __FILE__, __LINE__);    \
} while (0)

/* MinGW (on Microsoft Windows) lacks a kill() function. */
#ifndef HAVE_KILL
# define kill(PID,SIG)
#endif

/* Define a sleep() function if we don't have sleep() itself. */
#ifndef HAVE_SLEEP
# ifdef _WIN32
#  define sleep(S) Sleep(1000*(S))
#  define HAVE_SLEEP
# else
#  define sleep(S)
# endif
#endif


/*********************
 * Type declarations *
 *********************/

/* Define a key:value type that matches what ncptl_sig2num() returns. */
typedef struct {
  char *name;
  int number;
} NAMENUMBER;


/************************************
 * Imported variables and functions *
 ************************************/

extern int ncptl_unsync_rand_state_seeded;
extern void ncptl_log_shutdown (const char *, va_list);
extern void ncptl_init_genrand(RNG_STATE *, uint64_t);
extern uint32_t ncptl_genrand_int32(RNG_STATE *);
extern int64_t ncptl_genrand_int63(RNG_STATE *);
extern uint64_t ncptl_genrand_int64(RNG_STATE *);
extern const NAMENUMBER *ncptl_sig2num (const char *, unsigned int);
extern void ncptl_log_add_comment (const char *, const char *);
extern void ncptl_discern_system_information (SYSTEM_INFORMATION *);
#ifdef HAVE_DECL_STRSIGNAL
# if HAVE_DECL_STRSIGNAL == 0
/* I've used an ecc installation that fails to declare strsignal(). */
extern char *strsignal (int);
# endif
#endif


/*******************************
 * Internal variable (needs to *
 * appear early in this file)  *
 *******************************/

/* Dummy variable to prevent whiny C compilers from complaining about
 * unused function parameters. */
static volatile int dummyvar;


/******************************************
 * Library-global variables and functions *
 ******************************************/

/* Name of the executable file and program arguments (set if and when
 * ncptl_parse_command_line() is called) */
char *ncptl_progname = "coNCePTuaL";
int ncptl_argc_copy = 0;
char **ncptl_argv_copy = NULL;

/* Information about the hardware and operating system */
SYSTEM_INFORMATION systeminfo;

/* # of timebase (and usually CPU) cycles per microsecond */
#ifdef HAVE_CYCLES_PER_USEC
uint64_t ncptl_cycles_per_usec = 1;   /* Until ncptl_init() is called, pretend we have a really, really slow clock (1 MHz). */
# ifdef _WIN32
uint64_t ncptl_cycles_per_sec = 1;    /* Microsoft Windows has only low precision timers. */
# endif
#endif

/* Various HPET-related values */
#ifdef USE_HPET
volatile uint64_t *ncptl_hpet_timer = NULL; /* Pointer to the main HPET counter */
uint64_t ncptl_hpet_period_fs = 0;          /* HPET period in femptoseconds */
int ncptl_hpet_works = 0;                   /* 1=HPET works; 0=it doesn't */
#endif

/* Mean # of microseconds of overhead involved in invoking ncptl_time() */
uint64_t ncptl_time_overhead = (uint64_t)(~0);

/* Difference between successive readings of ncptl_time() */
double ncptl_time_delta_mean = 0.0;
double ncptl_time_delta_stddev = 0.0;

/* Actual delay incurred when sleeping using ncptl_udelay() */
double ncptl_sleep_mean = 0.0;
double ncptl_sleep_stddev = 0.0;

/* Difference between successive readings of ncptl_process_time() */
double ncptl_proc_time_delta_mean = 0.0;
double ncptl_proc_time_delta_stddev = 0.0;

/* Seed for the random-number generator */
int ncptl_rng_seed = 0;

/* The process's physical ID */
ncptl_int ncptl_self_proc;

/* List of signals the user doesn't want us to trap */
int ncptl_no_trap_signal[NUM_SIGNALS];

/* Some systems that have a working fork() function that happens to be
 * incompatible with a particular communication library.  We therefore
 * enable the user to set the NCPTL_NOFORK environment variable to
 * inhibit all fork()-calling functions (fork(), system(), popen(),
 * etc.). */
#ifdef HAVE_WORKING_FORK
int ncptl_fork_works = 1;
#else
int ncptl_fork_works = 0;
#endif

/* Specify the log-file checkpoint interval in microseconds. */
uint64_t ncptl_log_checkpoint_interval = (uint64_t) 60000000;


/* Install a signal handler and store the value of the previous signal
 * handler.  Errors can be ignored or cause the application to
 * abort. */
void ncptl_install_signal_handler (int signalnum,
                                   SIGHANDLER newhandler,
                                   SIGHANDLER *oldhandler,
                                   int abort_on_failure)
{
  int success;               /* 1=success; 0=failure */
  SIGHANDLER prevhandler;    /* Value to assign to oldhandler */

  /* Install the signal handler. */
#ifdef HAVE_SIGACTION
  struct sigaction newhandlerinfo;
  struct sigaction oldhandlerinfo;

  newhandlerinfo.sa_handler = newhandler;
  sigemptyset (&newhandlerinfo.sa_mask);
  newhandlerinfo.sa_flags = 0;
  success = (sigaction(signalnum, &newhandlerinfo, &oldhandlerinfo) != -1);
  prevhandler = oldhandlerinfo.sa_handler;
#else
  prevhandler = signal (signalnum, newhandler);
  success = (prevhandler != SIG_ERR);
#endif

  /* Optionally store the old signal handler and optionally abort the
   * program on failure. */
  if (success) {
    if (oldhandler)
      *oldhandler = prevhandler;
  }
  else
    if (abort_on_failure) {
#ifdef HAVE_STRSIGNAL
      ncptl_fatal ("Failed to register a handler for signal %d (%s)",
                   signalnum, strsignal(signalnum));
#else
      ncptl_fatal ("Failed to register a handler for signal %d",
                   signalnum);
#endif
    }
}


#ifdef HAVE_GETRUSAGE
/* Return the process time (user or OS) in microseconds. */
uint64_t ncptl_process_time (int user0sys1)
{
  struct rusage usageinfo;

  if (getrusage (RUSAGE_SELF, &usageinfo) == -1)
    NCPTL_SYSTEM_ERROR ("getrusage() failed");
  if (user0sys1 == 0)
    return usageinfo.ru_utime.tv_sec*INT64_C(1000000) + usageinfo.ru_utime.tv_usec;
  if (user0sys1 == 1)
    return usageinfo.ru_stime.tv_sec*INT64_C(1000000) + usageinfo.ru_stime.tv_usec;
  NCPTL_FATAL_INTERNAL();
  return (uint32_t)(-1);             /* Appease idiotic compilers. */
}


/* Return the number of major and minor page faults. */
void ncptl_page_fault_count (uint64_t *major, uint64_t *minor)
{
  struct rusage usageinfo;

  if (getrusage (RUSAGE_SELF, &usageinfo) == -1)
    NCPTL_SYSTEM_ERROR ("getrusage() failed");
  *major = (uint64_t) usageinfo.ru_majflt;
  *minor = (uint64_t) usageinfo.ru_minflt;
}
#endif


/* Return the total number of interrupts received by the node since
 * boot time or -1 if unknown. */
uint64_t ncptl_interrupt_count (void)
{
  uint64_t numints = (uint64_t)(~0);  /* Total number of interrupts seen on all CPUs */

#if defined(HAVE_KSTAT_DATA_LOOKUP)
  /* Use the kstat interface to tally the number of interrupts. */
  kstat_ctl_t *kcontrol;         /* kstat control */
  kstat_t *thekstat;             /* The kstat itself */
  kstat_named_t *kstatdata;      /* Value encountered */

  /* Open the kernel statistics. */
  if (!(kcontrol=kstat_open()))
    return numints;

  /* Iterate over all kstats until we find all cpu/intrstat values. */
  numints = 0;
  for (thekstat=kstat_lookup(kcontrol, "cpu", -1, "intrstat");
       thekstat;
       thekstat=(kstat_t *)thekstat->ks_next) {
    int level;              /* Interrupt level number */

    /* Find a cpu/intrstat kstat. */
    if (kstat_read(kcontrol, thekstat, NULL) == -1)
      /* We're doomed if we can't read the kstat. */
      return (uint64_t)(~0);
    if (strcmp(thekstat->ks_module, "cpu") || strcmp(thekstat->ks_name, "intrstat"))
      /* This isn't a kstat we care about -- continue with the next one. */
      continue;

    /* Search for interrupt levels 0..255 and store each interrupt's tally. */
    for (level=0; level<256; level++) {
      char levelname[15];     /* "level-" followed by the level number */

      sprintf (levelname, "level-%d", level);
      if ((kstatdata=(kstat_named_t *)kstat_data_lookup (thekstat, levelname))
          && kstatdata->data_type == KSTAT_DATA_UINT64)
        numints += kstatdata->value.ui64;
    }
  }

  /* Close the kernel statistics and return. */
  (void) kstat_close (kcontrol);
  return numints;
#elif defined(USE_PROC_INTERRUPTS)
  /* Attempt to parse the contents of the /proc/interrupts file. */
# define MAX_INTR_LINE_LEN 1048576
  FILE *intfile;               /* Handle to /proc/interrupts */
  char *oneline = (char *) ncptl_malloc(MAX_INTR_LINE_LEN, 0);  /* One line of interrupt counts */

  /* Open the file and discard the header line. */
  if (!(intfile=fopen("/proc/interrupts", "r")))
    return numints;
  if (!fgets(oneline, MAX_INTR_LINE_LEN, intfile)) {
    fclose (intfile);
    return numints;
  }

  /* Read the remaining lines one-by-one.  Each line consists of an
   * interrupt number, a tally for each CPU, and a description of the
   * interrupt type and corresponding device driver:
   *
   *  50:          0       1430  IO-SAPIC-level  usb-ohci
   *  53:  843677863          0  IO-SAPIC-level  eth0
   *  54:          0   43858189  IO-SAPIC-level  ioc0
   *
   * Note that the following code will be confused if the description
   * column begins with a number.
   */
  numints = 0;
  while (fgets(oneline, MAX_INTR_LINE_LEN, intfile)) {
    char *word;     /* The current word on the current line */

    for (word=strtok(oneline, " "); word; word=strtok(NULL, " "))
      if (isdigit(word[0])) {
        uint64_t wordints = (uint64_t) strtoll (word, NULL, 10);
        if (errno == ERANGE)
          break;
        numints += wordints;
      }
      else
        break;
  }

  /* Return the tally. */
  fclose (intfile);
  ncptl_free (oneline);
  return numints;
# undef MAX_INTR_LINE_LEN
#else
  /* We don't know how to tally interrupts on this platform. */
  return numints;
#endif
}


/* Return the time of day in seconds. */
unsigned long ncptl_time_of_day (void)
{
#if defined(HAVE_TIME)
  return (unsigned long) time(NULL);
#elif defined(HAVE_GETTIMEOFDAY)
  {
    struct timeval now;
    int result;

    if ((result=gettimeofday(&now, NULL)) == -1)
      ncptl_fatal ("gettimeofday() failed with error code %d", result);
    return now.tv_sec + 1000000*tv_usec;
  }
#else
# error Unable to read the time of day.
#endif
}


/* Parse an environment variable, ENVVAR, as an unsigned 64-bit number
 * and assign the value to VALUE.  Return 1 on success (which includes
 * an unset environment variable) and 0 on failure (viz., a parse
 * error).  VALUE is modified only if ENVVAR is defined and parses
 * correctly. */
int ncptl_envvar_to_uint64 (const char *envvar, uint64_t *value)
{
  char *envstring = getenv(envvar);    /* Value of ENVVAR as a string */
  char *firstbad;                      /* Pointer to first non-digit */
  uint64_t envvalue;                   /* Numerical value of ENVVAR */

  /* An undefined variable is treated as a success but VALUE is left
   * untouched. */
  if (!envstring)
    return 1;

  /* Reject negative numbers even if strtoull() doesn't. */
  if (envstring[0] == '-')
    return 0;

  /* Parse the environment variable using strtoull(). */
  errno = 0;           /* BSD's strtoull() doesn't reset errno on success. */
  envvalue = strtoull (envstring, &firstbad, 10);
  if (errno || firstbad==envstring || *firstbad)
    return 0;          /* Parse error */
  *value = envvalue;
  return 1;
}


/* Wrap a non-inlined ncptl_time_no_hpet() function around the inlined
 * version to ensure that ncptl_time_no_hpet() can be called
 * externally. */
uint64_t ncptl_time_no_hpet (void)
{
  extern inline uint64_t inlined_time_no_hpet (void);

  return inlined_time_no_hpet();
}


/************************************
 * Internal variables and functions *
 ************************************/

/* Pointer to a variable to set upon a SIGALRM */
static volatile int *flag_to_set = NULL;

/* Min. # of iterations of a tight loop we can perform in one microsecond */
static uint64_t spinsperusec = 0;

/* ncptl_udelay() polls cycle counters but not timers that require OS
 * intervention because that might introduce excessive load on the
 * system.  We assume that if ncptl_time_overhead is less than one
 * microsecond then we must have a cycle counter; otherwise, we assume
 * that we're going through the OS. */
#if NCPTL_TIMER_TYPE == 3 || NCPTL_TIMER_TYPE == 4
static int cycle_counter_delay = 1;    /* We know a priori that we have a cycle counter. */
#else
static int cycle_counter_delay = -1;   /* We need to determine dynamically what we have. */
#endif

#ifdef USE_HPET
static int hpet_fd;                /* HPET device file descripor */
static volatile char *hpet_data;   /* Pointer to device memory */
#endif

/* Random variable used by ncptl_random_task() (initialized by
 * ncptl_seed_random_task()) */
static RNG_STATE random_task_state;

/* Allocate space for storing old signal handlers. */
static SIGHANDLER original_handler[NUM_SIGNALS];

/* Signal to send ourself as part of abnormal exit handling. */
static int exit_signal = 0;


/* Restore all signal handlers to their original values. */
static void reinstate_all_signal_handlers (void)
{
  int i;

  for (i=1; i<NUM_SIGNALS; i++)
    if (!ncptl_no_trap_signal[i])
      ncptl_install_signal_handler (i, original_handler[i], NULL, 0);
}


/* Signal handler for SIGALRM */
static RETSIGTYPE set_flag_on_interrupt (int signalnum)
{
  if (flag_to_set) {
    *flag_to_set = 1;
    flag_to_set = NULL;
  }
#ifndef HAVE_SIGACTION
    ncptl_install_signal_handler (signalnum, original_handler[signalnum], NULL, 0);
#else
    dummyvar = signalnum;    /* Convince the compiler that signalnum is not an unused parameter. */
#endif
  return RETSIGVALUE;
}


/* Send a signal to ourself. */
static void signal_self (void)
{
#ifdef HAVE_SIGACTION
  sigset_t selfset;

  /* Make it possible to send exit_signal to ourself from within an
   * exit_signal handler.  Otherwise, the exit_signal would be
   * deferred but never sent because the process would exit first. */
  (void) sigemptyset (&selfset);
  (void) sigaddset (&selfset, exit_signal);
  (void) sigprocmask (SIG_UNBLOCK, &selfset, NULL);
#endif
  kill (getpid(), exit_signal);
}


/* Signal handler for all other signals */
static RETSIGTYPE abort_on_signal (int signalnum)
{
  /* Restore all original signal handlers and prepare to have
   * signalnum resent to ourself when ncptl_fatal() invokes exit(). */
  reinstate_all_signal_handlers();
  exit_signal = signalnum;
  atexit (signal_self);

  /* Notify the user that we're going down on a signal. */
#ifdef HAVE_STRSIGNAL
  ncptl_fatal ("Received signal %d (%s); specify --no-trap=%d to ignore",
               signalnum, strsignal(signalnum), signalnum);
#else
  ncptl_fatal ("Received signal %d; specify --no-trap=%d to ignore",
               signalnum, signalnum);
#endif
  return RETSIGVALUE;
}


/* Convert signal_str to an integer or die trying. */
static int parse_signal (const char *signal_str)
{
  int signalnum;           /* Signal number to return */
  char *endptr;            /* Pointer to the first non-numeric value */
  const NAMENUMBER *signalpair;  /* {signal name, signal number} pair */

  /* See if the signal was specified by name. */
  signalpair = ncptl_sig2num (signal_str, (unsigned int) strlen(signal_str));
  if (signalpair)
    return (int) signalpair->number;

  /* See if the signal was specified by number. */
  signalnum = (int) strtol (signal_str, &endptr, 10);
  if (*endptr)
    ncptl_fatal ("Unable to parse signal \"%s\"", signal_str);
  if (signalnum<0 || signalnum>=NUM_SIGNALS)
    ncptl_fatal ("Signal number \"%d\" is not between 0 and %d",
                 signalnum, NUM_SIGNALS-1);
  return signalnum;
}


/* Parse a comma-separated list of dash-separated numbers. */
static void parse_signal_list (const char *signallist)
{
  char *signalstring;   /* Mutable version of signallist */
  char *range;          /* A single signal or range of signals */
  int i;

  /* Initialize the routine. */
  signalstring = ncptl_strdup (signallist);
  for (i=(int)strlen(signalstring)-1; i>=0; i--)    /* Allow either spaces or commas. */
    if (signalstring[i] == ' ')
      signalstring[i] = ',';

  /* Loop over all comma-separated values. */
  for (range=strtok (signalstring, ",");
       range;
       range=strtok (NULL, ",")) {
    char *dashptr = strchr (range, '-');    /* Pointer to the first dash */
    int firstsignal, lastsignal;            /* Beginning and ending of range */

    /* Parse the range or individual number. */
    if (dashptr && dashptr!=range) {
      *dashptr = '\0';
      firstsignal = parse_signal (range);
      lastsignal = parse_signal (dashptr+1);
    }
    else
      firstsignal = lastsignal = parse_signal (range);
    if (firstsignal > lastsignal)
      ncptl_fatal ("Signal range \"%d-%d\" needs to be written as \"%d-%d\"",
                   firstsignal, lastsignal, lastsignal, firstsignal);

    /* Set a flag for each number in the range. */
    for (i=firstsignal; i<=lastsignal; i++)
      ncptl_no_trap_signal[i] = 1;
  }

  /* Finish up cleanly. */
  ncptl_free (signalstring);
}


/* Convert a string to its numeric value.  The input string is a
 * number with optional coNCePTuaL suffixes. */
static ncptl_int string_to_integer (char *stringval)
{
  char *badintmsg = "\"%s\" is not a valid integer";
  char *suffix;
  int64_t intval = strtoll (stringval, &suffix, 10);

  /* Abort if no characters were valid. */
  if (suffix == stringval)
    ncptl_fatal (badintmsg, stringval);

  /* Process the suffix */
  switch (suffix[0]) {
    /* No suffix */
    case '\0':
      break;

    /* Tebibytes */
    case 'T':
    case 't':
      intval *= 1024;
      /* No break */

    /* Gibibytes */
    case 'G':
    case 'g':
      intval *= 1024;
      /* No break */

    /* Mebibytes */
    case 'M':
    case 'm':
      intval *= 1024;
      /* No break */

    /* Kibibytes */
    case 'K':
    case 'k':
      intval *= 1024;
      if (suffix[1])       /* Something came after the suffix. */
        ncptl_fatal (badintmsg, stringval);
      break;

    /* Base 10 exponent */
    case 'E':
    case 'e': {
      char *expstr = suffix + 1;
      int64_t exponent = strtoll (expstr, &suffix, 10);
      if (suffix[0])       /* We must consume the entire string. */
        ncptl_fatal (badintmsg, stringval);
      intval *= ncptl_func_power ((ncptl_int)10, (ncptl_int)exponent);
    }
      break;

    /* None of the above */
    default:
      ncptl_fatal (badintmsg, stringval);
      break;
  }

  /* Return the modified integer. */
  return intval;
}


#if NCPTL_TIMER_TYPE == 2
/* Define a function that uses a low-precision gettimeofday() with a
 * high-precision but 32-bit cycle counter to return a reasonable
 * 64-bit timer reading. */
static uint64_t fabricate_64_bit_cycle_counter (void)
{
  static uint64_t wrapcycles = UINT64_C(4294967296);  /* Wrap time in cycles */
  struct timeval tod;             /* Current time from gettimeofday() */
  uint64_t fnow;                  /* Current cycle time (fine-grained) */
  static uint64_t fthen = 0;      /* Previous cycle time (fine-grained) */
  uint64_t cnow;                  /* Current cycle time (coarse-grained) */
  static uint64_t cthen = 0;      /* Previous cycle time (coarse-grained) */
  uint64_t felapsed;              /* Elapsed cycle time (fine-grained) */
  uint64_t celapsed;              /* Elapsed cycle time (coarse-grained) */
  uint64_t true_elapsed;          /* Adjusted elapsed cycle time (coarse+fine) */
  static uint64_t true_time = 0;  /* Adjusted cycle time (coarse+fine) */

  /* Measure the current cycle time on both timers. */
  READ_CYCLE_COUNTER (fnow);
  if (gettimeofday(&tod, NULL) == -1)
    NCPTL_SYSTEM_ERROR ("Failed to read the current time");
  cnow = ncptl_cycles_per_usec * (tod.tv_sec*UINT64_C(1000000) + tod.tv_usec);

  /* Use the fine-grained timer to adjust the coarse-grained timer. */
  celapsed = cnow - cthen;
  felapsed = fnow - fthen;
  true_elapsed = wrapcycles*(celapsed/wrapcycles) + felapsed;
  if (fthen >= fnow)
    true_elapsed += wrapcycles;

  /* Prepare for our next invocation. */
  cthen = cnow;
  fthen = fnow;
  true_time += true_elapsed;
  return true_time;
}
#endif


/* Enable ncptl_log_shutdown() to be called from a non-stdarg function. */
static void invoke_ncptl_log_shutdown (const char *format, ...)
{
  va_list args;               /* Argument list */

  va_start (args, format);
  ncptl_log_shutdown (format, args);
  va_end (args);
}


/* Determine if ncptl_time() increments extremely slowly (e.g., in
 * 1-second increments).  Store the given number of data points in
 * timerdeltas[] and return 1 if the average delta is greater than 1
 * ms, otherwise 0.
 */
static int timer_increments_slowly (uint64_t numdeltas, uint64_t *timerdeltas)
{
  const uint64_t maxtrialcalls = UINT64_C(10000000000);   /* Give up if the timer doesn't increment after this many iterations. */
  uint64_t meandelta = UINT64_C(0);                       /* Average timer increment */
  uint64_t i, j;

  /* Keep probing until we get numdeltas valid readings. */
  for (i=0; i<numdeltas; i++) {
    uint64_t starttime, stoptime=UINT64_C(0);        /* Clock readings */

    starttime = ncptl_time();
    for (j=0; j<maxtrialcalls && (stoptime=ncptl_time()) == starttime; j++)
      ;
    if (j >= maxtrialcalls)
      /* We got the same time every reading -- the clock must be
       * seriously broken. */
      ncptl_fatal ("The timer function returns a constant value of %" PRIu64 " and therefore completely unusable", starttime);
    timerdeltas[i] = stoptime - starttime;
    meandelta += timerdeltas[i];
  }
  meandelta /= numdeltas;
  return meandelta > UINT64_C(1000);
}


/* Calculate the mean delay in calling ncptl_time(). */
static void calculate_mean_time_delay (void)
{
  const uint64_t mintrialcalls = 100000;  /* Min. # of measurements to take */
  uint64_t trialcalls;                    /* # of calls to ncptl_time() in each trial */
  const uint64_t mindatapoints = 1000;    /* Min. # of nonzero readings we require */
  uint64_t *timerdeltas;                  /* List of all non-zero deltas */
  uint64_t numdeltas = 0;                 /* # of entries in the above */

  timerdeltas = (uint64_t *) ncptl_malloc (mintrialcalls * sizeof(uint64_t), sizeof(uint64_t));
  (void) ncptl_time();                    /* fabricate_64_bit_cycle_counter() needs a warmup call. */
  for (trialcalls=mintrialcalls; numdeltas<mindatapoints; trialcalls*=10) {
    uint64_t starttime, stoptime;        /* Clock readings */
    uint64_t i;

    /* Take trialcalls readings and hope for mindatapoints nonzero deltas. */
    numdeltas = 0;
    sleep (0);
    for (i=0; i<trialcalls; i++) {
      starttime = ncptl_time();
      stoptime = ncptl_time();
      ncptl_time_overhead += stoptime - starttime;
      if (stoptime!=starttime && numdeltas<mintrialcalls)
        timerdeltas[numdeltas++] = stoptime - starttime;
    }
    ncptl_time_overhead /= trialcalls;

    /* Finish up if we received a sufficient number of nonzero deltas
     * or if we can determine that we're unlikely ever to receive a
     * sufficient number. */
    if (numdeltas >= mindatapoints
        || (numdeltas < 5 && timer_increments_slowly(numdeltas=5, timerdeltas))) {
      double meandelta = 0.0;
      double stddevdelta = 0.0;

      /* Calculate the mean and standard deviation. */
      for (i=0; i<numdeltas; i++)
        meandelta += (double) timerdeltas[i];
      meandelta /= (double) numdeltas;
      for (i=0; i<numdeltas; i++) {
        double num = timerdeltas[i] - meandelta;
        stddevdelta += num * num;
      }
      stddevdelta = sqrt (stddevdelta / (numdeltas-1));
      ncptl_time_delta_mean = meandelta;
      ncptl_time_delta_stddev = stddevdelta;
      break;
    }
  }
  if (cycle_counter_delay == -1)
    cycle_counter_delay = ncptl_time_overhead < 1;
  ncptl_free (timerdeltas);
}


/* Calculate the mean delay in sleeping with ncptl_udelay(). */
static void calculate_mean_sleep_delay (void)
{
#ifdef HAVE_NANOSLEEP
  uint64_t *timerdeltas;         /* List of all timing measurements */
  const int numdeltas = 25;      /* # of entries in the above */
  uint64_t starttime, stoptime;  /* Clock readings */
  int i;

  /* Take a few delay measurements. */
  timerdeltas = (uint64_t *) ncptl_malloc (numdeltas * sizeof(uint64_t), sizeof(uint64_t));
  for (i=0; i<numdeltas; i++) {
    starttime = ncptl_time();
    ncptl_udelay (1, 1);
    stoptime = ncptl_time();
    timerdeltas[i] = stoptime - starttime;
  }

  /* Calculate the mean and standard deviation. */
  for (i=0; i<numdeltas; i++)
    ncptl_sleep_mean += (double) timerdeltas[i];
  ncptl_sleep_mean /= (double) numdeltas;
  for (i=0; i<numdeltas; i++) {
    double num = timerdeltas[i] - ncptl_sleep_mean;
    ncptl_sleep_stddev += num * num;
  }
  ncptl_sleep_stddev = sqrt (ncptl_sleep_stddev / (numdeltas-1));
  ncptl_free (timerdeltas);
#endif
}


/* Calculate the quality of the user/system time read from
 * ncptl_process_time(). */
static void calculate_process_time_quality (void)
{
#ifdef HAVE_GETRUSAGE
  const int datapoints = 100;  /* # of nonzero readings we require */
  uint64_t *timerdeltas;       /* List of nonzero readings */
  double meandelta = 0.0;      /* Mean nonzero delta */
  double stddevdelta = 0.0;    /* Standard deviation delta */
  int i;

  /* Take a number of back-to-back measurements and record the nonzeroes. */
  timerdeltas =
    (uint64_t *) ncptl_malloc (datapoints * sizeof(uint64_t),
                               sizeof(uint64_t));
  for (i=0; i<datapoints; i++) {
    uint64_t initial = ncptl_process_time(0) + ncptl_process_time(1);
    uint64_t final;
    do
      final = ncptl_process_time(0) + ncptl_process_time(1);
    while (initial == final);
    timerdeltas[i] = final - initial;
    meandelta += (double) timerdeltas[i];
  }

  /* Calculate the mean and standard deviation of the timing deltas. */
  meandelta /= datapoints;
  for (i=0; i<datapoints; i++) {
    double num = timerdeltas[i] - meandelta;
    stddevdelta += num * num;
  }
  stddevdelta = sqrt (stddevdelta / (datapoints-1));
  ncptl_proc_time_delta_mean = meandelta;
  ncptl_proc_time_delta_stddev = stddevdelta;
  ncptl_free (timerdeltas);
#endif
}


/* Calibrate the number of spins per microsecond.  We spin for
 * TRIALSPINS iterations and divide TRIALSPINS into the elapsed number
 * of microseconds.  We take the minimum of NUMTRIALS trials because
 * we can always delay longer if necessary. */
static void calibrate_spins_per_usec (void)
{
  int numtrials = 2;              /* # of trials to perform */
  uint64_t trialspins = 10000;    /* # of spins in each trial (adaptive) */
  uint64_t trial_spinsperusec;    /* One trial's spins/usecs */
  uint64_t starttime, stoptime;   /* Clock readings */
  const uint64_t target_usecs = 500000;   /* Target time to spin for */
  uint64_t i;

  /* We might be able to make a better initial estimate. */
#ifdef HAVE_CYCLES_PER_USEC
  trialspins = ncptl_cycles_per_usec * target_usecs;
#endif

  /* Estimate the minimum number of spins per microsecond. */
  spinsperusec = ~0;
  while (numtrials--)
    while (1) {
      sleep (0);           /* Try to refresh our time quantum. */
      starttime = ncptl_time();
      for (i=0; i<trialspins; i++)
        dummyvar = 0;
      stoptime = ncptl_time();
      if (stoptime - starttime >= target_usecs) {
        trial_spinsperusec = trialspins / (stoptime-starttime);
        if (spinsperusec > trial_spinsperusec)
          spinsperusec = trial_spinsperusec;
        break;
      }
      trialspins = (stoptime==starttime ?
                    trialspins*2 :
                    (target_usecs*trialspins)/(stoptime-starttime));
    }
}


/* Return the current time in microseconds without using HPET.
 * NOTE: This function must be kept up-to-date with
 * log_write_prologue_timer(). */
inline uint64_t inlined_time_no_hpet (void)
{
#if NCPTL_TIMER_TYPE == 1
  /* Use gettimeofday() if we were forced to or if nothing else is
   * available. */
  struct timeval now;
  if (gettimeofday(&now, NULL) == -1)
    NCPTL_SYSTEM_ERROR ("Failed to read the current time");
  return (uint64_t)now.tv_sec*(uint64_t)1000000 + (uint64_t)now.tv_usec;
#elif NCPTL_TIMER_TYPE == 2
  return fabricate_64_bit_cycle_counter() / ncptl_cycles_per_usec;
#elif NCPTL_TIMER_TYPE == 3
  /* Read the hardware real-time cycle counter using inline assembly
   * language. */
  uint64_t now;
  READ_CYCLE_COUNTER(now);
  return now / ncptl_cycles_per_usec;
#elif NCPTL_TIMER_TYPE == 4
  /* Read Linux's real-time cycle counter. */
  return get_cycles() / ncptl_cycles_per_usec;
#elif NCPTL_TIMER_TYPE == 5
  /* Utilize PAPI's real-time cycle counter. */
  int64_t now = PAPI_get_real_usec();
  if (now < 0)
    ncptl_fatal ("Failed to read the current time (%s)",
                 PAPI_strerror(now));
  return (uint64_t) now;
#elif NCPTL_TIMER_TYPE == 6
  /* Utilize a high-resolution clock function. */
  struct timespec now;
  if (clock_gettime(CLOCKID, &now) == -1)
    NCPTL_SYSTEM_ERROR ("Failed to read the current time");
  return (uint64_t)now.tv_sec*(uint64_t)1000000 + (uint64_t)now.tv_nsec/(uint64_t)1000;
#elif NCPTL_TIMER_TYPE == 7
  /* Utilize a high-resolution time-in-seconds function. */
  return (uint64_t)(dclock()*1.0e6);
#elif NCPTL_TIMER_TYPE == 8
  /* Invoke the Win32 high-resolution timer function. */
  LARGE_INTEGER now;
  if (!QueryPerformanceCounter(&now))
    ncptl_fatal ("Failed to read the current time");
  return (1000000 * (uint64_t)now.QuadPart) / ncptl_cycles_per_sec;
#elif NCPTL_TIMER_TYPE == 9
  /* Use MPI's MPI_Wtime() function, which returns the time in seconds. */
  return (uint64_t) (MPI_Wtime()*1.0e6);
#else
# error Unable to implement a microsecond-timer function
#endif
}


/* Attempt to open and memory-map the High-Precision Event Timer
 * (HPET) device.  If anything goes wrong, set the HPET memory pointer
 * to a hardwired NULL value.  On success, override systeminfo's
 * timer_freq field. */
static void initialize_hpet (void)
{
#ifdef USE_HPET
  uint64_t gencap;      /* The HPET General Capabilities and ID register */
  uint64_t now1, now2;  /* Subsequent values of HPET */

  /* Open and memory-map the HPET device. */
  if ((hpet_fd=open(HPET_DEVICE, O_RDONLY)) == -1)
    return;
  if ((hpet_data=(volatile char *)mmap (NULL, 1024, PROT_READ, MAP_SHARED, hpet_fd, 0)) == (void *)-1)
    return;

  /* Read the timer's General Capabilities and ID register. */
  gencap = *(volatile uint64_t *)hpet_data;
  if ((gencap>>13&1) != 1)
    return;   /* Don't even bother with 32-bit HPET devices. */
  ncptl_hpet_period_fs = gencap >> 32;
  if (ncptl_hpet_period_fs == 0 || ncptl_hpet_period_fs > 0x05F5E100)
    return;   /* The specification dictates a non-zero period of <100ns. */

  /* At this point, if the main counter isn't stuck on some value then
   * we assume it works. */
  ncptl_hpet_timer = (volatile uint64_t *) (hpet_data + 0xF0);
  now1 = *ncptl_hpet_timer;
  ncptl_udelay (3, 0);
  now2 = *ncptl_hpet_timer;
  if (now1 == now2)
    return;
  ncptl_hpet_works = 1;
  systeminfo.timer_freq = 1e15 / ncptl_hpet_period_fs;
#endif
}


/* Cleanly shut down the High-Precision Event Timer (HPET) device. */
static void finalize_hpet (void)
{
#ifdef USE_HPET
  if (hpet_data != (void *)-1)
    munmap ((void *)hpet_data, 1024);
  if (hpet_fd != -1)
    close (hpet_fd);
#endif
}


/************************************
 * Exported variables and functions *
 ************************************/

/* OS memory-page size */
int ncptl_pagesize;


/* Flag enabling backends to initialize faster at the expense of
 * getting completely bogus timing measurements */
int ncptl_fast_init = 0;


/* Output an error message and abort the program. */
void ncptl_fatal (const char *format, ...)
{
  va_list args;                        /* Argument list */
  static int within_ncptl_fatal = 0;   /* Check for recursive invocations */

  va_start (args, format);
  if (within_ncptl_fatal++) {
    /* Some part of the shutdown process must have itself called
     * ncptl_fatal().  Kill ourself to avoid getting stuck in an
     * infinite loop. */
    if (within_ncptl_fatal > 2)
      fprintf (stderr, "Internal error: Recursive invocation of ncptl_fatal().  Please contact %s\n", PACKAGE_BUGREPORT);
    kill(getpid(), SIGKILL);
    _exit (EXIT_FAILURE);    /* In case kill() failed, exit without calling any exit handlers. */
  }
  else {
    va_list args_copy;   /* Copy of the argument list to pass to ncptl_log_shutdown() */

    /* First invocation */
    va_copy (args_copy, args);
    ncptl_log_shutdown (format, args_copy);
    va_end (args_copy);
    fprintf (stderr, "%s: ", ncptl_progname);
    vfprintf (stderr, format, args);
    fprintf (stderr, "\n");
  }
  va_end (args);
  exit (EXIT_FAILURE);
}


/* Initialize the coNCePTuaL run-time library. */
void ncptl_init (int version, char *argv0)
{
  /* Ensure the header and library version numbers match. */
  if (version != NCPTL_RUN_TIME_VERSION)
    ncptl_fatal ("Version mismatch: ncptl.h=%d; libncptl=%d",
                 version, NCPTL_RUN_TIME_VERSION);
  ncptl_progname = ncptl_strdup(argv0);

  /* Don't use fork() if instructed not to. */
#ifdef HAVE_WORKING_FORK
  if (getenv("NCPTL_NOFORK"))
    ncptl_fork_works = 0;
#endif

  /* If we're using PAPI, initialize it. */
#ifdef USE_PAPI
  {
    int retval = PAPI_library_init (PAPI_VER_CURRENT);

    if (retval < 0) {
      char *errmsg = PAPI_strerror (retval);

      if (errmsg)
        ncptl_fatal ("Failed to initialize PAPI (%s)", errmsg);
      else
        ncptl_fatal ("Failed to initialize PAPI (error code=%d)", retval);
    }
    else
      if (retval != PAPI_VER_CURRENT)
        ncptl_fatal ("PAPI library version mismatch: header=%d; library=%d",
                     PAPI_VER_CURRENT, retval);
  }
#endif

  /* Acquire as much information as possible about the underlying system. */
  ncptl_discern_system_information (&systeminfo);
  if (systeminfo.pagesize)
    ncptl_pagesize = systeminfo.pagesize;
  else
    ncptl_fatal ("Unable to determine the OS page size");
#ifdef HAVE_CYCLES_PER_USEC
  if (systeminfo.timer_freq) {
    ncptl_cycles_per_usec = (uint64_t) (systeminfo.timer_freq / 1.0e6);
#ifdef _WIN32
    ncptl_cycles_per_sec = (uint64_t) systeminfo.timer_freq;
#endif
  }
  else
    if (systeminfo.cpu_freq)
      ncptl_cycles_per_usec = (uint64_t) (systeminfo.cpu_freq / 1.0e6);
    else
      ncptl_fatal ("Unable to determine the timer frequency");
#endif

  /* Let the user override ncptl_fast_init at run time. */
  if (getenv("NCPTL_FAST_INIT"))
    ncptl_fast_init = atoi(getenv("NCPTL_FAST_INIT"));

  /* Let the user override ncptl_log_checkpoint_interval at run time. */
  ncptl_log_checkpoint_interval /= 1000000;
  if (!ncptl_envvar_to_uint64 ("NCPTL_CHECKPOINT", &ncptl_log_checkpoint_interval))
    ncptl_fatal ("\"%s\" is not a valid number of seconds for NCPTL_CHECKPOINT", getenv("NCPTL_CHECKPOINT"));
  ncptl_log_checkpoint_interval *= 1000000;

  /* Determine the quality of coNCePTuaL's various timers. */
  initialize_hpet();
  if (ncptl_fast_init)
    spinsperusec = 1;
  else {
    /* Calculate the mean delay in calling ncptl_time(). */
    calculate_mean_time_delay();

    /* Calculate the mean delay in sleeping with ncptl_udelay(). */
    calculate_mean_sleep_delay();

    /* Calculate the quality of the user/system time read from
     * ncptl_process_time(). */
    calculate_process_time_quality();

    /* Calibrate the number of spins per microsecond. */
    calibrate_spins_per_usec();
  }

  /* Initialize the list of signals not to trap.  By default, all
   * signals are trapped except for SIGALRM. */
  {
    int i;

    for (i=0; i<NUM_SIGNALS; i++)
      ncptl_no_trap_signal[i] = 0;
  }
  ncptl_no_trap_signal[SIGALRM] = 1;

  /* Seed the random-task-number generator.  Note that the value used
   * is not synchronized across tasks.  A correct backend should call
   * ncptl_seed_random_task() explicitly. */
  ncptl_seed_random_task (0, (ncptl_int)-1);
}


/* Cleanly shut down the coNCePTuaL run-time library. */
void ncptl_finalize (void)
{
  /* Close the log file(s). */
  invoke_ncptl_log_shutdown ("Backend failed to call ncptl_log_close()");
  reinstate_all_signal_handlers();

  /* Free memory just to be pedantic about it. */
  if (strcmp (ncptl_progname, "coNCePTuaL")) {   /* "coNCePTuaL" is assigned statically */
    ncptl_free (ncptl_progname);
    ncptl_progname = NULL;
  }
  if (ncptl_argv_copy) {
    int i;

    for (i=0; i<ncptl_argc_copy; i++)
      ncptl_free (ncptl_argv_copy[i]);
    ncptl_free (ncptl_argv_copy);
    ncptl_argv_copy = NULL;
  }

  /* Shut down the HPET device just to be pedantic about it, too. */
  finalize_hpet();
}


/* Fill a region of memory with known values.  If VALIDITY is +1, the
 * memory contents contain a verifiable sequence of integers; if -1,
 * the memory contents are polluted. */
void ncptl_fill_buffer (void *buffer, ncptl_int numbytes, int validity)
{
  if (numbytes > (ncptl_int)sizeof(uint32_t)) {
    uint32_t *bufptr = (uint32_t *)buffer;
    ncptl_int numwords = numbytes/sizeof(uint32_t) - 1;
    uint32_t seed;             /* Seed for the random-number generator */
    RNG_STATE verify_state;    /* Current state of the RNG */

    /* Initialize the random-number generator. */
    seed = (uint32_t) time (NULL);
    ncptl_init_genrand (&verify_state, (uint64_t) seed);

    /* Store the seed and the subsequent random words in the buffer. */
    *bufptr++ = seed;
    while (numwords--)
      *bufptr++ = (uint32_t) ncptl_genrand_int32 (&verify_state);
    if (validity == -1) {
      /* Bit-flip the buffer to cause maximal bit errors. */
      bufptr = 1 + (uint32_t *)buffer;
      numwords = numbytes/sizeof(uint32_t) - 1;
      while (numwords--) {
        *bufptr ^= ~(0UL);
        bufptr++;
      }
    }
  }
}


/* Verify the contents of memory filled by ncptl_fill_buffer().
 * Return the number of erroneous bits. */
ncptl_int ncptl_verify (void *buffer, ncptl_int numbytes)
{
  uint32_t *wordlist = (uint32_t *) buffer;  /* Word version of buffer */
  ncptl_int numwords = numbytes / sizeof(uint32_t);   /* # of words in the above */
  ncptl_int biterrors = 0;    /* Total number of bit errors */
  RNG_STATE verify_state;     /* Current state of the RNG */
  int i;

  /* We need at least two words in order to verify a buffer. */
  if (numwords < 2)
    return 0;

  /* Produce a sequence of random numbers from the original seed and
   * compare that sequence to the given one. */
  ncptl_init_genrand (&verify_state, (uint64_t)wordlist[0]);
  for (i=1; i<numwords; i++) {
    uint32_t expected_value = (uint32_t) ncptl_genrand_int32 (&verify_state);
    uint32_t mismatch_positions = wordlist[i] ^ expected_value;

    /* Mismatch -- tally the number of erroneous bits. */
    while (mismatch_positions) {
      biterrors++;
      mismatch_positions &= (mismatch_positions ^ -mismatch_positions);
    }
  }
  return biterrors;
}


/* Demand that the run-time library not trap a given signal. */
void ncptl_permit_signal (int signalnum)
{
  ncptl_no_trap_signal[signalnum] = 1;
}


/* Parse the command line. */
void ncptl_parse_command_line (int argc, char *argv[],
                               NCPTL_CMDLINE *orig_arglist, int numargs)
{
  NCPTL_CMDLINE *arglist;   /* Argument list with a few extra arguments added */
  NCPTL_CMDLINE extra_args[] = {    /* Arguments to add to orig_arglist[] */
    {NCPTL_TYPE_STRING, NULL, "comment", 'C',
     "Additional commentary to write to the log file, @FILE to import commentary from FILE, or !COMMAND to import commentary from COMMAND (may be specified repeatedly)", {0}},
    {NCPTL_TYPE_STRING, NULL, "no-trap", 'N', SIGNAL_CMDLINE_DESC, {0}}
  };
  const int num_extra_args = 2;    /* Number of extra arguments in the above */
  char *commentstr = NULL;         /* String containing a log-file comment */
  char *signal_string = "";        /* String containing a signal list */
  int i, j;

  /* If we haven't yet called ncptl_init(), store argv[0] now. */
  if (!ncptl_progname)
    ncptl_progname = ncptl_strdup(argv[0]);

  /* Add a few additional arguments to the list. */
  arglist = (NCPTL_CMDLINE *) ncptl_malloc ((numargs+num_extra_args)*sizeof(NCPTL_CMDLINE), CPU_MINIMUM_ALIGNMENT_BYTES);
  for (i=0; i<num_extra_args; i++)
    arglist[i] = extra_args[i];
  arglist[0].variable = (CMDLINE_VALUE *) &commentstr;
  arglist[0].defaultvalue.stringval = "";
  arglist[1].variable = (CMDLINE_VALUE *) &signal_string;
  arglist[1].defaultvalue.stringval = "";
  for (i=0; i<numargs; i++)
    arglist[i+num_extra_args] = orig_arglist[i];
  numargs += num_extra_args;

  /* Start by setting all variables to their default values. */
  for (i=0; i<numargs; i++)
    switch (arglist[i].type) {
      case NCPTL_TYPE_INT:
        *(ncptl_int *)(arglist[i].variable) = arglist[i].defaultvalue.intval;
        break;

      case NCPTL_TYPE_STRING:
        *(char **)(arglist[i].variable) = arglist[i].defaultvalue.stringval;
        break;

      default:
        NCPTL_FATAL_INTERNAL();
        break;
    }

  /* Sort the command-line arguments by short name.  Uppercase names
   * are output last. */
  for (i=0; i<numargs-1; i++) {
    int shortname_i = (int) arglist[i].shortname;
    if (isupper(shortname_i))
      shortname_i += 1000;
    for (j=i+1; j<numargs; j++) {
      int shortname_j = (int) arglist[j].shortname;
      if (isupper(shortname_j))
        shortname_j += 1000;
      if (shortname_i > shortname_j) {
        NCPTL_CMDLINE temparg = arglist[i];
        arglist[i] = arglist[j];
        arglist[j] = temparg;
        shortname_i = shortname_j;
      }
    }
  }

  /* Parse the command line. */
#if defined(USE_POPT)
  {
    /* ----- Variation 1: popt ----- */
    struct poptOption *popt_arglist;    /* popt version of arglist[] */
    struct poptOption extra_args[] = {  /* Extra args to tack onto popt_arglist */
      POPT_AUTOHELP
      POPT_TABLEEND
    };
    poptContext context;   /* popt context */
    char **stringvars;     /* string equivalent of each ncptl_int variable */
    int result;            /* Result of calling a popt function */

    /* Convert the argument list from NCPTL_CMDLINEs to poptOptions. */
    popt_arglist =
      (struct poptOption *) ncptl_malloc ((numargs+2)*sizeof(struct poptOption), 0);
    stringvars = (char **) ncptl_malloc (numargs*sizeof(char *), 0);
    for (i=0; i<numargs; i++) {
      popt_arglist[i].longName   = arglist[i].longname;
      popt_arglist[i].shortName  = arglist[i].shortname;
      popt_arglist[i].val        = 0;
      popt_arglist[i].arg        = (void *) arglist[i].variable;

      switch (arglist[i].type) {
        case NCPTL_TYPE_INT:
          popt_arglist[i].argInfo    = POPT_ARG_STRING;
          popt_arglist[i].argDescrip = "<number>";
          popt_arglist[i].descrip    =
            (char *) ncptl_malloc (strlen(arglist[i].description) + 50, 0);
          sprintf ((char *) popt_arglist[i].descrip,
                   "%s [default: %" PRId64 "]",
                   arglist[i].description, (int64_t) arglist[i].defaultvalue.intval);
          stringvars[i] = NULL;
          popt_arglist[i].arg = (void *) &stringvars[i];
          break;

        case NCPTL_TYPE_STRING:
          popt_arglist[i].argInfo    = POPT_ARG_STRING;
          popt_arglist[i].argDescrip = "<string>";
          popt_arglist[i].descrip    =
            (char *) ncptl_malloc (strlen(arglist[i].description) +
                                   strlen(arglist[i].defaultvalue.stringval) + 25,
                                   0);
          sprintf ((char *) popt_arglist[i].descrip, "%s [default: \"%s\"]",
                   arglist[i].description, arglist[i].defaultvalue.stringval);
          break;

        default:
          NCPTL_FATAL_INTERNAL();
          break;
      }
    }
    for (i=0; i<2; i++) {
      popt_arglist[numargs+i].longName   = extra_args[i].longName;
      popt_arglist[numargs+i].shortName  = extra_args[i].shortName;
      popt_arglist[numargs+i].argInfo    = extra_args[i].argInfo;
      popt_arglist[numargs+i].arg        = extra_args[i].arg;
      popt_arglist[numargs+i].val        = extra_args[i].val;
      popt_arglist[numargs+i].descrip    = extra_args[i].descrip;
      popt_arglist[numargs+i].argDescrip = extra_args[i].argDescrip;
    }

    /* Handle --comment/-C specially in the help string. */
    for (i=0; i<numargs; i++)
      if (popt_arglist[i].shortName == 'C') {
        strcpy ((char *)popt_arglist[i].descrip, arglist[i].description);
        popt_arglist[i].val = 'C';
      }

    /* Parse the command line with popt. */
    context = poptGetContext(NULL, argc, (const char **)argv, popt_arglist, 0);
    while ((result=poptGetNextOpt(context)) >= 0) {
      if (result == 'C')
        /* Special case for --comment/-C as these can be used multiple
         * times.  We store a copy of the comment string in a queue
         * for later use. */
        ncptl_log_add_comment (NULL, poptGetOptArg (context));
      else
        NCPTL_FATAL_INTERNAL();
    }
    if (result < -1)
      ncptl_fatal ("%s: %s",
                   poptBadOption(context, POPT_BADOPTION_NOALIAS),
                   poptStrerror(result));

    /* Copy the string results into the original ncptl_int variables. */
    for (i=0; i<numargs; i++)
      if (arglist[i].type == NCPTL_TYPE_INT) {
        if (stringvars[i])
          arglist[i].variable->intval = string_to_integer (stringvars[i]);
        else
          arglist[i].variable->intval = arglist[i].defaultvalue.intval;
      }

    /* Clean up. */
    poptFreeContext (context);
    for (i=0; i<numargs; i++)
      ncptl_free ((void *) popt_arglist[i].descrip);
    ncptl_free (popt_arglist);
    ncptl_free (stringvars);
  }
#elif defined(USE_GETOPT_LONG)
  {
    /* ----- Variation 2: getopt_long ----- */
    struct option *getopt_arglist;   /* Long options */
    char *getopt_short_arglist;      /* One-letter options */
    NCPTL_CMDLINE *short_arg_to_info[256]; /* Map from short option to argument info */
    int arg;                         /* Current one-letter option */
#ifndef HAVE_OPTOPT
    int optopt = '!';                /* optopt isn't always defined. */
#endif

    /* Convert the argument list from NCPTL_CMDLINEs to options. */
    getopt_arglist =
      (struct option *) ncptl_malloc ((numargs+2)*sizeof(struct option), 0);
    for (i=0; i<numargs; i++) {
      getopt_arglist[i].name    = arglist[i].longname;
      getopt_arglist[i].has_arg = required_argument;
      getopt_arglist[i].flag    = NULL;
      getopt_arglist[i].val     = arglist[i].shortname;
    }
    getopt_arglist[numargs].name    = "help";
    getopt_arglist[numargs].has_arg = no_argument;
    getopt_arglist[numargs].flag    = NULL;
    getopt_arglist[numargs].val     = '?';
    getopt_arglist[numargs+1].name    = NULL;
    getopt_arglist[numargs+1].has_arg = 0;
    getopt_arglist[numargs+1].flag    = NULL;
    getopt_arglist[numargs+1].val     = 0;

    /* Create a list of short options and a mapping from short option
     * to variable pointer. */
    getopt_short_arglist = (char *) ncptl_malloc ((numargs*2)+2, 0);
    for (i=0; i<numargs; i++) {
      getopt_short_arglist[i*2] = arglist[i].shortname;
      getopt_short_arglist[i*2+1] = ':';
      short_arg_to_info[(int)arglist[i].shortname] = &arglist[i];
    }
    getopt_short_arglist[numargs*2]   = '?';
    getopt_short_arglist[numargs*2+1] = '\0';

    /* Parse the command line with getopt_long. */
    optind = 1;
    while ((arg=getopt_long(argc, argv, getopt_short_arglist, getopt_arglist, NULL)) != -1)
      if (arg == '?') {
        if (optopt != '?')
          printf ("\n");
        printf ("Usage: %s [OPTION...]\n", argv[0]);
        for (i=0; i<numargs; i++)
          switch (arglist[i].type) {
            case NCPTL_TYPE_INT:
              printf ("  -%c, --%s=<number>\t%s [default: %" PRId64 "]\n",
                      arglist[i].shortname,
                      arglist[i].longname,
                      arglist[i].description,
                      (int64_t) arglist[i].defaultvalue.intval);
              break;

            case NCPTL_TYPE_STRING:
              printf ("  -%c, --%s=<string>\t%s",
                      arglist[i].shortname,
                      arglist[i].longname,
                      arglist[i].description);
              if (arglist[i].shortname != 'C')
                printf (" [default: \"%s\"]",
                        arglist[i].defaultvalue.stringval);
              printf ("\n");
              break;

            default:
              NCPTL_FATAL_INTERNAL();
              break;
          }
        printf ("\n");
        printf ("Help options\n");
        printf ("  -?, --help         \tShow this help message\n");
        exit (EXIT_FAILURE);
      }
      else
        switch (short_arg_to_info[arg]->type) {
          case NCPTL_TYPE_INT:
            *(ncptl_int *)short_arg_to_info[arg]->variable = string_to_integer (optarg);
            break;

          case NCPTL_TYPE_STRING:
            if (arg == 'C')
              /* Special case for --comment/-C as these can be used
               * multiple times.  We store a copy of the comment
               * string in a queue for later use. */
              ncptl_log_add_comment (NULL, optarg);
            else
              *(char **)short_arg_to_info[arg]->variable = optarg;
            break;

          default:
            NCPTL_FATAL_INTERNAL();
            break;
        }

    /* Clean up. */
    ncptl_free (getopt_short_arglist);
    ncptl_free (getopt_arglist);
  }
#else
  {
    /* ----- Variation 3: getopt ----- */
    char *getopt_short_arglist;      /* One-letter options */
    NCPTL_CMDLINE *short_arg_to_info[256]; /* Map from short option to argument info */
    int arg;                         /* Current one-letter option */
#ifndef HAVE_OPTOPT
    int optopt = '!';                /* optopt isn't always defined. */
#endif

    /* Create a list of short options and a mapping from short option
     * to variable pointer. */
    getopt_short_arglist = (char *) ncptl_malloc ((numargs*2)+2, 0);
    for (i=0; i<numargs; i++) {
      getopt_short_arglist[i*2] = arglist[i].shortname;
      getopt_short_arglist[i*2+1] = ':';
      short_arg_to_info[(int)arglist[i].shortname] = &arglist[i];
    }
    getopt_short_arglist[numargs*2]   = '?';
    getopt_short_arglist[numargs*2+1] = '\0';

    /* Parse the command line with getopt. */
    optind = 1;
    while ((arg=getopt(argc, argv, getopt_short_arglist)) != -1)
      if (arg == '?') {
        if (optopt != '?')
          printf ("\n");
        printf ("Usage: %s [OPTION...]\n", argv[0]);
        for (i=0; i<numargs; i++)
          switch (arglist[i].type) {
            case NCPTL_TYPE_INT:
              printf ("  -%c <number>\t%s [default: %" PRId64 "]\n",
                      arglist[i].shortname,
                      arglist[i].description,
                      (int64_t) arglist[i].defaultvalue.intval);
              break;

            case NCPTL_TYPE_STRING:
              printf ("  -%c <string>\t%s",
                      arglist[i].shortname,
                      arglist[i].description);
              if (arglist[i].shortname != 'C')
                printf (" [default: \"%s\"]",
                        arglist[i].defaultvalue.stringval);
              printf ("\n");
              break;

            default:
              NCPTL_FATAL_INTERNAL();
              break;
          }
        printf ("\n");
        printf ("Help options\n");
        printf ("  -?         \tShow this help message\n");
        exit (EXIT_FAILURE);
      }
      else
        switch (short_arg_to_info[arg]->type) {
          case NCPTL_TYPE_INT:
            *(ncptl_int *)short_arg_to_info[arg]->variable = string_to_integer (optarg);
            break;

          case NCPTL_TYPE_STRING:
            if (arg == 'C')
              /* Special case for --comment/-C as these can be used
               * multiple times.  We store a copy of the comment
               * string in a queue for later use. */
              ncptl_log_add_comment (NULL, optarg);
            else
              *(char **)short_arg_to_info[arg]->variable = optarg;
            break;

          default:
            NCPTL_FATAL_INTERNAL();
            break;
        }

    /* Clean up. */
    ncptl_free (getopt_short_arglist);
  }
#endif

  /* Conclude by setting all default values to actual values. */
  for (i=0; i<numargs; i++)
    switch (arglist[i].type) {
      case NCPTL_TYPE_INT:
        arglist[i].defaultvalue.intval = *(ncptl_int *)(arglist[i].variable);
        break;

      case NCPTL_TYPE_STRING:
        arglist[i].defaultvalue.stringval = *(char **)(arglist[i].variable);
        break;

      default:
        NCPTL_FATAL_INTERNAL();
        break;
    }

  /* Store a copy of argc and argv[].  We have to make a deep copy
   * because argc and argv[] may in fact be temporaries passed to us
   * from the pyncptl Python interface. */
  ncptl_argc_copy = argc;
  ncptl_argv_copy = (char **) ncptl_malloc (argc*sizeof(char *), 0);
  for (i=0; i<argc; i++)
    ncptl_argv_copy[i] = ncptl_strdup (argv[i]);

  /* Now that we have a list of signals to ignore, set up a signal
   * handler for each possible signal, except those the user doesn't
   * want us to trap.  We always trap SIGALRM, though, because we
   * actually use that internally. */
  parse_signal_list (signal_string);
  for (i=1; i<NUM_SIGNALS; i++) {
    /* Store the current value of each signal handler. */
    original_handler[i] = SIG_DFL;   /* Deal with the following lines failing. */
    ncptl_install_signal_handler (i, SIG_DFL, &original_handler[i], 0);
    ncptl_install_signal_handler (i, original_handler[i], NULL, 0);

    /* Assign SIGALRM. */
    switch (i) {
#ifdef HAVE_SETITIMER
      case SIGALRM:
        /* Needed to implement coNCePTuaL's FOR <time> construct */
        ncptl_install_signal_handler (i, set_flag_on_interrupt, &original_handler[i], 1);
        break;
#endif

      default:
        /* All signals that are not trapped kill the process. */
        if (!ncptl_no_trap_signal[i])
          ncptl_install_signal_handler (i, abort_on_signal, &original_handler[i], 0);
    }
  }

  /* Clean up some more. */
  ncptl_free (arglist);
}


/* Return the current time in microseconds. */
uint64_t ncptl_time (void)
{
#ifdef USE_HPET
  /* Give top priority to HPET because it's the most robust timer we know of. */
  if (ncptl_hpet_works)
    return (*ncptl_hpet_timer*ncptl_hpet_period_fs) / UINT64_C(1000000000);
  else
    return inlined_time_no_hpet();
#else
  return inlined_time_no_hpet();
#endif
}


/* Asynchronously set a variable to 1 after a given number of microseconds. */
void ncptl_set_flag_after_usecs(volatile int *flag, uint64_t delay)
{
#ifdef HAVE_SETITIMER
  struct itimerval interrupt_time;

  /* Request a one-shot interrupt. */
  interrupt_time.it_interval.tv_sec = 0;
  interrupt_time.it_interval.tv_usec = 0;
  interrupt_time.it_value.tv_sec = (long) (delay / 1000000);
  interrupt_time.it_value.tv_usec = (long) (delay % 1000000);
  flag_to_set = flag;
  if (setitimer(ITIMER_REAL, &interrupt_time, NULL) == -1)
    NCPTL_SYSTEM_ERROR ("failed to set the interval timer");
#else
  ncptl_fatal ("This program can't run without a setitimer() function");
#endif
}


/* Spin (0) or sleep (1) for a given number of microseconds.
 * NOTE: This function must be kept up-to-date with
 * log_write_prologue_timer() and ncptl_time().
 */
void ncptl_udelay (int64_t delay, int spin0block1)
{
  if (spin0block1 == 0) {
    /* Spin. */
    uint64_t usecs_remaining;   /* # of microseconds we underspun */
    uint64_t targettime;        /* Time when we're finished */

    /* Spin for a number of iterations proportional to DELAY.  If we
     * underspin (due to poor calibration) we just try again. */
    if (delay < 2*(int64_t)ncptl_time_overhead)
      return;
    usecs_remaining = delay - ncptl_time_overhead;
    targettime = ncptl_time() + usecs_remaining - ncptl_time_overhead;

    /* Poll if we have a cycle counter.  Spin if we don't. */
    if (cycle_counter_delay)
      /* We're reading a CPU cycle counter.  Hence, calling the timer
       * function repeatedly gives us maximum accuracy without having
       * to invoke the operating system (which may have adverse
       * performance effects). */
      while (ncptl_time() < targettime)  /* Pray that the cycle counter doesn't both overflow and skip targettime. */
        ;
    else
      /* We're probably not reading a CPU cycle counter.  Hence, it's
       * best to avoid calling ncptl_time() more than necessary
       * because we don't want to pound on a potentially shared OS.
       * We therefore determine a number of spins, spin that many
       * times, recalculate the spin count, and repeat until we reach
       * our target time. */
      while (usecs_remaining) {
        const int spinfactor = 2;   /* Try to get more precision by forcing SPINFACTOR passes through the loop. */
        uint64_t numspins = usecs_remaining * spinsperusec / spinfactor;
        uint64_t now;
        uint64_t i;

        for (i=0; i<numspins; i++)
          dummyvar = 0;
        now = ncptl_time() + ncptl_time_overhead;
        usecs_remaining = now<targettime ? targettime-now : 0;
      }
  }
  else
#ifdef HAVE_NANOSLEEP
    {
      /* Block -- possibly up to a quantum longer than requested. */
      struct timespec blocktime;
      struct timespec remainingtime;

      blocktime.tv_sec = (time_t) (delay / 1000000);
      blocktime.tv_nsec = (long) (1000 * (delay % 1000000));
      while (nanosleep(&blocktime, &remainingtime) == -1)
        if (errno == EINTR)
          blocktime = remainingtime;
        else
          NCPTL_SYSTEM_ERROR ("failed to pause execution with nanosleep()");
    }
#else
  ncptl_fatal ("Sleeping is not possible without a nanosleep() function");
#endif
}


/* Initialize the random-number generator needed by
 * ncptl_random_task().  If SEED is zero, we choose an arbitrary local
 * (i.e., not synchronized across tasks) seed.
 * ncptl_seed_random_task() returns the seed that was used. */
int ncptl_seed_random_task (int seed, ncptl_int physrank)
{
  ncptl_rng_seed = seed;
  if (!ncptl_rng_seed) {
    int devurandom;

    /* We get to choose our own seed.  If we have /dev/urandom we use that. */
    if ((devurandom=open("/dev/urandom", O_RDONLY)) != -1 &&
        read (devurandom, (void *)&ncptl_rng_seed, sizeof(int)) == sizeof(int))
      /* We successfully got some random data from /dev/urandom. */
      close (devurandom);
    else {
      /* We couldn't read /dev/urandom; just slap a few arbitrary
       * numbers together and use that. */
      const int bigprime = 1073742811;
      char *c;

      ncptl_rng_seed = (int) ncptl_time_of_day();
      ncptl_rng_seed = ncptl_rng_seed*bigprime + getpid();
      ncptl_rng_seed = ncptl_rng_seed*bigprime + getppid();
      for (c=ncptl_progname; *c; c++)
        ncptl_rng_seed = ncptl_rng_seed*bigprime + *c;
    }
  }
  ncptl_init_genrand (&random_task_state, (uint64_t) ncptl_rng_seed);
  ncptl_unsync_rand_state_seeded = 0;    /* Unsynchronized RNG must re-seed, too. */
  ncptl_self_proc = physrank;            /* Store our physical ID */
  return ncptl_rng_seed;
}


/* Return a randomly selected task number from LOWERBOUND to
 * UPPERBOUND (both inclusive).  If EXCLUDED is nonnegative then that
 * task number will never be selected.  If no tasks can be selected,
 * -1 is returned. */
ncptl_int ncptl_random_task (ncptl_int lowerbound, ncptl_int upperbound,
                             ncptl_int excluded)
{
  if (lowerbound > upperbound)
    return -1;
  if (excluded<lowerbound || excluded>upperbound)
    /* Handle both the case when EXCLUDED is -1 and when it's out of bounds. */
    return lowerbound + ncptl_genrand_int63(&random_task_state) % (upperbound-lowerbound+1);
  else
    /* Some element that's within range must be excluded. */
    if (upperbound == lowerbound)
      /* The only number in range is to be excluded. */
      return -1;
    else {
      /* The range contains multiple numbers and one of these is to be
       * excluded.  The approach we take is first to map the range to
       * [0, SHIFTEDUPPER] (and excluded SHIFTEDEXCL) to simplify the
       * arithmetic; then, we randomly select a non-excluded element;
       * and finally, we map it back to [LOWERBOUND, UPPERBOUND]. */
      ncptl_int shiftedupper = upperbound - lowerbound;
      ncptl_int shiftedexcl = excluded - lowerbound;
      ncptl_int randtask =
        (ncptl_int) (ncptl_genrand_int63(&random_task_state) % shiftedupper);
      randtask = (shiftedexcl+1+randtask) % (shiftedupper+1);
      return lowerbound + randtask;
    }
}


/* Allocate a data structure to map between (physical) processor IDs
 * and (virtual) task IDs.  There is not currently a function to
 * deallocate the result. */
NCPTL_VIRT_PHYS_MAP *ncptl_allocate_task_map (ncptl_int numtasks)
{
  NCPTL_VIRT_PHYS_MAP *procmap = (NCPTL_VIRT_PHYS_MAP *) ncptl_malloc (sizeof(NCPTL_VIRT_PHYS_MAP), 0);
  ncptl_int i;

  procmap->numtasks = numtasks;
  procmap->virt2phys = (ncptl_int *) ncptl_malloc (numtasks*sizeof(ncptl_int), 0);
  procmap->phys2virt = (ncptl_int *)ncptl_malloc (numtasks*sizeof(ncptl_int), 0);
  for (i=0; i<numtasks; i++) {
    procmap->virt2phys[i] = i;
    procmap->phys2virt[i] = i;
  }
  procmap->used = 0;
  return procmap;
}


/* Store a pointer to a task map, and mark the task map as "live". */
NCPTL_VIRT_PHYS_MAP *ncptl_point_to_task_map (NCPTL_VIRT_PHYS_MAP *oldmap)
{
  oldmap->used = 1;
  return oldmap;
}


/* Replicate an existing task map if it is "live" (i.e., something
 * points to it) or return the input parameter if not.  There is not
 * currently a function to deallocate the result. */
NCPTL_VIRT_PHYS_MAP *ncptl_conditionally_copy_task_map (NCPTL_VIRT_PHYS_MAP *oldmap)
{
  NCPTL_VIRT_PHYS_MAP *newmap;    /* Map to return */
  ncptl_int numtasks;             /* Number of tasks in the map */
  ncptl_int i;

  if (!oldmap->used)
    return oldmap;
  numtasks = oldmap->numtasks;
  newmap = (NCPTL_VIRT_PHYS_MAP *) ncptl_malloc (sizeof(NCPTL_VIRT_PHYS_MAP), 0);
  newmap->numtasks = numtasks;
  newmap->virt2phys = (ncptl_int *) ncptl_malloc (numtasks*sizeof(ncptl_int), 0);
  newmap->phys2virt = (ncptl_int *)ncptl_malloc (numtasks*sizeof(ncptl_int), 0);
  for (i=0; i<newmap->numtasks; i++) {
    newmap->virt2phys[i] = oldmap->virt2phys[i];
    newmap->phys2virt[i] = oldmap->phys2virt[i];
  }
  newmap->used = 0;
  return newmap;
}


/* Map a (virtual) task ID to a (physical) processor ID. */
ncptl_int ncptl_virtual_to_physical (NCPTL_VIRT_PHYS_MAP *procmap,
                                     ncptl_int virtID)
{
  if (virtID<0 || virtID>=procmap->numtasks)
    ncptl_fatal ("Cannot map task ID %" NICS " to a processor ID", virtID);
  return procmap->virt2phys[virtID];
}


/* Map a (physical) processor ID to a (virtual) task ID. */
ncptl_int ncptl_physical_to_virtual (NCPTL_VIRT_PHYS_MAP *procmap,
                                     ncptl_int physID)
{
  if (physID<0 || physID>=procmap->numtasks)
    ncptl_fatal ("Cannot map processor ID %" NICS " to a task ID", physID);
  return procmap->phys2virt[physID];
}


/* Assign a (physical) processor ID to a (virtual) task ID given a
 * virtual-to-physical mapping table and its length.  Return a new
 * task ID for our processor given its processor number. */
ncptl_int ncptl_assign_processor (ncptl_int virtID, ncptl_int physID,
                                  NCPTL_VIRT_PHYS_MAP *procmap,
                                  ncptl_int physrank)
{
  ncptl_int physID_prev;                /* Task ID virtID's current processor */
  ncptl_int virtID_prev;                /* Task ID that currently has processor physID */
  ncptl_int virtrank;                   /* New task ID for physrank */

  /* Ensure we're not out of bounds. */
  if (physID<0 || physID>=procmap->numtasks)
    ncptl_fatal ("Cannot assign processor %" NICS " to task %" NICS
                 " (processor ID is out of bounds)",
                 physID, virtID);
  if (virtID<0 || virtID>=procmap->numtasks)
    ncptl_fatal ("Cannot assign processor %" NICS " to task %" NICS
                 " (task ID is out of bounds)",
                 physID, virtID);

  /* Assign processor physID to task ID virtID while maintaining a bijection
   * between task IDs and processors. */
  physID_prev = procmap->virt2phys[virtID];
  virtID_prev = procmap->phys2virt[physID];
  procmap->virt2phys[virtID] = physID;
  procmap->phys2virt[physID] = virtID;
  procmap->virt2phys[virtID_prev] = physID_prev;
  procmap->phys2virt[physID_prev] = virtID_prev;

  /* Return the new virtual rank corresponding to physical rank physrank. */
  virtrank = procmap->phys2virt[physrank];
  return virtrank;
}
