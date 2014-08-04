/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * functions for manipulating log files
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
#include "compiler_version.h"


/**********
 * Macros *
 **********/

/* ASCI Red lacks a realpath() function and a vsnprintf() function. */
#ifndef HAVE_REALPATH
# define realpath(ORIG, RESOLVED) NULL
#endif
#ifndef HAVE_VSNPRINTF
# define vsnprintf(S, N, FMT, AP) vsprintf (S, FMT, AP)
#endif

/* When building under Microsoft Windows with MinGW, "group" and
 * "other" file-permission symbols are not defined.  Define them here
 * as synonyms for "user".  When building under Microsoft Windows with
 * the Microsoft C compiler, even S_IXUSR is undefined so we define
 * that, too, if necessary. */
#ifndef S_IXUSR
# define S_IXUSR 00100
#endif
#ifndef S_IXGRP
# define S_IXGRP S_IXUSR
#endif
#ifndef S_IXOTH
# define S_IXOTH S_IXUSR
#endif

/* MinGW (under Microsoft Windows) doesn't define userID-related
 * functions. */
#ifndef HAVE_GETUID
# define getuid() -1
#endif
#ifndef HAVE_GETEUID
# define geteuid() -1
# define getegid() -1
#endif

/* The Microsoft C compiler apparently lacks a definition of ssize_t. */
#ifndef HAVE_SSIZE_T
typedef long ssize_t;
#endif

/* Define strings to specify that we're writing to standard output or
 * to an internal string. */
#define STANDARD_OUTPUT_NAME "<standard output>"
#define INTERNAL_STRING_NAME "<internal string>"

/* Define an arbitrary byte increment for resizing the log-contents string. */
#define LOG_CONTENTS_INCREMENT 8192


/*********************
 * Type declarations *
 *********************/

/* Define a type that describes a single column of a log file. */
typedef struct {
  char *description;        /* Textual description of a column (NULL=invalid column) */
  LOG_AGGREGATE aggregate;  /* Aggregate used to summarize the column */
  double aggregate_param;   /* Additional information specific to certain aggregates */
  NCPTL_QUEUE *rawdata;     /* Non-aggregated data values */
  NCPTL_QUEUE *finaldata;   /* Aggregated data values */
} LOG_COLUMN;

/* Define a type representing a {value, tally} pair in a histogram. */
typedef struct {
  double value;
  uint64_t tally;
} VALUE_TALLY;

/* Define a type for extra key:value pairs to write to the log file as
 * comments. */
typedef struct {
  char *key;          /* Statically allocated string; NULL means "User comment N" */
  char *value;        /* Dynamically allocated string */
} LOG_COMMENT;

/* Define a type that encapsulates much of the state needed to
 * represent a log file's contents.  This makes it possible for one
 * process to maintain multiple log files concurrently (e.g., in a
 * multithreaded backend). */
typedef struct ncptl_log_file_state {
  /* Handle to the log file or, alternatively, a string containing the
   * text that would have been written to the log file.  If logfile is
   * NULL, then output is written to log_contents.  However, both
   * logfile and log_contents can be non-NULL.  This occurs if the
   * program invokes ncptl_log_get_contents() when output is written
   * to logfile. */
  FILE *logfile;
  char *log_contents;
  ncptl_int log_contents_used;          /* # of valid bytes in log_contents */
  ncptl_int log_contents_allocated;     /* # of bytes allocated for log_contents */

  /* Name of thie log file */
  char *filename;

  /* Process rank (PROCESSOR in the coNCePTuaL language) associated
   * with this log file */
  ncptl_int process_rank;

  /* Store a database of key:value pairs written as comments to the
   * log-file prologue. */
  NCPTL_SET *log_database;

  /* Current contents of the log file */
  LOG_COLUMN *logfiledata;    /* Current contents */
  int log_columns_alloced;    /* # of columns allocated */
  int log_columns_used;       /* # of valid columns */
  int log_need_newline;       /* 1=output a line break before the table */

  /* Seconds after the epoch at which we created the log file */
  time_t log_creation_time;

#ifdef HAVE_GETRUSAGE
  /* Process time used at the point at which we created the log file */
  uint64_t log_creation_process_time_user;
  uint64_t log_creation_process_time_sys;

  /* Major and minor page faults observed at the point at which we
   * created the log file */
  uint64_t major_faults;      /* Major page faults */
  uint64_t minor_faults;      /* Minor page faults */
#endif

#ifdef USE_HPET
  /* Values of ncptl_time() and ncptl_time_no_hpet() when we created
   * the log file */
  uint64_t log_creation_time_hpet;      /* Value from ncptl_time() */
  uint64_t log_creation_time_no_hpet;   /* Value from ncptl_time_no_hpet() */
#endif

  /* Number of interrupts seen since boot time at the point at which
   * we created the log file */
  uint64_t log_creation_interrupt_count;

  /* Current contents of the {value, tally} histogram */
  VALUE_TALLY *histnodes;  /* All of the nodes in the histogram tree */
  void *histtree;       /* Histogram stored as a binary tree */
  double *histvalues;   /* List of unique values in the histogram */
  double *histtallies;  /* List of tallies associated with values */
  int histnumpairs;     /* # of {value, tally} pairs in the histogram */

  /* Random variable used by find_k_median() (initialized by
   * ncptl_log_open()) */
  RNG_STATE random_state;

  /* Maximum delay time in microseconds before file metadata
   * operations.  The actual delay time is a uniform-random number no
   * greater than this value. */
  uint64_t log_delay;

  /* Data needed for checkpointing log files */
  uint64_t last_checkpoint;  /* Time of last checkpoint */
  int suppress_emptying;     /* 1=don't empty the log after committing data */
} NCPTL_LOG_FILE_STATE;


/************************************
 * Imported variables and functions *
 ************************************/

extern char *ncptl_progname;
extern int ncptl_argc_copy;
extern char **ncptl_argv_copy;
extern uint64_t ncptl_time_overhead;
extern double ncptl_time_delta_mean;
extern double ncptl_time_delta_stddev;
extern double ncptl_sleep_mean;
extern double ncptl_sleep_stddev;
extern double ncptl_proc_time_delta_mean;
extern double ncptl_proc_time_delta_stddev;
extern int ncptl_no_trap_signal[NUM_SIGNALS];
extern int ncptl_fork_works;
extern uint64_t ncptl_cycles_per_usec;
extern SYSTEM_INFORMATION systeminfo;
#ifdef HAVE_BGPPERSONALITY
extern _BGP_Personality_t ncptl_bgp_personality;
#endif
#ifdef HAVE_BGLPERSONALITY
extern BGLPersonality ncptl_bgl_personality;
#endif
extern uint64_t ncptl_log_checkpoint_interval;
extern int ncptl_hpet_works;

extern void ncptl_init_genrand(RNG_STATE *, uint64_t);
extern int64_t ncptl_genrand_int63(RNG_STATE *);
extern uint64_t ncptl_genrand_int64(RNG_STATE *);
extern void ncptl_install_signal_handler (int, SIGHANDLER, SIGHANDLER *, int);
#ifdef HAVE_GETRUSAGE
extern uint64_t ncptl_process_time (int);
extern void ncptl_page_fault_count (uint64_t *, uint64_t *);
#endif
extern uint64_t ncptl_interrupt_count (void);
extern unsigned long ncptl_time_of_day (void);
extern void ncptl_log_commit_data (NCPTL_LOG_FILE_STATE *);
extern int ncptl_envvar_to_uint64 (const char *, uint64_t *);
extern ncptl_int ncptl_get_peak_memory_usage (void);
extern uint64_t ncptl_time_no_hpet (void);


/************************************
 * Internal variables and functions *
 ************************************/

/* Dummy variable to prevent whiny C compilers from complaining about
 * unused function parameters */
static volatile union {
  int i;
  void *vp;
} dummyvar;

/* Queue of all {value, tally} pairs encountered in a histogram. */
static NCPTL_QUEUE *histogram_data;

/* The number of digits per floating-point value to write to the
 * log file */
static const int log_data_digits = 10;

/* Queue of extra log-file comments as specified on the command line
 * or by a backend.  These are entered into all log files. */
static NCPTL_QUEUE *extra_log_comments = NULL;

/* Queue of all log-file state we ever allocated */
static NCPTL_QUEUE *all_log_file_state = NULL;

/* Separator string for log-file sections */
static const char *log_section_separator = "###########################################################################\n";


/* Return the kth median of a list of values in linear time
 * (probabilistically).  WARNING: This operation destructively
 * reorders the elements in DATA. */
static double find_k_median (NCPTL_LOG_FILE_STATE *logstate, double *data,
                             ncptl_int k, ncptl_int firstelt,
                             ncptl_int lastelt)
{
  ncptl_int pivotelt;   /* Row by which to partition the column */
  double pivotvalue;    /* Contents of LOGFILEDATA's row PIVOTROW, column COLUMN */
  ncptl_int topsetsize; /* # of rows in the upper (smaller valued) partition */
  ncptl_int i, j;

  /* If we have only one element, we have nothing to do. */
  if (firstelt == lastelt)
    return data[firstelt];

  /* Choose a pivot at random and swap it to the first element. */
  pivotelt = ncptl_genrand_int63 (&logstate->random_state) % (lastelt-firstelt+1) + firstelt;
  pivotvalue = data[pivotelt];
  data[pivotelt] = data[firstelt];
  data[firstelt] = pivotvalue;

  /* Partition the data into elements less than or equal to PIVOTVALUE
   * and elements greater than or equal to PIVOTVALUE. */
  i = firstelt - 1;
  j = lastelt + 1;
  do {
    /* Find the topmost element that's on the wrong side of the pivot. */
    do {
      j--;
    }
    while (data[j] > pivotvalue);

    /* Find the bottommost element that's on the wrong side of the pivot. */
    do {
      i++;
    }
    while (data[i] < pivotvalue);

    /* Swap the two misordered values. */
    if (i < j) {
      double swapval = data[i];
      data[i] = data[j];
      data[j] = swapval;
    }
  }
  while (i < j);

  /* Search exactly one of the two partitions. */
  topsetsize = j - firstelt + 1;
  if (k <= topsetsize)
    return find_k_median (logstate, data, k, firstelt, j);
  else
    return find_k_median (logstate, data, k-topsetsize, j+1, lastelt);
}


/* Return the median of a column of LOGFILEDATA. */
static double find_median (NCPTL_LOG_FILE_STATE *logstate, double *data,
                           ncptl_int datalen)
{
  if (datalen & 1)
    /* Odd number of data values -- there's only one median. */
    return find_k_median (logstate, data, (datalen+1)/2, 0, datalen-1);
  else {
    /* Even number of data values -- return the average of the two medians. */
    double topmed, botmed;
    topmed = find_k_median (logstate, data, (datalen+1)/2, 0, datalen-1);
    botmed = find_k_median (logstate, data, (datalen+1)-(datalen+1)/2, 0, datalen-1);
    return (topmed+botmed) / 2.0;
  }
}


/* Return the nth percentile of a column of LOGFILEDATA. */
static double find_percentile (NCPTL_LOG_FILE_STATE *logstate, double *data,
                               ncptl_int datalen, double percentile)
{
  double data_offset;                  /* Index into the sorted data */
  ncptl_int floor_data_offset;         /* Integral version of the above */
  double lower_value, upper_value;     /* Values read from data_offset and data_offset+1 */

  /* Handle the simple cases first. */
  if (percentile < 0.0 || percentile > 100.0)
    ncptl_fatal ("Percentile %.25g is invalid (must be from 0 to 100)", percentile);
  if (percentile == 0.0)
    return data[0];
  if (percentile == 100.0)
    return data[datalen - 1];

  /* Compute the percentile using a linear interpolation of the modes
   * for the order statistics for the uniform distribution on [0,1].
   * See http://en.wikipedia.org/wiki/Quantile for details. */
  data_offset = (datalen - 1)*percentile/100.0 + 1.0;
  floor_data_offset = (ncptl_int) floor(data_offset);
  lower_value = find_k_median (logstate, data, floor_data_offset, 0, datalen-1);
  upper_value = find_k_median (logstate, data, floor_data_offset + 1, 0, datalen-1);
  return lower_value + (data_offset - (double)floor_data_offset)*(upper_value - lower_value);
}


/* Return the median absolute deviation of a column of LOGFILEDATA. */
static double find_mad (NCPTL_LOG_FILE_STATE *logstate, double *data,
                        ncptl_int datalen)
{
  double median;     /* Median of the given data */
  double *abs_devs;  /* Absolute deviations of the given data from the median */
  double mad;        /* Median of the above */
  ncptl_int i;

  median = find_median (logstate, data, datalen);
  abs_devs = ncptl_malloc (datalen*sizeof(double), sizeof(double));
  for (i=0; i<datalen; i++)
    abs_devs[i] = fabs(data[i] - median);
  mad = find_median (logstate, abs_devs, datalen);
  ncptl_free(abs_devs);
  return mad;
}


/* Return the sum of a list of values. */
static double find_sum (double *data, ncptl_int datalen)
{
  double sum = 0.0;
  ncptl_int i;

  for (i=0; i<datalen; i++)
    sum += data[i];
  return sum;
}


/* Return the arithmetic mean of a list of values. */
static double find_mean (double *data, ncptl_int datalen)
{
  return find_sum (data, datalen) / datalen;
}


/* Return the variance of a list of values. */
static double find_variance (double *data, ncptl_int datalen)
{
  double variance = 0.0;
  double mean;
  ncptl_int i;

  if (datalen <= 1)
    return 0.0;

  mean = find_mean (data, datalen);
  for (i=0; i<datalen; i++) {
    double num = data[i] - mean;
    variance += num * num;
  }
  return variance / (datalen - 1.0);   /* Unbiased */
}


/* Return the standard deviation of a list of values. */
static double find_std_dev (double *data, ncptl_int datalen)
{
  return sqrt (find_variance (data, datalen));
}


/* Return the minimum of a list of values. */
static double find_minimum (double *data, ncptl_int datalen)
{
  double min = LARGEST_DOUBLE_VALUE;
  ncptl_int i;

  for (i=0; i<datalen; i++)
    if (min > data[i])
      min = data[i];
  return min;
}


/* Return the maximum of a list of values. */
static double find_maximum (double *data, ncptl_int datalen)
{
  double max = -LARGEST_DOUBLE_VALUE;
  ncptl_int i;

  for (i=0; i<datalen; i++)
    if (max < data[i])
      max = data[i];
  return max;
}


/* Return any value from a list of values but abort if there's more
 * than one value represented. */
static double find_only (double *data, ncptl_int datalen)
{
  double first = data[0];
  int i;

  for (i=1; i<datalen; i++)
    if (data[i] != first)
      ncptl_fatal ("Attempted to log more than one value in a \"THE\" column");
  return first;
}


/* Return the final value from a list of values. */
static double find_final (double *data, ncptl_int datalen)
{
  return data[datalen-1];
}


/* Return the harmonic mean of a list of values. */
static double find_harmonic_mean (double *data, ncptl_int datalen)
{
  double sum = 0.0;
  int i;

  for (i=0; i<datalen; i++)
    if (data[i])
      sum += 1.0 / data[i];
    else
      ncptl_fatal ("Attempted to take the harmonic mean of a set containing a zero element");
  return datalen / sum;
}


/* Return the geometric mean of a list of values. */
static double find_geometric_mean (double *data, ncptl_int datalen)
{
  double product = 1.0;
  int i;

  for (i=0; i<datalen; i++)
    if (data[i])
      product *= data[i];
    else
      ncptl_fatal ("Attempted to take the geometric mean of a set containing a zero element");
  return pow (product, 1.0/datalen);
}


/* Compare two values in a {value, tally} pair, returning one of -1,
 * 0, or 1 a la strcmp().  This is used by qsort(). */
static int hist_compare_value_tally (const void *first, const void *second)
{
  double firstval = ((VALUE_TALLY *)first)->value;
  double secondval = ((VALUE_TALLY *)second)->value;

  if (firstval < secondval)
    return -1;
  if (firstval > secondval)
    return +1;
  return 0;
}


/* Append VALUE and TALLY to the global HISTOGRAM_DATA queue. */
static void store_histogram_contents (void *value, void *tally)
{
  VALUE_TALLY newdata;

  newdata.value = *(double *)value;
  newdata.tally = *(uint64_t *)tally;
  ncptl_queue_push (histogram_data, (void *)&newdata);
}


/* Given a list of values and a queue, push a histogram of the values
 * onto the queue, alternating values and tallies. */
static void produce_histogram (double *data, ncptl_int datalen, NCPTL_QUEUE *histQ)
{
  NCPTL_SET *hist_set = ncptl_set_init (datalen, sizeof(double), sizeof(uint64_t));
  ncptl_int num_unique_values;    /* Unique {value, tally} pairs in the histogram */
  VALUE_TALLY *sorted_histogram;  /* Sorted list of {value, tally} pairs */
  ncptl_int i;

  /* Construct a set of {value, tally} pairs. */
  for (i=0; i<datalen; i++) {
    uint64_t *tally = (uint64_t *) ncptl_set_find (hist_set, (void *)&data[i]);
    uint64_t newtally;

    if (tally) {
      newtally = 1 + *tally;
      ncptl_set_remove (hist_set, (void *)&data[i]);
    }
    else
      newtally = 1;
    ncptl_set_insert (hist_set, (void *)&data[i], (void *)&newtally);
  }

  /* Walk the set, storing the unique values and tallies in the global
   * variable HISTOGRAM_DATA. */
  histogram_data = ncptl_queue_init (sizeof(VALUE_TALLY));
  ncptl_set_walk (hist_set, store_histogram_contents);
  num_unique_values = ncptl_queue_length(histogram_data);
  sorted_histogram = (VALUE_TALLY *) ncptl_queue_contents(histogram_data, 0);
  qsort ((void *)sorted_histogram, (size_t) num_unique_values,
         sizeof(VALUE_TALLY), hist_compare_value_tally);

  /* Push each {value, tally} pair onto HISTQ. */
  for (i=0; i<num_unique_values; i++) {
    double tally = (double) sorted_histogram[i].tally;
    ncptl_queue_push (histQ, (void *) &sorted_histogram[i].value);
    ncptl_queue_push (histQ, (void *) &tally);
  }

  /* Clean up. */
  ncptl_set_empty (hist_set);
  ncptl_free (hist_set);
  ncptl_queue_empty (histogram_data);
  ncptl_free (histogram_data);
}


/* Duplicate a string with all leading/trailing spaces removed and all
 * other whitespace characters converted to an ordinary space.  The
 * caller must ncptl_free() the result. */
static char *trimstring (char *oldstring)
{
  char *newstring = ncptl_strdup (oldstring);
  char *cb, *ce;

  /* Remove leading spaces. */
  for (cb=newstring; isspace((int)*cb); cb++)
    ;

  /* Remove trailing spaces. */
  for (ce=newstring+strlen(newstring)-1; ce>=cb && isspace((int)*ce); ce--)
    ;

  /* Shift the valid characters to the beginning of the string. */
  *++ce = '\0';
  (void) memmove (newstring, cb, ce-cb+1);

  /* Replace whitespace with " ". */
  for (cb=newstring; *cb; cb++)
    if (isspace((int)*cb))
      *cb = ' ';

  /* Return the result. */
  return newstring;
}


/* Determine clock wraparound time (problematic with a 32-bit cycle
 * counter). */
static double clock_wraparound_time (void)
{
  double wrapseconds = 0.0;
#if !defined(FORCE_GETTIMEOFDAY) && !defined(FORCE_MPI_WTIME)
# if NCPTL_TIMER_TYPE != 2
#  ifdef HAVE_GET_CYCLES
  if (sizeof(get_cycles()) < 8) {
    wrapseconds = pow(2.0, 8.0*sizeof(get_cycles()));
    wrapseconds /= ncptl_cycles_per_usec * 1.0e+6;
  }
#  elif defined(HAVE_SYS_SYSSGI_H) && defined(HAVE_SYSSGI)
  if (syssgi(SGI_CYCLECNTR_SIZE) < 64) {
    wrapseconds = pow(2.0, syssgi(SGI_CYCLECNTR_SIZE));
    wrapseconds /= ncptl_cycles_per_usec * 1.0e+6;
  }
#  elif defined(HAVE_ALPHA_CPU) && defined(READ_CYCLE_COUNTER)
  wrapseconds = pow(2.0, 32.0);
  wrapseconds /= ncptl_cycles_per_usec * 1.0e+6;
#  endif
# endif
# ifdef USE_HPET
  if (ncptl_hpet_works)
    wrapseconds = pow(2.0, 64.0) / 1e15;
# endif
#endif
  return wrapseconds;
}


/* Full expand the name of an executable file.  The result is returned
 * as a pointer to a static buffer. */
static char *fully_expanded_path (char *shortpath)
{
  static char expandedpath[PATH_MAX_VAR+1];    /* String to return */
  char *pathvar = getenv("PATH");              /* PATH environment variable */
  char *onedir;                                /* One directory in PATH */

  /* Ensure we have a PATH variable. */
  if (!pathvar) {
    /* No path?  Very strange, but do the best we can. */
    if (!realpath (shortpath, expandedpath))
      strcpy (expandedpath, shortpath);
    return expandedpath;
  }

  /* Try each element of PATH in turn.  Pray that there aren't any
   * directories with ":" in their name. */
  pathvar = ncptl_strdup (pathvar);
  for (onedir=strtok(pathvar, ":"); onedir; onedir=strtok(NULL, ":")) {
    char newpath[PATH_MAX_VAR+1];  /* onedir + shortpath */
    struct stat pathinfo;          /* Information about newpath */
    uid_t my_uid = geteuid();      /* This process's user ID */
    gid_t my_gid = getegid();      /* This process's group ID */

    sprintf (newpath, "%s/%s", onedir, shortpath);
    if (stat(newpath, &pathinfo)!=-1 && S_ISREG(pathinfo.st_mode) &&
        (((pathinfo.st_mode&S_IXUSR) && my_uid==pathinfo.st_uid) ||
         ((pathinfo.st_mode&S_IXGRP) && my_gid==pathinfo.st_gid) ||
         (pathinfo.st_mode&S_IXOTH))) {
      /* The file exists and we can execute it.  We must therefore
       * have the right file. */
      if (!realpath (newpath, expandedpath))
        strcpy (expandedpath, newpath);
      ncptl_free (pathvar);
      return expandedpath;
    }
  }

  /* We didn't find our path.  I don't know how, but let's try to
   * return something, anyway. */
  ncptl_free (pathvar);
  if (!realpath (shortpath, expandedpath))
    strcpy (expandedpath, shortpath);
  return expandedpath;
}


/* Compare two integers, returning one of -1, 0, or 1 a la strcmp().
 * This is used by qsort(). */
static int compare_ncptl_ints (const void *first, const void *second)
{
  ncptl_int firstval = *(ncptl_int *)first;
  ncptl_int secondval = *(ncptl_int *)second;

  if (firstval < secondval)
    return -1;
  if (firstval > secondval)
    return +1;
  return 0;
}


/* Destructively sort a list of numbers and return it as a string of
 * comma-separated ranges.  The caller must ncptl_free() the
 * result. */
static char *numbers_to_ranges (ncptl_int *values, ncptl_int numvalues)
{
  char *resultstr;       /* String to return */
  ncptl_int stringlen;   /* Bytes allocated for the above */
  char *endresultstr;    /* Pointer to the NULL at the end of resultstr */
  ncptl_int rangebegin;  /* Starting value in the current range */
  ncptl_int rangeend;    /* Ending value in the current range */
  ncptl_int i;

  /* Allocate memory for the worst-case resulting string. */
  for (i=0, stringlen=0; i<numvalues; i++) {
    char onenum[25];      /* Storage for a single ASCII number */
    sprintf (onenum, "%" NICS, values[i]);
    stringlen += strlen (onenum) + 1;        /* +1 for dash, comma, or NULL */
  }
  resultstr = ncptl_malloc (stringlen*sizeof(char), 0);

  /* Sort the input list. */
  qsort((void *)values, (size_t)numvalues, sizeof(ncptl_int), compare_ncptl_ints);

  /* Construct a string of ranges. */
  endresultstr = resultstr;
  rangebegin = rangeend = values[0];
  for (i=1; i<numvalues; i++) {
    if (values[i] == values[i-1]+1)
      /* Next sequential value -- extend the current range. */
      rangeend = values[i];
    else
      if (values[i] > values[i-1]+1) {
        /* Skipped value -- start a new range. */
        if (rangebegin == rangeend)
          sprintf (endresultstr, "%s%" NICS,
                   rangebegin == values[0] ? "" : ",", rangeend);
        else
          sprintf (endresultstr, "%s%" NICS "%c%" NICS,
                   rangebegin == values[0] ? "" : ",", rangebegin,
                   rangeend == rangebegin+1 ? ',' : '-', rangeend);
        endresultstr += strlen (endresultstr);
        rangebegin = rangeend = values[i];
      }
  }

  /* Append the final range. */
  if (rangebegin == rangeend)
    sprintf (endresultstr, "%s%" NICS,
             rangebegin == values[0] ? "" : ",", rangeend);
  else
    sprintf (endresultstr, "%s%" NICS "%c%" NICS,
             rangebegin == values[0] ? "" : ",", rangebegin,
             rangeend == rangebegin+1 ? ',' : '-', rangeend);
  return resultstr;
}


/* Delay for a random number of microseconds. */
static void log_random_delay (NCPTL_LOG_FILE_STATE *logstate)
{
  uint64_t usec_delay;           /* Delay in microseconds. */

  if (!logstate->log_delay)
    return;
  usec_delay = ncptl_genrand_int64 (&logstate->random_state) % logstate->log_delay;
  ncptl_udelay (usec_delay, 0);
}


/* Write a string to the log file. Currently, no file error-checking is
 * performed. */
static void log_printf (NCPTL_LOG_FILE_STATE *logstate, const char *format, ...)
{
  va_list args;

  va_start (args, format);
  if (logstate->logfile)
    /* File */
    (void) vfprintf (logstate->logfile, format, args);
  else {
    /* String */
    while (1) {
      int bytes_available = (int) (logstate->log_contents_allocated - logstate->log_contents_used);
      int bytes_needed = vsnprintf(&logstate->log_contents[logstate->log_contents_used-1],  /* Overwrite the trailing '\0'. */
                               bytes_available, format, args);
      if (bytes_needed == -1 || bytes_needed+1 >= bytes_available) {
        /* We need to allocate more memory for log_contents and try again. */
        if (bytes_needed < LOG_CONTENTS_INCREMENT)
          bytes_needed = LOG_CONTENTS_INCREMENT;
        logstate->log_contents_allocated += bytes_needed;
        logstate->log_contents = ncptl_realloc(logstate->log_contents,
                                               logstate->log_contents_allocated,
                                               0);
      }
      else {
        logstate->log_contents_used += bytes_needed;
        break;
      }
    }
  }
  va_end (args);
}


/* Write a character to the log file.  Currently, no error-checking is
 * performed. */
static void log_putc (NCPTL_LOG_FILE_STATE *logstate, int onechar)
{
  if (logstate->logfile)
    /* File */
    (void) fputc (onechar, logstate->logfile);
  else {
    /* String */
    if (logstate->log_contents_used == logstate->log_contents_allocated) {
      /* Allocate more memory. */
      logstate->log_contents_allocated += LOG_CONTENTS_INCREMENT;
      logstate->log_contents = ncptl_realloc(logstate->log_contents,
                                             logstate->log_contents_allocated,
                                             0);
    }
    logstate->log_contents[logstate->log_contents_used-1] = (char) onechar;  /* Overwrite the trailing '\0'. */
    logstate->log_contents[logstate->log_contents_used++] = '\0';
  }
}


/* Flush the log file.  Currently, no error-checking is performed. */
static void log_flush (NCPTL_LOG_FILE_STATE *logstate)
{
  if (!logstate->logfile)
    /* String */
    return;
  log_random_delay (logstate);
  (void) fflush (logstate->logfile);
}


/* Write a key:value pair to the log file.  This is intended to be
 * used for outputting prologue/epilogue information.  For
 * convenience, the value argument is a printf()-like template
 * followed by the corresponding data to plug in. */
static void log_key_value (NCPTL_LOG_FILE_STATE *logstate,
                           const char *key, const char *valuefmt, ...)
{
  char keycopy[NCPTL_MAX_LINE_LEN]; /* Copied and padded version of KEY */
  char value[NCPTL_MAX_LINE_LEN];   /* Formatted version of VALUEFMT */
  void *prev_value;            /* Value from a previous insertion of KEY */
  va_list args;                /* Arguments used to create VALUE */
  char *cleankey;              /* Copy of KEY with all colons replaced with periods */
  char *colon;                 /* Pointer to the first colon in CLEANKEY */

  /* Store a formatted version of VALUEFMT in VALUE and a padded
   * version of KEY in KEYCOPY. */
  va_start (args, valuefmt);
  vsnprintf (value, NCPTL_MAX_LINE_LEN, valuefmt, args);
  va_end (args);
  memset (keycopy, 0, NCPTL_MAX_LINE_LEN);
  strcpy (keycopy, key);

  /* Add the key:value pair to the prologue/epilogue database. */
  prev_value = ncptl_set_find (logstate->log_database, (void *) keycopy);
  if (prev_value)
    ncptl_set_remove (logstate->log_database, (void *) keycopy);
  ncptl_set_insert (logstate->log_database, (void *) keycopy, (void *) value);

  /* Write the key and value to the log file. */
  cleankey = ncptl_strdup (key);
  while ((colon=strchr(cleankey, ':')))
    *colon = '.';
  log_printf (logstate, "# %s: %s\n", cleankey, value);
  ncptl_free (cleankey);
}


/* Log a key and a doubleword value but append an SI prefix to the value. */
static void log_key_value_SI (NCPTL_LOG_FILE_STATE *logstate,
                              const char *key, const double value,
                              const char *unitname, const char *unit,
                              const double unitsize, const char *extratext)
{
  char *prefmults = " KMGTPEZY";    /* SI prefixes */
  double abbrvalue = value;         /* Abbreviated display of VALUE */

  while (*(prefmults+1) && abbrvalue>unitsize) {
    prefmults++;
    abbrvalue /= unitsize;
  }
  if (*prefmults == ' ')
    log_key_value (logstate, key, "%.0f %s%s", value, unitname, extratext);
  else
    log_key_value (logstate, key, "%.0f %s (%.1f %c%s)%s",
                   value, unitname, abbrvalue, *prefmults, unit, extratext);
}


/* Write an argc/argv[] argument array to the log file. */
static void log_write_command_line (NCPTL_LOG_FILE_STATE *logstate,
                                    char *key, int argc, char **argv)
{
  char *commandline;       /* Entire command line */
  size_t numbytes = 0;     /* Min. # of bytes in the above */
  char *clptr;             /* Pointer into commandline[] */
  int i;
  size_t j;

  /* Allocate more than enough space to store all command-line
   * arguments. */
  for (i=0; i<argc; i++)
    numbytes += strlen(argv[i]) + 1;
  clptr = commandline = (char *) ncptl_malloc (4*numbytes+2, 0);

  /* Escape characters that are special to the shell. */
  for (i=0; i<argc; i++) {
    *clptr++ = ' ';
    numbytes = strlen (argv[i]);
    for (j=0; j<numbytes; j++)
      switch (argv[i][j]) {
        /* First, check for punctuation that *isn't* special. */
        case '#':
        case '%':
        case '+':
        case ',':
        case '-':
        case '.':
        case '/':
        case ':':
        case '=':
        case '@':
        case '^':
        case '_':
          *clptr++ = argv[i][j];
          break;

        /* Of the remaining characters, only alphanumerics don't need
         * to be escaped. */
        default:
          if (!isalnum((int)argv[i][j]))
            *clptr++ = '\\';
          if (iscntrl((int)argv[i][j])) {
            /* Output control characters in octal. */
            sprintf (clptr, "%03o", (int)argv[i][j]);
            while (*clptr)
              clptr++;
          }
          else
            *clptr++ = argv[i][j];
          break;
      }
  }
  *clptr = '\0';

  /* Output the command line and clean up. */
  log_key_value (logstate, key, "%s", commandline+1);
  ncptl_free (commandline);
}


#if PROC_CMD_LINE_TYPE == 2
/* Write the contents of /proc/<PID>/cmdline as a command line to the
 * log file.  Return 1 on success, 0 on failure. */
static int log_write_proc_cmdline (NCPTL_LOG_FILE_STATE *logstate,
                                   char *key, char *filename)
{
  int cmd_fd;                /* File descriptor for filename */
  char commandline[NCPTL_MAX_LINE_LEN];   /* Command line as a single string */
  char *cmd_ptr = commandline;            /* Pointer into commandline[] */
  char *cmd_argv[NCPTL_MAX_LINE_LEN];     /* Pointers into commandline[] */
  int cmd_argc = 0;          /* Number of entries in cmd_argv[] */
  ssize_t cmd_len;           /* Number of bytes in commandline[] */

  /* Read the entire file into commandline[]. */
  if ((cmd_fd=open(filename, O_RDONLY)) == -1)
    return 0;
  if ((cmd_len=read(cmd_fd, commandline, NCPTL_MAX_LINE_LEN)) < 1)
    return 0;
  (void) close (cmd_fd);

  /* Split commandline[] into cmd_argv[] and update cmd_argc accordingly. */
  for (cmd_ptr=commandline; cmd_ptr<&commandline[cmd_len]; cmd_ptr+=strlen(cmd_ptr)+1)
    cmd_argv[cmd_argc++] = cmd_ptr;
  cmd_argv[cmd_argc] = NULL;

  /* Output the command line. */
  log_write_command_line (logstate, key, cmd_argc, cmd_argv);
  return 1;
}
#endif


/* Write a time value in a user-friendly format. */
static void log_write_friendly_time (NCPTL_LOG_FILE_STATE *logstate, double num_seconds_float)
{
  uint64_t num_seconds;         /* Integral number of seonds */
  uint64_t days, hours, minutes, seconds;    /* Categorized version of elapsed_time */
  int needcomma;                /* 0=don't prepend a command; >0=prepend */
  char *prefix;                 /* Prefix to output before first term. */

#define LOG_PRINTF_TERM(TERM, TERMSTR)                  \
    if (TERM)                                           \
      log_printf (logstate, "%s%" PRIu64 " %s%s",       \
                        needcomma++ ? ", " : prefix,    \
                        TERM,                           \
                        TERMSTR,                        \
                        TERM==1 ? "" : "s")

  num_seconds = (uint64_t) (num_seconds_float + 0.5);
  log_printf (logstate, "%" PRIu64 " second%s",
              num_seconds, num_seconds==1 ? "" : "s");
  if (num_seconds >= 60) {
    needcomma = 0;
    prefix = " (i.e., ";
    seconds = num_seconds % 60;
    num_seconds /= 60;
    minutes = num_seconds % 60;
    num_seconds /= 60;
    hours = num_seconds % 24;
    num_seconds /= 24;
    days = num_seconds;
    LOG_PRINTF_TERM (days,    "day");
    LOG_PRINTF_TERM (hours,   "hour");
    LOG_PRINTF_TERM (minutes, "minute");
    LOG_PRINTF_TERM (seconds, "second");
    log_printf (logstate, ")");
  }
}


/* Write miscellaneous, basic information to the log file. */
static void log_write_prologue_basic (NCPTL_LOG_FILE_STATE *logstate,
                                      char *progname,
                                      char *program_uuid,
                                      char *backend_name,
                                      char *backend_desc,
                                      ncptl_int tasks)
{
  char currentdir[PATH_MAX_VAR+1];      /* Current working directory */
#if PROC_CMD_LINE_TYPE == 1
  char procfilename[PATH_MAX_VAR+1];    /* File containing our original command line */
#endif

  /* Write our arguments to the log file. */
  log_key_value (logstate, "coNCePTuaL version", "%s", PACKAGE_VERSION);
  log_key_value (logstate, "coNCePTuaL backend", "%s (%s)",
                 backend_name, backend_desc);
  log_key_value (logstate, "Executable name", "%s", fully_expanded_path(progname));
  if (getcwd (currentdir, PATH_MAX_VAR))
    log_key_value (logstate, "Working directory", "%s", currentdir);

  /* Write the current command line to the log file.  In a future
   * version of the code we may write our parent's command line, as
   * well. */
#if PROC_CMD_LINE_TYPE == 2
  if (!log_write_proc_cmdline (logstate, "Command line", PROC_CMD_LINE))
#elif PROC_CMD_LINE_TYPE == 1
  sprintf (procfilename, PROC_CMD_LINE, getpid());
  if (!log_write_proc_cmdline (logstate, "Command line", procfilename))
#endif
    if (ncptl_argc_copy)
      log_write_command_line (logstate, "Command line", ncptl_argc_copy, ncptl_argv_copy);

  /* Say how many tasks and processors we have available to us. */
  log_key_value (logstate, "Number of tasks", "%" NICS, tasks);
  log_key_value (logstate, "Rank (0<=P<tasks)", "%" NICS, logstate->process_rank);

  /* Log a unique identifier for this particular program execution. */
  log_key_value (logstate, "Unique execution identifier", program_uuid);
}


/* Output a list of all of the network interfaces we know about. */
static void log_write_prologue_hardware_networks (NCPTL_LOG_FILE_STATE *logstate)
{
  ncptl_int num_networks;       /* Total number of networks */
  ncptl_int net_num = 0;        /* Current network number */
  char **net_strings;           /* List of strings describing our networks */

  if (!systeminfo.networks)
    return;
  num_networks = ncptl_queue_length (systeminfo.networks);
  net_strings = ncptl_queue_contents (systeminfo.networks, 0);
  for (net_num=0; net_num < num_networks; net_num++) {
    char key[50];    /* "Network interface N" with N being a 64-bit number */

    sprintf (key, "Network interface %" NICS, net_num+1);
    log_key_value (logstate, key, "%s", net_strings[net_num]);
  }
}


#ifdef HAVE_LIBELAN
/* Output some interesting Elan-specific information. */
static void log_write_prologue_hardware_elan (NCPTL_LOG_FILE_STATE *logstate)
{
  int numcaps;                  /* Number of capabilities (usually 1) */
  int c;

  /* Get the number of capabilities. */
  if (rms_ncaps(&numcaps) == -1)
    return;

  /* Output each capability in turn. */
  for (c=0; c<numcaps; c++) {
    ELAN_CAPABILITY elancap;    /* Current Elan capability */
    char capstring[50];         /* Sufficient space for "Elan capability" and a number */

    if (rms_getcap(c, &elancap) == -1)
      continue;
    if (c == 0)
      strcpy (capstring, "Elan capability");
    else
      sprintf (capstring, "Elan capability %d", c+1);
    log_key_value (logstate, capstring,
                   "[%x.%x.%x.%x] Version %x Type %x Context %x.%x.%x Node %x.%x",
                   elancap.cap_userkey.key_values[0],
                   elancap.cap_userkey.key_values[1],
                   elancap.cap_userkey.key_values[2],
                   elancap.cap_userkey.key_values[3],
                   elancap.cap_version, elancap.cap_type,
                   elancap.cap_lowcontext, elancap.cap_mycontext,
                   elancap.cap_highcontext,
                   elancap.cap_lownode, elancap.cap_highnode);
  }
}
#endif


#ifdef HAVE_BGPPERSONALITY
/* Output some interesting BlueGene/P-specific information. */
static void log_write_prologue_hardware_bgp (NCPTL_LOG_FILE_STATE *logstate)
{
  unsigned int xsize = ncptl_bgp_personality.Network_Config.Xnodes;
  unsigned int ysize = ncptl_bgp_personality.Network_Config.Ynodes;
  unsigned int zsize = ncptl_bgp_personality.Network_Config.Znodes;
  unsigned int xloc = ncptl_bgp_personality.Network_Config.Xcoord;
  unsigned int yloc = ncptl_bgp_personality.Network_Config.Ycoord;
  unsigned int zloc = ncptl_bgp_personality.Network_Config.Zcoord;

  /* Log information about the node. */
  log_key_value (logstate, "Node coordinate within the BlueGene/P partition", "(%u, %u, %u)",
                 xloc, yloc, zloc);

  /* Log information about the partition. */
  log_key_value (logstate, "BlueGene/P partition size", "%u * %u * %u = %lu nodes",
                 xsize, ysize, zsize,
                 (unsigned long)xsize * (unsigned long)ysize * (unsigned long)zsize);
}
#endif


#ifdef HAVE_BGLPERSONALITY
/* Output some interesting BlueGene/L-specific information. */
static void log_write_prologue_hardware_bgl (NCPTL_LOG_FILE_STATE *logstate)
{
  const char *part_top = "BlueGene/L partition topology";
  unsigned int xsize = (unsigned int) BGLPersonality_xSize(&ncptl_bgl_personality);
  unsigned int ysize = (unsigned int) BGLPersonality_ySize(&ncptl_bgl_personality);
  unsigned int zsize = (unsigned int) BGLPersonality_zSize(&ncptl_bgl_personality);
  int torusx = BGLPersonality_isTorusX(&ncptl_bgl_personality);
  int torusy = BGLPersonality_isTorusY(&ncptl_bgl_personality);
  int torusz = BGLPersonality_isTorusZ(&ncptl_bgl_personality);
  int vnm = BGLPersonality_virtualNodeMode(&ncptl_bgl_personality);
  char nodeloc[NCPTL_MAX_LINE_LEN];

  /* Log information about the node. */
  BGLPersonality_getLocationString (&ncptl_bgl_personality, nodeloc);
  log_key_value (logstate, "BlueGene/L node location", nodeloc);
  log_key_value (logstate, "Node coordinate within the BlueGene/L partition", "(%u, %u, %u)",
                 BGLPersonality_xCoord(&ncptl_bgl_personality),
                 BGLPersonality_yCoord(&ncptl_bgl_personality),
                 BGLPersonality_zCoord(&ncptl_bgl_personality));

  /* Log information about the partition. */
  switch (torusz*4 + torusy*2 + torusx) {
    case 0:
      {
        unsigned int dimens[3];      /* Dimensions in non-descending order */

        /* Sort the X, Y, and Z dimensions. */
        dimens[0] = xsize;
        dimens[1] = ysize;
        dimens[2] = zsize;
        if (dimens[0] > dimens[1]) {
          unsigned int larger = dimens[0];
          dimens[0] = dimens[1];
          dimens[1] = larger;
        }
        if (dimens[0] > dimens[2]) {
          unsigned int larger = dimens[0];
          dimens[0] = dimens[2];
          dimens[2] = larger;
        }
        if (dimens[1] > dimens[2]) {
          unsigned int larger = dimens[1];
          dimens[1] = dimens[2];
          dimens[2] = larger;
        }

        /* Output the appropriate topology. */
        if (dimens[2] == 1)
          log_key_value (logstate, part_top, "single node");
        else
          if (dimens[1] == 1)
            log_key_value (logstate, part_top, "1-D mesh");
          else
            if (dimens[0] == 1)
              log_key_value (logstate, part_top, "2-D mesh");
            else
              log_key_value (logstate, part_top, "3-D mesh");
      }
      break;

    case 1:
      log_key_value (logstate, part_top, "torus in X, mesh in Y and Z");
      break;

    case 2:
      log_key_value (logstate, part_top, "torus in Y, mesh in X and Z");
      break;

    case 3:
      log_key_value (logstate, part_top, "torus in X and Y, mesh in Z");
      break;

    case 4:
      log_key_value (logstate, part_top, "torus in Z, mesh in X and Y");
      break;

    case 5:
      log_key_value (logstate, part_top, "torus in X and Z, mesh in Y");
      break;

    case 6:
      log_key_value (logstate, part_top, "torus in Y and Z, mesh in Z");
      break;

    case 7:
      log_key_value (logstate, part_top, "3-D torus");
      break;

    default:
      ncptl_fatal ("Internal error in %s, line %d", __FILE__, __LINE__);
      break;
  }
  log_key_value (logstate, "BlueGene/L partition size", "%u * %u * %u = %lu nodes",
                 xsize, ysize, zsize,
                 (unsigned long)xsize * (unsigned long)ysize * (unsigned long)zsize);
  log_key_value (logstate, "BlueGene/L node mode", vnm ? "virtual" : "coprocessor");
}
#endif

#if defined(HAVE__MY_PNID) || defined(CRAY_XT_NID_FILE)
/* Write some Cray-specific information to the log file. */
static void log_write_prologue_hardware_xt (NCPTL_LOG_FILE_STATE *logstate)
{
# ifdef HAVE__MY_PNID
  extern uint32_t _my_pnid;       /* Predefined */
# elif defined(CRAY_XT_NID_FILE)
  uint32_t _my_pnid;              /* To be read from CRAY_XT_NID_FILE */
# else
#  error Unable to determine how to read a Cray node ID
# endif
  char rsinfostr[NCPTL_MAX_LINE_LEN];
# if defined(HAVE_RCAMESHTOPOLOGY) || defined(HAVE_RSMSEVENT)
  rs_node_t physinfo;
  char *env_topo_class = getenv("RSMS_TOPO_CLASS");
# endif
# ifdef HAVE_RCAMESHCOORD
  rca_mesh_coord_t mesh_coord;
# endif

# if !defined(HAVE__MY_PNID) && defined(CRAY_XT_NID_FILE)
  {
    /* We need to read our node ID from a file. */
    FILE *nidfile;
    if (!(nidfile=fopen(CRAY_XT_NID_FILE, "r")))
      return;
    if (fscanf(nidfile, "%u", &_my_pnid) != 1) {
      fclose(nidfile);
      return;
    }
    fclose(nidfile);
  }
# endif

  /* Write our physical node ID. */
  sprintf (rsinfostr, "%u", _my_pnid);
  log_key_value (logstate, "Cray node ID", rsinfostr);

  /* Use topology class information to interpret the physical node ID. */
# ifdef HAVE_RCAMESHTOPOLOGY
  {
    int topo;                  /* Topology class */

    rca_get_meshtopology(&topo);
    log_key_value (logstate, "Cray topology class", get_topo_str(topo));
    rca_get_nodeid(&physinfo);
    rs_phys2str(&physinfo, rsinfostr);
    log_key_value (logstate, "Cray node location", rsinfostr);
  }
# elif defined(HAVE_RSMSEVENT)
  /* The topology class defaults to class 4 because that's what some
   * of Cray's programs do.  The user can override the default by
   * setting RSMS_TOPO_CLASS. */
  rs_nid_init (env_topo_class ? atoi(env_topo_class) : RS_TOPO_CLASS_4);
  log_key_value (logstate, "Cray topology class", get_topo_str(topo_class));
  memset ((void *)&physinfo, 0, sizeof(rs_node_t));
  rs_nid2phys(_my_pnid, rt_node, &physinfo);
  rs_format_phys (&physinfo, rsinfostr);
  log_key_value (logstate, "Cray node location", rsinfostr);
# else
  /* Newer Cray systems maintain node location in the /proc filesystem. */
  do {
    FILE *cnamefile;
    int col, row, cage, slot, node;
    char physinfostr[NCPTL_MAX_LINE_LEN];

    if (!(cnamefile=fopen (CRAY_XC_CNAME_FILE, "r")))
      break;
    if (fscanf (cnamefile, "c%d-%dc%ds%dn%d", &col, &row, &cage, &slot, &node) != 5) {
      fclose (cnamefile);
      break;
    }
    fclose (cnamefile);
    sprintf (physinfostr, "column %d, row %d, cage %d, slot %d, node %d (c%d-%dc%ds%dn%d)",
             col, row, cage, slot, node,
             col, row, cage, slot, node);
    log_key_value (logstate, "Cray node location", physinfostr);
  }
  while (0);
# endif

# ifdef HAVE_RCAMESHCOORD
  if (rca_get_meshcoord ((uint16_t)_my_pnid, &mesh_coord) == 0) {
    sprintf (rsinfostr, "(%u, %u, %u)",
             mesh_coord.mesh_x, mesh_coord.mesh_y, mesh_coord.mesh_z);
    log_key_value (logstate, "Cray node coordinates", rsinfostr);
  }
# endif
}
#endif


#ifdef ODM_IS_SUPPORTED
/* Write information gathered via ODM to the log file. */
static void log_write_prologue_hardware_odm (NCPTL_LOG_FILE_STATE *logstate)
{
  struct CuAt *cuat_info;
  int num_instances;

  if (odm_initialize())
    return;
  if ((cuat_info=getattr ("sys0", "modelname", 0, &num_instances))
      && cuat_info->value)
    log_key_value (logstate, "System model", cuat_info->value);
  if ((cuat_info=getattr ("sys0", "frequency", 0, &num_instances))
      && cuat_info->value) {
    double bus_freq;

    sscanf (cuat_info->value, "%lf", &bus_freq);
    log_key_value_SI (logstate, "System-bus frequency", bus_freq,
                      "Hz", "Hz", 1000.0, "");
  }
  (void) odm_terminate();
}
#endif


#ifdef HAVE_OPENIB
/* Convert from an InfiniBand MTU to a byte count. */
static int mtu_to_bytes (enum ibv_mtu mtu)
{
  int bytes = -1;

  switch (mtu) {
    case IBV_MTU_256:
      bytes = 256;
      break;
    case IBV_MTU_512:
      bytes = 512;
      break;
    case IBV_MTU_1024:
      bytes = 1024;
      break;
    case IBV_MTU_2048:
      bytes = 2048;
      break;
    case IBV_MTU_4096:
      bytes = 4096;
      break;
    default:
      break;
  }
  return bytes;
}


/* Convert from an InfiniBand link width to an "X" number. */
static int width_to_x (uint8_t width)
{
  int xnum = -1;

  switch (width) {
    case 1:
      xnum = 1;
      break;
    case 2:
      xnum = 4;
      break;
    case 4:
      xnum = 8;
      break;
    case 8:
      xnum = 12;
      break;
    default:
      break;
  }
  return xnum;
}


/* Convert from an InfiniBand link speed to gigabits per second. */
static double speed_to_gbps (uint8_t speed)
{
  double gbps = -1.0;

  switch (speed) {
    case 1:
      gbps = 2.5;
      break;
    case 2:
      gbps = 5.0;
      break;
    case 4:
      gbps = 10.0;
      break;
    default:
      break;
  }
  return gbps;
}


/* Write OpenIB InfiniBand-related information to the log file. */
static void log_write_prologue_hardware_openib (NCPTL_LOG_FILE_STATE *logstate)
{
  struct ibv_device **hcalist;      /* List of InfiniBand HCAs */
  int numhcas = -1;                 /* Number of entries in the above */
  struct ibv_context *hcactx;       /* HCA device context */
  struct ibv_device_attr hca_attr;  /* HCA device attributes */
  int port;                         /* Current port number */
  int liveports = 0;                /* Tally of live ports */
  struct ibv_port_attr first_port_attr;  /* Port attributes of first live port */

  /* Open the InfiniBand HCA. */
#ifdef HAVE_IBV_GET_DEVICE_LIST
  hcalist = ibv_get_device_list(&numhcas);
  if (!hcalist || numhcas<=0)
    return;
#elif HAVE_IBV_GET_DEVICES
  hcalist = ibv_get_devices();
  if (!hcalist)
    return;
# define ibv_free_device_list free
#else
# error Unrecognized OpenIB library version
#endif

  /* Log information about the first HCA in the list. */
  hcactx = ibv_open_device(*hcalist);
  if (!hcactx) {
    ibv_free_device_list (hcalist);
    return;
  }
  if (ibv_query_device(hcactx, &hca_attr)) {
    (void) ibv_close_device (hcactx);
    ibv_free_device_list (hcalist);
    return;
  }
#ifdef HAVE_PCIUTILS
  /* Output only the firmware version; everything else is redundant
   * with the PCI Utilities' output. */
  log_key_value (logstate,
                 "InfiniBand HCA firmware version",
                 "%s",
                 hca_attr.fw_ver);
#else
  log_key_value (logstate,
                 "InfiniBand HCA",
                 "vendor 0x%04X, part %d, revision 0x%X, firmware version %s",
                 hca_attr.vendor_id,
                 hca_attr.vendor_part_id,
                 hca_attr.hw_ver,
                 hca_attr.fw_ver);
#endif
  if (numhcas > 0)
    log_key_value (logstate, "InfiniBand HCA count", "%d", numhcas);

  /* Log information about the first port on the first HCA. */
  memset(&first_port_attr, 0, sizeof(struct ibv_port_attr));  /* Silence whiny C compilers. */
  for (port=1; port<=hca_attr.phys_port_cnt; port++) {
    struct ibv_port_attr port_attr;    /* Port attributes */

    if (ibv_query_port(hcactx, port, &port_attr))
      continue;
    if (port_attr.state == IBV_PORT_ACTIVE
        && port_attr.phys_state == 5)
      if (++liveports == 1)
        first_port_attr = port_attr;
  }
  if (liveports) {
    int link_width = width_to_x (first_port_attr.active_width);
    double link_speed = speed_to_gbps (first_port_attr.active_speed);

    if (link_width > 0 && link_speed > 0.0)
      log_key_value (logstate,
                     "InfiniBand link speed",
                     "%dX * %.3g Gbps * %d live+active port(s) = %.3g Gbps",
                     link_width, link_speed, liveports,
                     link_width*link_speed*liveports);
    log_key_value_SI (logstate,
                      "InfiniBand MTU size",
                      mtu_to_bytes(first_port_attr.active_mtu),
                      "bytes", "B", 1024.0, "");
  }

  /* Close the InfiniBand HCA. */
  (void) ibv_close_device (hcactx);
  ibv_free_device_list (hcalist);
}
#endif

/* Write hardware and OS information to the log file .*/
static void log_write_prologue_hardware (NCPTL_LOG_FILE_STATE *logstate)
{
  /* Define some key strings to pass to log_key_value(). */
  const char *cpu_freq = "CPU frequency";
  const char *cc_freq = "Cycle-counter frequency";
#ifdef CYCLES_PER_USEC
  const char *cc_freq_hw = " [hardwired at compile time]";
#else
  const char *cc_freq_hw = "";
#endif
  const char *phys_mem = "Physical memory";

#define LOG_CONDITIONALLY(KEY, FMT, FIELD)              \
  do {                                                  \
    if (systeminfo.FIELD)                               \
      log_key_value (logstate, KEY, FMT, systeminfo.FIELD); \
  }                                                     \
  while (0)
#define LOG_CONDITIONALLY_TRIMMED(KEY, FMT, FIELD)      \
  do {                                                  \
    if (systeminfo.FIELD) {                             \
      char *trimmed = trimstring (systeminfo.FIELD);    \
      log_key_value (logstate, KEY, FMT, trimmed);      \
      ncptl_free (trimmed);                             \
    }                                                   \
  }                                                     \
  while (0)

  /* Log whatever hardware and OS information we have. */
  LOG_CONDITIONALLY_TRIMMED ("Host name",               "%s", hostname);
  LOG_CONDITIONALLY_TRIMMED ("Operating system",        "%s", os);
  LOG_CONDITIONALLY_TRIMMED ("OS distribution",         "%s", osdist);
  LOG_CONDITIONALLY_TRIMMED ("Computer make and model", "%s", computer);
  LOG_CONDITIONALLY_TRIMMED ("BIOS version",            "%s", bios);
  LOG_CONDITIONALLY_TRIMMED ("CPU vendor",              "%s", cpu_vendor);
  LOG_CONDITIONALLY_TRIMMED ("CPU architecture",        "%s", arch);
  LOG_CONDITIONALLY_TRIMMED ("CPU model",               "%s", cpu_model);
  LOG_CONDITIONALLY_TRIMMED ("CPU flags",               "%s", cpu_flags);
  LOG_CONDITIONALLY         ("Hardware threads per CPU core", "%d", threads_per_core);
  LOG_CONDITIONALLY         ("CPU cores per socket",    "%d", cores_per_socket);
  LOG_CONDITIONALLY         ("CPU sockets per node",    "%d", sockets_per_node);
  LOG_CONDITIONALLY         ("Total CPU contexts per node", "%d", contexts_per_node);
  if (systeminfo.cpu_freq)
    log_key_value_SI (logstate, cpu_freq, systeminfo.cpu_freq, "Hz", "Hz", 1000.0, "");
  if (systeminfo.timer_freq)
    log_key_value_SI (logstate, cc_freq, systeminfo.timer_freq, "Hz", "Hz", 1000.0, cc_freq_hw);
  else
    if (systeminfo.cpu_freq)
      log_key_value (logstate, cc_freq, "(assumed to be the same as the CPU frequency)");
  LOG_CONDITIONALLY ("OS page size", "%" PRIu64 " bytes", pagesize);
#ifdef OS_PAGE_SIZE
  log_printf (logstate, "# WARNING: Page size was specified manually at configuration time.\n");
#endif
  if (systeminfo.physmem)
    log_key_value_SI (logstate, phys_mem, (double)systeminfo.physmem,
                      "bytes", "B", 1024.0, "");
#undef LOG_CONDITIONALLY
#undef LOG_CONDITIONALLY_TRIMMED

  log_write_prologue_hardware_networks (logstate);
#ifdef HAVE_LIBELAN
  log_write_prologue_hardware_elan (logstate);
#endif
#ifdef HAVE_BGPPERSONALITY
  log_write_prologue_hardware_bgp (logstate);
#endif
#ifdef HAVE_BGLPERSONALITY
  log_write_prologue_hardware_bgl (logstate);
#endif
#if defined(HAVE__MY_PNID) || defined(CRAY_XT_NID_FILE)
  log_write_prologue_hardware_xt (logstate);
#endif
#ifdef ODM_IS_SUPPORTED
  log_write_prologue_hardware_odm (logstate);
#endif
#ifdef HAVE_OPENIB
  log_write_prologue_hardware_openib (logstate);
#endif
}


/* Write to the log file which CPUs this thread can migrate to. */
static void log_write_prologue_thread_affinity (NCPTL_LOG_FILE_STATE *logstate)
{
#ifdef HAVE_SCHED_H
  cpu_set_t cpumask;                /* Bit mask of the CPUs we can use */
  ncptl_int cpulist[CPU_SETSIZE];   /* List of available CPUs */
  ncptl_int numcpus = 0;            /* Number of valid entries in the above */
  char *cpustring;                  /* Compacted string version of cpulist[] */
  int i;

  if (sched_getaffinity (0, sizeof(cpu_set_t), &cpumask) == -1)
    return;
  for (i=0; i<CPU_SETSIZE; i++)
    if (CPU_ISSET(i, &cpumask))
      cpulist[numcpus++] = i;
  cpustring = numbers_to_ranges (cpulist, numcpus);
  log_key_value (logstate, "Thread affinity (CPU numbers)", cpustring);
  ncptl_free (cpustring);
  if (numcpus > 1)
    log_printf (logstate, "# WARNING: Threads can migrate among %" NICS " CPUs, which may cause performance variability.\n",
                numcpus);
#else
  dummyvar.vp = logstate;   /* Convince the compiler that logstate is not an unused parameter. */
#endif
}


/* Write to the log file information about the build of the run-time
 * library. */
static void log_write_prologue_library (NCPTL_LOG_FILE_STATE *logstate)
{
  int isize = sizeof(int);
  int lsize = sizeof(long);
  int psize = sizeof(void *);
  char *compiler_mode = "nonstandard (neither ILP32 nor LP64)";
  char *somestring;

  somestring = trimstring (CONFIGURE_COMMAND);
  log_key_value (logstate, "coNCePTuaL configuration", "%s", somestring);
  ncptl_free (somestring);

  somestring = trimstring (RT_COMPILER);
  log_key_value (logstate, "Library compiler+linker", "%s", somestring);
  ncptl_free (somestring);

  somestring = trimstring (RT_COMPILER_VERSION);
  if (strcmp(somestring, "unknown"))
    log_key_value (logstate, "Library compiler version", "%s", somestring);
  ncptl_free (somestring);

  somestring = trimstring (RT_COMPOPTS);
  log_key_value (logstate, "Library compiler options", "%s", somestring);
  ncptl_free (somestring);

  somestring = trimstring (RT_LINKOPTS);
  log_key_value (logstate, "Library linker options", "%s", somestring);
  ncptl_free (somestring);

  if (isize==4 && lsize==4 && psize==4)
    compiler_mode = "ILP32";
  else
    if (isize==4 && lsize==8 && psize==8)
      compiler_mode = "LP64";
  log_key_value (logstate, "Library compiler mode", "%s", compiler_mode);
}


/* Return the name of the microsecond timer as a statically allocated
 * string.  If hpet is 1 we attempt to query the HPET device; if hpet
 * is 0 we ignore the HPET device.  This function must be kept current
 * with ncptl_time() and ncptl_time_no_hpet(). */
static char *microsecond_timer_name (int hpet)
{
  static char timer_name[1000]; /* Underlying mechanism used by ncptl_time() */

#ifdef USE_HPET
  if (hpet && ncptl_hpet_works) {
    sprintf (timer_name, "HPET [%s]", HPET_DEVICE);
    return timer_name;
  }
#else
  dummyvar.i = hpet;  /* Convince the compiler that hpet is not an unused parameter. */
#endif

#if NCPTL_TIMER_TYPE == 1
  sprintf (timer_name, "gettimeofday()");
#elif NCPTL_TIMER_TYPE == 2
  sprintf (timer_name, "inline assembly code + gettimeofday()");
#elif NCPTL_TIMER_TYPE == 3
  sprintf (timer_name, "inline assembly code");
#elif NCPTL_TIMER_TYPE == 4
  sprintf (timer_name, "get_cycles()");
#elif NCPTL_TIMER_TYPE == 5
  sprintf (timer_name, "PAPI_get_real_usec()");
#elif NCPTL_TIMER_TYPE == 6
  sprintf (timer_name, "clock_gettime(%s)", CLOCKID_STRING);
#elif NCPTL_TIMER_TYPE == 7
  sprintf (timer_name, "dclock()");
#elif NCPTL_TIMER_TYPE == 8
  sprintf (timer_name, "QueryPerformanceCounter()");
#elif NCPTL_TIMER_TYPE == 9
  sprintf (timer_name, "MPI_Wtime()");
#else
# error Unrecognized microsecond-timer type
#endif
  return timer_name;
}


/* Write to the log file information about the microsecond timer type
 * and quality.  This must be kept current with ncptl_time() and
 * ncptl_time_no_hpet(). */
static void log_write_prologue_timer (NCPTL_LOG_FILE_STATE *logstate)
{
  const char *timer_ovhd = "Average microsecond timer overhead";

  /* Output the type of our microsecond timer. */
  log_key_value (logstate, "Microsecond timer type", "%s", microsecond_timer_name(1));

  /* If we didn't calibrate the timer then we have nothing meaningful
   * to say about it. */
  if (ncptl_fast_init) {
#ifdef HAVE_CYCLES_PER_USEC
    log_printf (logstate, "# WARNING: Timer was not initialized; performance results may be meaningless.\n");
#else
    log_printf (logstate, "# WARNING: Timer quality was not evaluated; performance results have an unknown error component.\n");
#endif
    return;
  }

  /* Output some information about the timer quality. */
  if (ncptl_time_overhead < 1)
    log_key_value (logstate, timer_ovhd, "%s", "<1 microsecond");
  else
    if (ncptl_time_overhead == 1)
      log_key_value (logstate, timer_ovhd, "%s", "1 microsecond");
    else
      log_key_value (logstate, timer_ovhd, "%" PRIu64 " microseconds", ncptl_time_overhead);
  log_key_value (logstate, "Microsecond timer increment",
                 "%.6g +/- %.6g microseconds (ideal: 1 +/- 0)",
                 ncptl_time_delta_mean, ncptl_time_delta_stddev);
  if (ncptl_time_delta_mean >= 2.0)
    log_printf (logstate, "# WARNING: Timer exhibits poor granularity.\n");
  if (ncptl_time_delta_stddev >= 1.0)
    log_printf (logstate, "# WARNING: Timer has a large error component.\n");
  if (clock_wraparound_time()) {
    log_printf (logstate, "# WARNING: Timer wraps around every ");
    log_write_friendly_time (logstate, clock_wraparound_time());
    log_printf (logstate, ".\n");
  }

#ifdef HAVE_NANOSLEEP
  /* Output similar information about the sleep timer. */
  log_key_value (logstate, "Minimum sleep time", "%.6g +/- %.6g microseconds (ideal: 1 +/- 0)",
                 ncptl_sleep_mean, ncptl_sleep_stddev);
  if (ncptl_sleep_mean >= 2.0)
    log_printf (logstate, "# WARNING: Sleeping exhibits poor granularity (not a serious problem).\n");
  if (ncptl_sleep_stddev >= 1.0)
    log_printf (logstate, "# WARNING: Sleeping has a large error component (not a serious problem).\n");
#endif

#ifdef HAVE_GETRUSAGE
  /* Output similar information about resource usage. */
  log_key_value (logstate, "Process CPU timer", "getrusage()");
  log_key_value (logstate, "Process CPU-time increment", "%.6g +/- %.6g microseconds (ideal: 1 +/- 0)",
                 ncptl_proc_time_delta_mean, ncptl_proc_time_delta_stddev);
  if (ncptl_proc_time_delta_mean >= 2.0)
    log_printf (logstate, "# WARNING: Process timer exhibits poor granularity (not a serious problem).\n");
  if (ncptl_proc_time_delta_stddev >= 1.0)
    log_printf (logstate, "# WARNING: Process timer has a large error component (not a serious problem).\n");
#endif
}


/* Write the program's complete argument list to the log file. */
static void log_write_prologue_command_line (NCPTL_LOG_FILE_STATE *logstate,
                                             NCPTL_CMDLINE *arglist,
                                             int numargs)
{
  ncptl_int siglist[NUM_SIGNALS];   /* List of signals to ignore */
  ncptl_int numsigs = 0;            /* Number of entries in the above */
  char *sigstring;                  /* Compacted string version of siglist[] */
  int i;

  /* Output all of the user-defined arguments plus a few automatic ones. */
  for (i=0; i<numargs; i++)
    switch (arglist[i].type) {
      case NCPTL_TYPE_INT:
        log_key_value (logstate, arglist[i].description, "%" PRId64,
                       (int64_t) arglist[i].variable->intval);
        break;

      case NCPTL_TYPE_STRING:
        log_key_value (logstate, arglist[i].description, "%s",
                       arglist[i].variable->stringval);
        break;

      default:
        ncptl_fatal ("Internal error in %s, line %d", __FILE__, __LINE__);
        break;
    }

  /* Handle --no-trap specially. */
  for (i=0; i<NUM_SIGNALS; i++)
    if (ncptl_no_trap_signal[i])
      siglist[numsigs++] = (ncptl_int) i;
  sigstring = numbers_to_ranges (siglist, numsigs);
  log_key_value (logstate, SIGNAL_CMDLINE_DESC, "%s", sigstring);
  ncptl_free (sigstring);
}


/* Write the length of the log-file checkpointing interval. */
static void log_write_prologue_checkpointing (NCPTL_LOG_FILE_STATE *logstate)
{
  const char *key = "Log-file checkpointing interval";

  if (ncptl_log_checkpoint_interval) {
    log_printf (logstate, "# %s: ", key);
    log_write_friendly_time (logstate, ncptl_log_checkpoint_interval/1000000.0);
    log_printf (logstate, "\n");
  }
  else
    log_key_value (logstate, key, "infinite");
}


/* Signal handler for SIGCHLD -- ignore signals triggered by
 * popen()/pclose(). */
static RETSIGTYPE ignore_popen_SIGCHLD (int signalnum)
{
  dummyvar.i = signalnum;  /* Convince the compiler that signalnum is not an unused parameter. */
  return RETSIGVALUE;
}


/* Use an external executable to construct a list of dynamic libraries
 * that the user's executable is linked with. */
static void log_write_prologue_dynamic_libs (NCPTL_LOG_FILE_STATE *logstate)
{
#if defined(HAVE_POPEN) && defined(DYNLIB_CMD_FMT) && defined(DYNLIB_EXT)
  char *dynlib_cmd;        /* External command to execute */
  FILE *dynlib_pipe;       /* Pipe into which the external command writes */
  NCPTL_QUEUE *dynlibQ;    /* Queue of dynamic libraries encountered */
  char **dynlib_list;      /* Flattened version of dynlibQ */
  ncptl_int dynlib_tally;  /* Number of entries in dynlibQ */
  char oneline[NCPTL_MAX_LINE_LEN];   /* One line read from dynlib_pipe */
  char *selfname;          /* Full name of the current executable */
  SIGHANDLER oldsigchld;   /* Previous value of the SIGCHLD signal handler */

  /* popen() uses fork() which may not work properly. */
  if (!ncptl_fork_works)
    return;

  /* Ensure that popen()/pclose() don't trigger a deadly SIGCHLD
   * signal.  Ideally, this should be set to SIG_IGN, but not all
   * operating systems allow SIGCHLD to be set to SIG_IGN. */
  ncptl_install_signal_handler (SIGCHLD, ignore_popen_SIGCHLD, &oldsigchld, 0);

  /* Execute the command described by DYNLIB_CMD_FMT. */
  selfname = fully_expanded_path (ncptl_progname);
  dynlib_cmd =
    (char *) ncptl_malloc (strlen(DYNLIB_CMD_FMT) + strlen(selfname) + 1, 0);
  sprintf (dynlib_cmd, DYNLIB_CMD_FMT, selfname);
  if (!(dynlib_pipe=popen(dynlib_cmd, "r")))
    return;

  /* Read the command's output line-by-line and construct a list of
   * dynamic libraries encountered in it. */
  dynlibQ = ncptl_queue_init (sizeof(char *));
  while (fgets (oneline, NCPTL_MAX_LINE_LEN-1, dynlib_pipe)) {
    char *onetoken;         /* A single token of oneline */
    char *lastlib = NULL;   /* Last library mentioned in oneline */

    for (onetoken=strtok(oneline, " \t\n"); onetoken; onetoken=strtok(NULL, " \t\n"))
      if (strstr (onetoken, DYNLIB_EXT))
        lastlib = onetoken;
    if (lastlib) {
      /* Add the library name to the queue. */
      lastlib = ncptl_strdup(fully_expanded_path(lastlib));
      ncptl_queue_push (dynlibQ, (void *) &lastlib);
    }
  }

  /* Output a list of dynamic libraries. */
  dynlib_tally = ncptl_queue_length (dynlibQ);
  if (dynlib_tally) {
    char dynstring[NCPTL_MAX_LINE_LEN];    /* List of dynamic libraries */
    ncptl_int i;

    dynlib_list = (char **) ncptl_queue_contents (dynlibQ, 0);
    dynstring[0] = '\0';
    for (i=0; i<dynlib_tally; i++) {
      if (i)
        strcat (dynstring, " ");
      strcat (dynstring, dynlib_list[i]);
      ncptl_free ((void *)dynlib_list[i]);
    }
    log_key_value (logstate, "Dynamic libraries used", dynstring);
  }

  /* Clean up before returning. */
  pclose (dynlib_pipe);
  ncptl_queue_empty (dynlibQ);
  ncptl_free (dynlib_cmd);
  ncptl_install_signal_handler (SIGCHLD, oldsigchld, NULL, 0);
#endif
}


/* Given a comment queue and a handle to an open file, read each line
 * of the file into a comment in the comment queue. */
static void log_read_file_into_comments (NCPTL_QUEUE *expanded_comments,
                                         char *keybase,
                                         FILE *commentfile)
{
  LOG_COMMENT *onecomment;  /* Pointer to the end of the expanded_comments queue */
  char oneline[NCPTL_MAX_LINE_LEN+1];   /* One line read from commentfile */
  uint64_t lineno = 0;      /* Current line number */

  while (fgets (oneline, NCPTL_MAX_LINE_LEN, commentfile)) {
    int stringlen = strlen(oneline);

    if (oneline[stringlen-1] == '\n')
      oneline[stringlen-1] = '\0';
    onecomment = (LOG_COMMENT *) ncptl_queue_allocate (expanded_comments);
    if (keybase) {
      onecomment->key = (char *) ncptl_malloc (strlen(keybase) + 30, 0);  /* keybase + ", line " + 64-bit number + NULL */
      sprintf (onecomment->key, "%s, line %" PRIu64, keybase, ++lineno);
    }
    else
      onecomment->key = NULL;
    onecomment->value = ncptl_strdup (oneline);
  }
}


/* If the user or a backend specified additional commentary, output it. */
static void log_write_extra_comments (NCPTL_LOG_FILE_STATE *logstate)
{
  ncptl_int num_comments;  /* # of comments in a queue */
  NCPTL_QUEUE *expanded_comments;  /* extra_log_comments with files inlined */
  LOG_COMMENT *comments;     /* List of comments from a queue */
  ncptl_int user_comment_num = 0;   /* # of user (i.e., NULL-key) comments */
  ncptl_int i;

  /* Exit now if we have no work to do. */
  if (!extra_log_comments ||
      !(num_comments=ncptl_queue_length (extra_log_comments)))
    return;

  /* Expand the comment list into another queue. */
  comments = (LOG_COMMENT *) ncptl_queue_contents (extra_log_comments, 0);
  expanded_comments = ncptl_queue_init (sizeof(LOG_COMMENT));
  for (i=0; i<num_comments; i++)
    switch (comments[i].value[0]) {
      case '@':
        /* @FILE -- use each line of FILE as a separate user comment. */
        {
          FILE *commentfile;    /* File of comment lines */
          char *keystring;      /* "Contents of <filename>" */

          if (!(commentfile=fopen(&comments[i].value[1], "r"))) {
            log_printf (logstate, log_section_separator);
            ncptl_queue_empty (extra_log_comments);  /* Avoid infinite recursion from ncptl_fatal(). */
            ncptl_fatal ("Unable to open comment file \"%s\"", &comments[i].value[1]);
          }
          keystring = (char *) ncptl_malloc (15 + strlen(&comments[i].value[1]), 0);
          sprintf (keystring, "Contents of %s", &comments[i].value[1]);
          log_read_file_into_comments (expanded_comments, keystring, commentfile);
          ncptl_free (keystring);
          fclose (commentfile);
        }
        break;

      case '!':
        /* !COMMAND -- execute COMMAND and use each line of its output
         * as a separate user comment. */
#if defined(HAVE_POPEN) && defined(HAVE_WORKING_FORK)
        if (!ncptl_fork_works) {
          log_printf (logstate, log_section_separator);
          ncptl_queue_empty (extra_log_comments);  /* Avoid infinite recursion from ncptl_fatal(). */
          ncptl_fatal ("Unable to process --comment=\"%s\" without access to a popen() function",
                       comments[i].value);
        }
        else {
          FILE *commentstream;    /* File of comment lines */
          char *keystring;        /* 'Output of "<command>"' */
          int exitstatus;         /* Exit status of child process */

          if (!(commentstream=popen(&comments[i].value[1], "r"))) {
            log_printf (logstate, log_section_separator);
            ncptl_queue_empty (extra_log_comments);  /* Avoid infinite recursion from ncptl_fatal(). */
            ncptl_fatal ("Unable to execute command \"%s\"", &comments[i].value[1]);
          }
          keystring = (char *) ncptl_malloc (15 + strlen(&comments[i].value[1]), 0);
          sprintf (keystring, "Output of \"%s\"", &comments[i].value[1]);
          log_read_file_into_comments (expanded_comments, keystring, commentstream);
          ncptl_free (keystring);
          exitstatus = pclose (commentstream);
          if (!WIFEXITED(exitstatus) || WEXITSTATUS(exitstatus)) {
            log_printf (logstate, log_section_separator);
            ncptl_queue_empty (extra_log_comments);  /* Avoid infinite recursion from ncptl_fatal(). */
            ncptl_fatal ("Command \"%s\" exited abnormally", &comments[i].value[1]);
          }
        }
#else
        log_printf (logstate, log_section_separator);
        ncptl_queue_empty (extra_log_comments);  /* Avoid infinite recursion from ncptl_fatal(). */
        ncptl_fatal ("Unable to process --comment=\"%s\" without access to a popen() function",
                     comments[i].value);
#endif
        break;

      default:
        /* Anything else -- use as a literal user comment. */
        {
          LOG_COMMENT *onecomment = (LOG_COMMENT *) ncptl_queue_allocate (expanded_comments);
          onecomment->key = comments[i].key;
          onecomment->value = comments[i].value;
        }
        break;
    }

  /* Output and deallocate the expanded comment list. */
  num_comments = ncptl_queue_length (expanded_comments);
  comments = (LOG_COMMENT *) ncptl_queue_contents (expanded_comments, 0);
  for (i=0; i<num_comments; i++) {
    if (comments[i].key)
      log_key_value (logstate, comments[i].key, comments[i].value);
    else {
      char keystr[NCPTL_MAX_LINE_LEN];    /* Formatted key string */

      sprintf (keystr, "User comment %" NICS, ++user_comment_num);
      log_key_value (logstate, keystr, comments[i].value);
    }
  }

  /* Clean up. */
  if (!logstate->suppress_emptying) {
    for (i=0; i<num_comments; i++) {
      if (comments[i].key)
        ncptl_free (comments[i].key);
      ncptl_free (comments[i].value);
    }
    ncptl_queue_empty (extra_log_comments);
  }
  ncptl_queue_empty (expanded_comments);
}


/* Write to the log file information about the log creator and
 * creation time. */
static void log_write_prologue_creation (NCPTL_LOG_FILE_STATE *logstate)
{
  uid_t userid;               /* ID of current user */
  struct passwd *userinfo = NULL; /* Other information about the current user */
  char timestr[NCPTL_MAX_LINE_LEN];   /* Output of asctime() without the '\n' */

  /* Output the user's full name, if available.  If not, output the
   * user's username.  If that's not available either, output the
   * user's user ID. */
  userid = getuid();
#ifdef HAVE_GETPWUID
  userinfo = getpwuid (userid);
  if (userinfo)
    if (userinfo->pw_gecos && *userinfo->pw_gecos)
      log_key_value (logstate, "Log creator", "%s", userinfo->pw_gecos);
    else
      if (userinfo->pw_name && *userinfo->pw_name)
        log_key_value (logstate, "Log creator", "%s", userinfo->pw_name);
      else
        log_key_value (logstate, "Log creator", "UID %d", userid);
  else
#endif
    log_key_value (logstate, "Log creator", "UID %d", userid);

  /* Timestamp the log file. */
  logstate->log_creation_time = time (NULL);
  strcpy (timestr, asctime (localtime (&logstate->log_creation_time)));
  timestr[strlen(timestr)-1] = '\0';
  log_key_value (logstate, "Log creation time", "%s", timestr);
#ifdef USE_HPET
  logstate->log_creation_time_hpet = ncptl_time();
  logstate->log_creation_time_no_hpet = ncptl_time_no_hpet();
#endif

  /* Store information we'll need when we close the log file. */
#ifdef HAVE_GETRUSAGE
  logstate->log_creation_process_time_user = ncptl_process_time(0);
  logstate->log_creation_process_time_sys = ncptl_process_time(1);
  ncptl_page_fault_count (&logstate->major_faults, &logstate->minor_faults);
#endif
  logstate->log_creation_interrupt_count = ncptl_interrupt_count();
}


/* Compare two pointers to strings (needed by the qsort() call in
 * log_write_prologue_environment()). */
static int indirect_strcmp (const void *first, const void *second)
{
  return strcmp (*(char **)first, *(char **)second);
}


/* Write the program's complete set of environment variables to the
 * log file. */
static void log_write_prologue_environment (NCPTL_LOG_FILE_STATE *logstate)
{
#ifndef environ
# ifdef HAVE_ENVIRON
  extern char **environ;      /* Array of environment variables. */
# else
  char *environ[] = {NULL};   /* Fabricate an empty environment-variable list. */
# endif
#endif
  int numvars;                /* # of entries in the above */
  char **sortenv;             /* Alphabetically sorted version of environ[] */
  int i;

  /* Sort the environment variables alphabetically. */
  for (sortenv=environ, numvars=0; *sortenv; sortenv++, numvars++)
    ;
  sortenv = (char **) ncptl_malloc ((numvars+1)*sizeof(char *), 0);
  for (i=0; i<numvars; i++) {
    char *c;

    /* Blank out any control characters we find so as not to confuse
     * ncptl-logextract. */
    sortenv[i] = ncptl_strdup (environ[i]);
    for (c=sortenv[i]; *c; c++)
      if (iscntrl((int)*c))
        *c = ' ';
  }
  sortenv[numvars] = NULL;
  qsort (sortenv, numvars, sizeof(char *), indirect_strcmp);

  /* Write the sorted list to the log file. */
  log_printf (logstate, "#\n");
  log_printf (logstate, "# Environment variables\n");
  log_printf (logstate, "# ---------------------\n");
  for (i=0; i<numvars; i++) {
    long keylen;                /* Length of the key (i.e., variable) name */
    char *equalptr;             /* Pointer to the first "=" */
    char keystring[NCPTL_MAX_LINE_LEN];   /* Key name extracting from a key=value string */

    /* It would be exceedingly odd if we didn't find a single "=". */
    if (!(equalptr=strchr(sortenv[i], '=')))
      continue;

    keylen = equalptr - sortenv[i];
    sprintf (keystring, "%*.*s", (int) keylen, (int) keylen, sortenv[i]);
    log_key_value (logstate, keystring, "%s", equalptr+1);
  }

  /* Clean up. */
  for (i=0; i<numvars; i++)
    ncptl_free (sortenv[i]);
  ncptl_free (sortenv);
}


/* Write the program's complete source code to the log file. */
static void log_write_prologue_source (NCPTL_LOG_FILE_STATE *logstate,
                                       char **sourcecode)
{
  if (!sourcecode)
    return;
  log_printf (logstate, "#\n");
  log_printf (logstate, "# coNCePTuaL source code\n");
  log_printf (logstate, "# ----------------------\n");
  while (*sourcecode)
    log_printf (logstate, "#     %s\n", *sourcecode++);
  log_printf (logstate, "#\n");
}


/* Write stock epilogue information to the log file.  The caller is
 * expected to have already written a row of hashes followed by an
 * exit status message and is expected to write another row of hashes
 * after calling log_write_epilogue(). */
static void log_write_epilogue (NCPTL_LOG_FILE_STATE *logstate)
{
  time_t now;                 /* Seconds since the epoch */
#ifdef HAVE_GETRUSAGE
  uint64_t procnow_user;      /* Total user process time used (microseconds) */
  uint64_t procnow_sys;       /* Total system process time used (microseconds) */
  uint64_t new_major_faults;  /* Major page faults since we started the log */
  uint64_t new_minor_faults;  /* Minor page faults since we started the log */
#endif

  /* Output the current time. */
  now = time (NULL);
  log_printf (logstate, "# Log completion time: %s", asctime (localtime (&now)));
  log_printf (logstate, "# Elapsed time: ");
  log_write_friendly_time (logstate, logstate->log_creation_time ? now - logstate->log_creation_time : 0.0);
  log_printf (logstate, "\n");

#ifdef USE_HPET
  /* Warn about discrepancies between HPET and whatever the alternative is. */
  if (logstate->log_creation_time_hpet) {
    uint64_t delta_hpet = ncptl_time() - logstate->log_creation_time_hpet;
    uint64_t delta_no_hpet = ncptl_time_no_hpet() - logstate->log_creation_time_no_hpet;
    double error_pct = ((double)delta_no_hpet-(double)delta_hpet) * 100.0 / delta_hpet;
    const double tolerance = 1.0;       /* Tolerate a 1% error. */

    if (error_pct > tolerance)
      log_printf (logstate, "# WARNING: The %s timer ran %.1f%% faster than the HPET timer.\n",
                  microsecond_timer_name(0), error_pct);
    else if (error_pct < -tolerance)
      log_printf (logstate, "# WARNING: The %s timer ran %.1f%% slower than the HPET timer.\n",
                  microsecond_timer_name(0), -error_pct);
  }
#endif

#ifdef HAVE_GETRUSAGE
  /* Now do the same thing for elapsed process time. */
  procnow_user = ncptl_process_time(0);
  procnow_sys = ncptl_process_time(1);
  log_printf (logstate, "# Process CPU usage (user+system): ");
  log_write_friendly_time (logstate,
                           logstate->log_creation_process_time_user
                           ? (procnow_user - logstate->log_creation_process_time_user) / 1000000.0
                           : 0.0);
  log_printf (logstate, " + ");
  log_write_friendly_time (logstate,
                           logstate->log_creation_process_time_sys
                           ? (procnow_sys - logstate->log_creation_process_time_sys) / 1000000.0
                           : 0.0);
  log_printf (logstate, "\n");

  /* Output new page faults observed since we started the log file. */
  ncptl_page_fault_count(&new_major_faults, &new_minor_faults);
  log_printf (logstate, "# Number of page faults observed: %" PRIu64 " major, %" PRIu64 " minor\n",
              new_major_faults - logstate->major_faults,
              new_minor_faults - logstate->minor_faults);
#endif

  /* Output the number of interrupts seen on all CPUs in the node. */
  if (logstate->log_creation_interrupt_count != (uint64_t)(~0))
    log_printf (logstate, "# Number of interrupts received (all CPUs): %" PRIu64 "\n",
                ncptl_interrupt_count() - logstate->log_creation_interrupt_count);

  /* Output the peak amount of allocated memory held at any given time. */
  log_key_value_SI (logstate, "Peak memory allocation",
                    (double)ncptl_get_peak_memory_usage(),
                    "bytes", "B", 1024.0, "");

  /* Output any extra comments specified by the backend. */
  log_write_extra_comments (logstate);
}


/* Delete the previous checkpoint data from the log file.  This must
 * never be called if we're logging to an internal string. */
static void log_truncate (NCPTL_LOG_FILE_STATE *logstate)
{
  long log_offset;     /* Current byte offset into the log file */
  int fildes;          /* Low-level file descriptor representing the log file */

  log_flush (logstate);
  if ((fildes=fileno(logstate->logfile)) == -1)
    NCPTL_SYSTEM_ERROR ("Unable to determine the log file's file descriptor");
  if ((log_offset=ftell(logstate->logfile)) == -1 && errno)
    NCPTL_SYSTEM_ERROR ("Unable to determine the log-file's current write offset");
  if (ftruncate(fildes, (off_t)log_offset) == -1)
    NCPTL_SYSTEM_ERROR ("Unable to remove old checkpoint state from the log file");
}


/* Given a number and a list of number ranges, return 1 if the number
 * is within the range, 0 otherwise. */
static int log_number_in_range (char *rangelist, ncptl_int number)
{
  char *rangestring;    /* Mutable version of rangelist */
  char *range;          /* A single number or range of numbers */
  ncptl_int i;

  /* Initialize the routine. */
  rangestring = ncptl_strdup (rangelist);
  for (i=(int)strlen(rangestring)-1; i>=0; i--)    /* Allow either spaces or commas. */
    if (rangestring[i] == ' ')
      rangestring[i] = ',';

  /* Loop over all comma-separated values. */
  for (range=strtok (rangestring, ",");
       range;
       range=strtok (NULL, ",")) {
    char *dashptr = strchr (range, '-');  /* Pointer to the first dash */
    ncptl_int firstrange, lastrange;      /* Beginning and ending of range */

    /* Parse the range or individual number. */
    if (dashptr && dashptr!=range) {
      *dashptr = '\0';
      firstrange = strtoll (range, NULL, 10);
      if (errno == ERANGE)
        ncptl_fatal ("Invalid value \"%s\" in log-file range \"%s\"",
                     range, rangelist);
      lastrange = strtoll (dashptr+1, NULL, 10);
      if (errno == ERANGE)
        ncptl_fatal ("Invalid value \"%s\" in log-file range \"%s\"",
                     dashptr+1, rangelist);
    }
    else {
      firstrange = lastrange = strtoll (range, NULL, 10);
      if (errno == ERANGE)
        ncptl_fatal ("Invalid value \"%s\" in log-file range \"%s\"",
                     range, rangelist);
    }
    if (firstrange > lastrange)
      ncptl_fatal ("Log-file range \"%" NICS "-%" NICS "\" needs to be written as \"%" NICS "-%" NICS "\"",
                   firstrange, lastrange, lastrange, firstrange);

    /* See if NUMBER is within the given range. */
    if (firstrange < 0)
      firstrange = -1;
    if (lastrange < 0)
      lastrange = -1;
    for (i=firstrange; i<=lastrange; i++)
      if (i == number) {
        ncptl_free (rangestring);
        return 1;
      }
  }

  /* Finish up cleanly. */
  ncptl_free (rangestring);
  return 0;
}


/* Given a template for the name of a log file, generate an actual
 * filename and return a pointer to a static buffer. */
static char *log_template_to_filename (char *logtemplate, ncptl_int processor)
{
#define MAX_DIGITS_ALLOWED 25    /* Enough digits for a 64-bit number */
  static char logfilename[PATH_MAX_VAR+2*MAX_DIGITS_ALLOWED];   /* Resulting log-file name + two 64-bit overshoots (not guaranteed to be sufficient) */
  ncptl_int run_number = 1;     /* Number that helps make LOGFILENAME unique */

  /* If the NCPTL_LOG_ONLY environment variable is set, log only if
   * we're in one of the given ranges. */
  if (getenv("NCPTL_LOG_ONLY")
      && !log_number_in_range(getenv("NCPTL_LOG_ONLY"), processor))
    return NULL_DEVICE_NAME;

  /* If we were told to log to the null device, the standard output
   * device, or an internal string then we don't need to parse the
   * filename. */
  if (logtemplate[0] == '\0')
    return NULL_DEVICE_NAME;
  if (!strcmp(logtemplate, STANDARD_OUTPUT_NAME)
      || !strcmp(logtemplate, INTERNAL_STRING_NAME))
    return logtemplate;

  /* Copy from LOGTEMPLATE to LOGFILENAME, replacing formals with actuals. */
  while (1) {
    int used_run_number = 0;     /* Flag indicating if RUN_NUMBER was used */
    int used_proc_number = 0;    /* Flag indicating if PROCESSOR was used */
    struct stat logfileinfo;     /* Information returned by stat() */
    char *tp, *lp;               /* Offsets into LOGTEMPLATE and LOGFILENAME */

    /* Generate a candiate LOGFILENAME. */
    for (tp=logtemplate, lp=logfilename; *tp; tp++, lp++) {
      if (lp >= &logfilename[PATH_MAX_VAR-1])
        ncptl_fatal ("Log-file template \"%s\" produced an excessively long filename on processor %" NICS,
                     logtemplate, processor);
      if (*tp == '%')
        switch (*++tp) {
          case '\0':
            /* Nothing after "%" */
            ncptl_fatal ("Missing directive at end of template \"%s\"", logtemplate);
            break;

          case '0':
          case '1':
          case '2':
          case '3':
          case '4':
          case '5':
          case '6':
          case '7':
          case '8':
          case '9':
            /* Field modifiers */
            {
              char *formatstring = (char *) ncptl_malloc (strlen(tp) + strlen(NICS) + 2, 0);
              char *fp;
              int64_t numdigits;   /* # of digits the user requested */

              /* Sanity-check the number of digits. */
              numdigits = strtoll (tp, NULL, 10);
              if (errno==ERANGE || numdigits<1 || numdigits>MAX_DIGITS_ALLOWED)
                ncptl_fatal ("Invalid field width of %" NICS " in \"%s\" -- must be between 1 and %d digits",
                             numdigits, logtemplate, MAX_DIGITS_ALLOWED);

              /* Construct a format string and pass it to sprintf(). */
              strcpy (formatstring, tp-1);
              for (fp=formatstring+1; isdigit((int)*fp); fp++, tp++)
                ;
              switch (*fp) {
                case '\0':
                  /* Nothing after "%" and some digits */
                  ncptl_fatal ("Missing directive at end of template \"%s\"", logtemplate);
                  break;

                case 'p':
                  /* Processor ID */
                  strcpy (fp, NICS);
                  sprintf (lp, formatstring, processor);
                  lp = &logfilename[strlen(logfilename)-1];
                  used_proc_number = 1;
                  break;

                case 'r':
                  /* Run number */
                  strcpy (fp, NICS);
                  sprintf (lp, formatstring, run_number);
                  lp = &logfilename[strlen(logfilename)-1];
                  used_run_number = 1;
                  break;

                default:
                  /* Anything else */
                  ncptl_fatal ("Unknown directive \"%%%c\" in template \"%s\"",
                               *fp, logtemplate);
                  break;
              }
              ncptl_free (formatstring);
            }
            break;

          case '%':
            /* Literal percent sign */
            *lp = '%';
            break;

          case 'p':
            /* Processor ID */
            sprintf (lp, "%" NICS, processor);
            lp = &logfilename[strlen(logfilename)-1];
            used_proc_number = 1;
            break;

          case 'r':
            /* Run number */
            sprintf (lp, "%" NICS, run_number);
            lp = &logfilename[strlen(logfilename)-1];
            used_run_number = 1;
            break;

          default:
            /* Anything else */
            ncptl_fatal ("Unknown directive \"%%%c\" in template \"%s\"",
                         *tp, logtemplate);
            break;

        }
      else
        *lp = *tp;
    }
    *lp = '\0';

    /* Force every task to use a unique filename. */
    if (!used_proc_number)
      ncptl_fatal ("The log-file template must contain a \"%%p\" (for processor number)");

    /* If the template contains "%r" but the filename already exists,
     * we need to try again with a new RUN_NUMBER. */
    if (!used_run_number)
      break;
    if (stat (logfilename, &logfileinfo) == -1) {
      if (errno == ENOENT)
        break;
      else
        NCPTL_SYSTEM_ERROR ("Unable to test the existence of the log file");
    }
    run_number++;
  }

  return logfilename;
#undef MAX_DIGITS_ALLOWED
}


/**********************
 * Exported functions *
 **********************/

/* Open the log file given a filename template and a processor.
 * Return an opaque object that represents all of the log file's
 * state. */
NCPTL_LOG_FILE_STATE *ncptl_log_open (char *logtemplate, ncptl_int processor)
{
  char *logfilename;
  NCPTL_LOG_FILE_STATE *logstate;

  /* Expand the filename template into a full filename. */
  if (!strcmp(logtemplate, "-"))
    logfilename = log_template_to_filename (STANDARD_OUTPUT_NAME, processor);
  else if (!strcmp(logtemplate, "$"))
    logfilename = log_template_to_filename (INTERNAL_STRING_NAME, processor);
  else
    logfilename = log_template_to_filename (logtemplate, processor);

  /* Allocate and initialize the log file's state. */
  logstate =
    (NCPTL_LOG_FILE_STATE *) ncptl_malloc (sizeof(NCPTL_LOG_FILE_STATE),
                                           CPU_MINIMUM_ALIGNMENT_BYTES);
  memset ((void *)logstate, 0, sizeof(NCPTL_LOG_FILE_STATE));

  /* Store the name of this log file. */
  logstate->filename = ncptl_strdup(logfilename);

  /* Store the processor number associated with this log file. */
  logstate->process_rank = processor;

  /* Create a database for log-file comments. */
  logstate->log_database = ncptl_set_init (101, NCPTL_MAX_LINE_LEN, NCPTL_MAX_LINE_LEN);

  /* Initialize the random-number generator needed by find_k_median()
   * and log_random_delay(). */
  ncptl_init_genrand (&logstate->random_state,
                      2000097899 * (1000095893*processor + ncptl_time_of_day()));

  /* If the NCPTL_LOG_DELAY environment variable is set, store the
   * corresponding number of milliseconds (which we convert to
   * microseconds) to spend on each file operation. */
  logstate->log_delay = 0;
  if (!ncptl_envvar_to_uint64 ("NCPTL_LOG_DELAY", &logstate->log_delay))
    ncptl_fatal ("\"%s\" is not a valid number of milliseconds for NCPTL_LOG_DELAY", getenv("NCPTL_LOG_DELAY"));
  logstate->log_delay *= 1000;

  /* Open the log file. */
  if (!strcmp(logfilename, INTERNAL_STRING_NAME)) {
    logstate->log_contents_allocated = LOG_CONTENTS_INCREMENT;
    logstate->log_contents = ncptl_malloc(logstate->log_contents_allocated, 0);
    logstate->log_contents[0] = '\0';
    logstate->log_contents_used = 1;
  }
  else {
    log_random_delay (logstate);
    if (!strcmp(logfilename, STANDARD_OUTPUT_NAME))
      logstate->logfile = stdout;
    else {
      if (!(logstate->logfile=fopen(logfilename, "w+"))) {
#ifdef HAVE_STRERROR
        if (strerror(errno))
          ncptl_fatal ("Failed to open log file \"%s\" (%s)",
                       logfilename, strerror(errno));
        else
#elif HAVE_DECL_SYS_ERRLIST
        if (errno < sys_nerr)
          ncptl_fatal ("Failed to open log file \"%s\" (%s)",
                       logfilename, sys_errlist[errno]);
        else
#endif
          ncptl_fatal ("Failed to open log file \"%s\" (errno=%d)",
                       logfilename, errno);
      }
    }
  }

  /* Disable checkpointing if we're writing to the null device, the
   * standard output device, or an internal string. */
  if (!strcmp(logfilename, NULL_DEVICE_NAME)
      || !strcmp(logfilename, STANDARD_OUTPUT_NAME)
      || !strcmp(logfilename, INTERNAL_STRING_NAME))
    ncptl_log_checkpoint_interval = 0;

  /* Both store and return the newly initialized log-file state. */
  if (!all_log_file_state)
    all_log_file_state = ncptl_queue_init (sizeof(NCPTL_LOG_FILE_STATE *));
  ncptl_queue_push (all_log_file_state, &logstate);
  return logstate;
}


/* Create a UUID to describe program execution.  This should be called
 * once per *program* and the result should be broadcast to all
 * processes before invoking ncptl_log_write_prologue().  The caller
 * can ncptl_free() the result as soon as ncptl_log_write_prologue()
 * returns. */
char *ncptl_log_generate_uuid (void)
{
  char *uuid_string = ncptl_malloc (37, 0);   /* UUID string to return */
#if defined(HAVE_UUID_UUID_H) && defined(HAVE_LIBUUID)
  uuid_t binary_uuid;         /* Internal UUID representation */

  /* Use libuuid to generate a UUID and convert it to a string. */
  uuid_generate (binary_uuid);
  uuid_unparse (binary_uuid, uuid_string);
#else
  /* Generate 128 random bits and format them as a UUID string. */
  RNG_STATE uuid_state;          /* Current state of the RNG */
  uint64_t seed;                 /* Seed for the above */
  uint64_t randnum1, randnum2;   /* UUID expressed as two random numbers */

  /* Initialize the random-number generator. */
  seed = (uint64_t) getpid() * (uint64_t) time (NULL);
  ncptl_init_genrand (&uuid_state, seed);

  /* Create a UUID. */
  randnum1 = ncptl_genrand_int64 (&uuid_state);
  randnum2 = ncptl_genrand_int64 (&uuid_state);
  sprintf (uuid_string, "%08" PRIx64 "-%04" PRIx64 "-%04" PRIx64 "-%04" PRIx64 "-%012" PRIx64,
           (randnum1>>32)&0xFFFFFFFF, (randnum1>>16)&0xFFFF, randnum1&0xFFFF,
           (randnum2>>48)&0xFFFF, randnum2&INT64_C(0xFFFFFFFFFFFF));
#endif

  /* Return the UUID to the caller. */
  return uuid_string;
}


/* Write a stock prologue to the log file. */
void ncptl_log_write_prologue (NCPTL_LOG_FILE_STATE *logstate,
                               char *progname, char *program_uuid,
                               char *backend_name, char *backend_desc,
                               ncptl_int tasks,
                               NCPTL_CMDLINE *arglist, int numargs,
                               char **sourcecode)
{
  /* Write a wealth of information about the coNCePTuaL compiler and
   * host hardware/software to the log file. */
  log_printf (logstate, log_section_separator);
  log_printf (logstate, "# ===================\n");
  log_printf (logstate, "# coNCePTuaL log file\n");
  log_printf (logstate, "# ===================\n");
  log_write_prologue_basic (logstate, progname, program_uuid, backend_name,
                            backend_desc, tasks);
  log_write_prologue_hardware (logstate);
  log_write_prologue_thread_affinity (logstate);
  log_write_prologue_library (logstate);
  log_write_prologue_dynamic_libs (logstate);
  log_write_prologue_timer (logstate);
  log_write_prologue_command_line (logstate, arglist, numargs);
  log_write_prologue_checkpointing (logstate);
  log_write_extra_comments (logstate);
  log_write_prologue_creation (logstate);
  log_write_prologue_environment (logstate);
  log_write_prologue_source (logstate, sourcecode);
  log_printf (logstate, log_section_separator);

  /* If checkpointing is enabled, assume that the process will be
   * killed without our having a chance to clean up. */
  if (ncptl_log_checkpoint_interval) {
    fpos_t log_position;  /* Current (abstract) position in the log file */

    if (fgetpos (logstate->logfile, &log_position) == -1)
      NCPTL_SYSTEM_ERROR ("Unable to determine the current log-file position");
    log_printf (logstate, log_section_separator);
    log_printf (logstate, "# Program aborted with the following error message:\n");
    log_printf (logstate, "#     Received signal 9 (Killed) or system crashed\n");  /* Why else? */
    log_write_epilogue (logstate);
    log_printf (logstate, log_section_separator);
    if (fsetpos (logstate->logfile, &log_position) == -1)
      NCPTL_SYSTEM_ERROR ("Unable to rewind the log file");
  }
  log_flush (logstate);
}


/* Write a stock epilogue to the log file. */
void ncptl_log_write_epilogue (NCPTL_LOG_FILE_STATE *logstate)
{
  log_printf (logstate, log_section_separator);
  log_printf (logstate, "# Program exited normally.\n");
  log_write_epilogue (logstate);
  log_printf (logstate, log_section_separator);
  if (ncptl_log_checkpoint_interval)
    log_truncate (logstate);
}


/* Look up a key in the log-file comment database and return the
 * corresponding value.  Return the empty string if the key is not
 * found in the database.  In either case, the caller should not
 * deallocate the result. */
char *ncptl_log_lookup_string (NCPTL_LOG_FILE_STATE *logstate, char *key)
{
  char keycopy[NCPTL_MAX_LINE_LEN];  /* Padded copy of KEY */
  void *found_value;

  memset (keycopy, 0, NCPTL_MAX_LINE_LEN);
  strcpy (keycopy, key);
  found_value = ncptl_set_find (logstate->log_database, keycopy);
  if (found_value)
    return (char *) found_value;
  else
    return "";
}


/* Log a value to a given column. */
void ncptl_log_write (NCPTL_LOG_FILE_STATE *logstate, int logcolumn,
                      char *description, LOG_AGGREGATE aggregate,
                      double aggregate_param, double value)
{
  LOG_COLUMN *thiscolumn;    /* Cache of the current column */
  int i;

  /* Allocate and initialize more columns if necessary. */
  if (logcolumn >= logstate->log_columns_alloced) {
    /* Double the number of allocated columns. */
    logstate->log_columns_alloced = 2*logstate->log_columns_alloced + 1;
    if (logstate->log_columns_alloced <= logcolumn)
      logstate->log_columns_alloced = logcolumn + 1;
    logstate->logfiledata =
      (LOG_COLUMN *) ncptl_realloc (logstate->logfiledata,
                                    logstate->log_columns_alloced*sizeof(LOG_COLUMN),
                                    0);

    /* Initialize all of the new columns. */
    for (i=logstate->log_columns_used; i<logstate->log_columns_alloced; i++)
      logstate->logfiledata[i].description = NULL;
  }

  /* Initialize column LOGCOLUMN if this is the first access to it.
   * If this is not the first access, ensure that the backend didn't
   * neglect to commit the log between top-level statements. */
  thiscolumn = &logstate->logfiledata[logcolumn];
  if (!thiscolumn->description) {
    thiscolumn->description = ncptl_strdup (description);
    thiscolumn->aggregate = aggregate;
    thiscolumn->aggregate_param = aggregate_param;
    thiscolumn->rawdata = ncptl_queue_init (sizeof(double));
    thiscolumn->finaldata = ncptl_queue_init (sizeof(double));
    if (logcolumn >= logstate->log_columns_used)
      logstate->log_columns_used = logcolumn + 1;
  }
  else
    if (thiscolumn->aggregate != aggregate ||
        thiscolumn->aggregate_param != aggregate_param ||
        strcmp (thiscolumn->description, description))
      ncptl_fatal ("Column information was altered unexpectedly");

  /* Push VALUE onto the raw-data queue. */
  ncptl_queue_push (thiscolumn->rawdata, &value);

  /* Periodically checkpoint the log file. */
  if (ncptl_log_checkpoint_interval
      && ncptl_time()-logstate->last_checkpoint > ncptl_log_checkpoint_interval) {
    fpos_t log_position;  /* Current (abstract) position in the log file */
    double **finaldata_backup;        /* Backup of each set of final data */
    ncptl_int *finaldata_backup_len;  /* Number of elements in each of the above */
    int c;

    /* Back up all of the final data queues. */
    finaldata_backup = (double **) ncptl_malloc (logstate->log_columns_used*sizeof(double *), 0);
    finaldata_backup_len = (ncptl_int *) ncptl_malloc (logstate->log_columns_used*sizeof(ncptl_int), 0);
    for (c=0; c<logstate->log_columns_used; c++)
      if (logstate->logfiledata[c].description) {
        NCPTL_QUEUE *thisqueue = logstate->logfiledata[c].finaldata;

        finaldata_backup_len[c] = ncptl_queue_length (thisqueue);
        finaldata_backup[c] = (double *) ncptl_queue_contents (thisqueue, 1);
      }

    /* Remember our current log state, dump the log, then wind back to
     * where we were. */
    if (fgetpos (logstate->logfile, &log_position) == -1)
      NCPTL_SYSTEM_ERROR ("Unable to determine the current log-file position");
    logstate->suppress_emptying = 1;
    ncptl_log_commit_data (logstate);
    log_printf (logstate, log_section_separator);
    log_printf (logstate, "# Program aborted with the following error message:\n");
    log_printf (logstate, "#     Received signal 9 (Killed) or system crashed\n");  /* Why else? */
    log_write_epilogue (logstate);
    log_printf (logstate, log_section_separator);
    log_truncate (logstate);
    logstate->suppress_emptying = 0;
    if (fsetpos (logstate->logfile, &log_position) == -1)
      NCPTL_SYSTEM_ERROR ("Unable to rewind the log file");

    /* Restore all of the final data queues to their previous contents. */
    for (c=0; c<logstate->log_columns_used; c++)
      if (logstate->logfiledata[c].description) {
        NCPTL_QUEUE *targetqueue = logstate->logfiledata[c].finaldata;

        ncptl_queue_empty (targetqueue);
        for (i=0; i<finaldata_backup_len[c]; i++)
          ncptl_queue_push (targetqueue, (void *) &finaldata_backup[c][i]);
        ncptl_free (finaldata_backup[c]);
      }
    ncptl_free (finaldata_backup_len);
    ncptl_free (finaldata_backup);
    logstate->last_checkpoint = ncptl_time();
  }
}


/* Compute the values of all aggregate functions. */
void ncptl_log_compute_aggregates (NCPTL_LOG_FILE_STATE *logstate)
{
  double *rawdata;          /* One column's worth of raw data */
  ncptl_int rawdatalen;     /* Number of entries in RAWDATA */
  NCPTL_QUEUE *finaldataQ;  /* Queue of aggregated data */
  double aggregate;         /* Aggregated value */
  int c, i;

  for (c=0; c<logstate->log_columns_used; c++) {
    /* Skip nonexistent and dataless columns. */
    if (!logstate->logfiledata[c].description)
      continue;
    rawdatalen = ncptl_queue_length (logstate->logfiledata[c].rawdata);
    if (!rawdatalen)
      continue;

    /* Compute the appropriate aggregate function on the column. */
    rawdata = (double *) ncptl_queue_contents (logstate->logfiledata[c].rawdata, 0);
    finaldataQ = logstate->logfiledata[c].finaldata;
    switch (logstate->logfiledata[c].aggregate) {
      case NCPTL_FUNC_NO_AGGREGATE:
        for (i=0; i<rawdatalen; i++)
          ncptl_queue_push (finaldataQ, &rawdata[i]);
        break;

      case NCPTL_FUNC_HISTOGRAM:
        produce_histogram (rawdata, rawdatalen, finaldataQ);
        break;

      /* All of the other aggregate functions produce a single value. */
      default:
        switch (logstate->logfiledata[c].aggregate) {
          case NCPTL_FUNC_MEAN:
            aggregate = find_mean (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_HARMONIC_MEAN:
            aggregate = find_harmonic_mean (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_GEOMETRIC_MEAN:
            aggregate = find_geometric_mean (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_MEDIAN:
            aggregate = find_median (logstate, rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_MAD:
            aggregate = find_mad (logstate, rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_STDEV:
            aggregate = find_std_dev (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_VARIANCE:
            aggregate = find_variance (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_SUM:
            aggregate = find_sum (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_MINIMUM:
            aggregate = find_minimum (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_MAXIMUM:
            aggregate = find_maximum (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_FINAL:
            aggregate = find_final (rawdata, rawdatalen);
            break;

          case NCPTL_FUNC_PERCENTILE:
            aggregate = find_percentile (logstate, rawdata, rawdatalen,
                                         logstate->logfiledata[c].aggregate_param);
            break;

          case NCPTL_FUNC_ONLY:
            aggregate = find_only (rawdata, rawdatalen);
            break;

          default:
            ncptl_fatal ("Internal error at %s, line %d", __FILE__, __LINE__);
            break;
        }
        ncptl_queue_push (finaldataQ, &aggregate);
        break;
    }

    /* Empty the raw-data queue. */
    if (!logstate->suppress_emptying)
      ncptl_queue_empty (logstate->logfiledata[c].rawdata);
  }
}


/* Complete the current table and begin a new one.  Backends should
 * insert a call to ncptl_log_commit_data() between top-level complex
 * statements. */
void ncptl_log_commit_data (NCPTL_LOG_FILE_STATE *logstate)
{
  char *description;  /* Textual description of a single column */
  char *src, *dest;   /* Indexes into the source and target description strings */
  ncptl_int maxrows = 0;  /* Maximum number of rows in any column */
  static int within_commit_data = 0;   /* 1=currently within ncptl_commit_data() */
  ncptl_int c, r;

  /* Ignore completely empty tables. */
  for (c=0; c<logstate->log_columns_used; c++)
    if (logstate->logfiledata[c].description)
      break;
  if (c >= logstate->log_columns_used)
    return;

  /* Avoid recursive invocations, such as ncptl_commit_data() -->
   * ncptl_fatal() --> ncptl_commit_data(). */
  if (within_commit_data)
    return;
  within_commit_data = 1;

  /* Conditionally output an empty row before the table. */
  if (logstate->log_need_newline)
    log_putc (logstate, '\n');
  else
    if (!logstate->suppress_emptying)
      logstate->log_need_newline = 1;

  /* Write the first header row. */
  for (c=0; c<logstate->log_columns_used; c++) {
    /* Skip empty columns. */
    if (!logstate->logfiledata[c].description)
      continue;

    /* Clean up the column description.  "Clean up" currently means to
     * escape backslashes and double quotes. */
    description = (char *) ncptl_malloc (2*(strlen(logstate->logfiledata[c].description)+1), 0);
    for (src=logstate->logfiledata[c].description, dest=description;
         *src;
         src++, dest++)
      switch (*src) {
        case '\\':
          *dest++ = *src;
          *dest = *src;
          break;

        case '"':
          *dest++ = '\\';
          *dest = *src;
          break;

        default:
          *dest = *src;
          break;
      }
    *dest = '\0';

    /* Output the cleaned-up description. */
    log_printf (logstate, "\"%s\"", description);
    if (logstate->logfiledata[c].aggregate == NCPTL_FUNC_HISTOGRAM) {
      log_putc (logstate, ',');
      log_printf (logstate, "\"%s\"", description);
    }
    log_putc (logstate, c==logstate->log_columns_used-1 ? '\n' : ',');
    ncptl_free (description);
  }

  /* Write the second header row. */
  for (c=0; c<logstate->log_columns_used; c++) {
    /* Skip empty columns. */
    if (!logstate->logfiledata[c].description)
      continue;

    /* Output a string describing the aggregate function. */
    log_putc (logstate, '"');
    switch (logstate->logfiledata[c].aggregate) {
      case NCPTL_FUNC_NO_AGGREGATE:
        log_printf (logstate, "(all data)");
        break;

      case NCPTL_FUNC_MEAN:
        log_printf (logstate, "(mean)");
        break;

      case NCPTL_FUNC_HARMONIC_MEAN:
        log_printf (logstate, "(harm. mean)");
        break;

      case NCPTL_FUNC_GEOMETRIC_MEAN:
        log_printf (logstate, "(geom. mean)");
        break;

      case NCPTL_FUNC_MEDIAN:
        log_printf (logstate, "(median)");
        break;

      case NCPTL_FUNC_MAD:
        log_printf (logstate, "(med. abs. dev.)");
        break;

      case NCPTL_FUNC_STDEV:
        log_printf (logstate, "(std. dev.)");
        break;

      case NCPTL_FUNC_VARIANCE:
        log_printf (logstate, "(variance)");
        break;

      case NCPTL_FUNC_SUM:
        log_printf (logstate, "(sum)");
        break;

      case NCPTL_FUNC_MINIMUM:
        log_printf (logstate, "(minimum)");
        break;

      case NCPTL_FUNC_MAXIMUM:
        log_printf (logstate, "(maximum)");
        break;

      case NCPTL_FUNC_FINAL:
        log_printf (logstate, "(final)");
        break;

      case NCPTL_FUNC_ONLY:
        log_printf (logstate, "(only value)");
        break;

      case NCPTL_FUNC_HISTOGRAM:
        log_printf (logstate, "(hist. values)\",\"(hist. tallies)");
        break;

      case NCPTL_FUNC_PERCENTILE:
        {
          char pctstr[25];
          const char *ordstr;
          sprintf(pctstr, "%.0f", logstate->logfiledata[c].aggregate_param);
          switch (pctstr[strlen(pctstr)-1]) {
            case 1:
              ordstr = "st";
              break;

            case 2:
              ordstr = "nd";
              break;

            case 3:
              ordstr = "rd";
              break;

            default:
              ordstr = "th";
              break;
          }
          log_printf (logstate, "(%s%s percentile)", pctstr, ordstr);
        }
        break;

      default:
        ncptl_fatal ("Internal error at %s, line %d", __FILE__, __LINE__);
        break;
    }
    log_putc (logstate, '"');
    log_putc (logstate, c==logstate->log_columns_used-1 ? '\n' : ',');
  }

  /* Determine the maximum number of rows of any column. */
  ncptl_log_compute_aggregates (logstate);
  for (c=0; c<logstate->log_columns_used; c++) {
    ncptl_int numrows;    /* Number of rows in the current column */

    /* Skip empty columns. */
    if (!logstate->logfiledata[c].description)
      continue;

    /* Take the maximum across all of the queue lengths. */
    numrows = ncptl_queue_length (logstate->logfiledata[c].finaldata);
    if (logstate->logfiledata[c].aggregate == NCPTL_FUNC_HISTOGRAM)
      numrows /= 2;              /* Stored as {value, tally} pairs */
    if (maxrows < numrows)
      maxrows = numrows;
  }

  /* Output the data one row at a time. */
  for (r=0; r<maxrows; r++) {
    for (c=0; c<logstate->log_columns_used; c++) {
      double *coldata;         /* All data in the current column */

      /* Skip empty columns. */
      if (!logstate->logfiledata[c].description)
        continue;

      /* Output the data at the current row and column. */
      coldata = (double *) ncptl_queue_contents (logstate->logfiledata[c].finaldata, 0);
      if (logstate->logfiledata[c].aggregate == NCPTL_FUNC_HISTOGRAM) {
        if (r < ncptl_queue_length(logstate->logfiledata[c].finaldata) / 2)
          log_printf (logstate, "%.*g,%.*g",
                   log_data_digits, coldata[r*2],
                   log_data_digits, coldata[r*2+1]);
        else
          log_printf (logstate, ",");
      }
      else
        if (r < ncptl_queue_length (logstate->logfiledata[c].finaldata))
          log_printf (logstate, "%.*g",
                   log_data_digits, coldata[r]);
      log_putc (logstate, c==logstate->log_columns_used-1 ? '\n' : ',');
    }
  }

  /* Empty the in-memory log. */
  if (!logstate->suppress_emptying) {
    for (c=0; c<logstate->log_columns_used; c++)
      if (logstate->logfiledata[c].description) {
        ncptl_queue_empty (logstate->logfiledata[c].finaldata);
        ncptl_free (logstate->logfiledata[c].description);
        logstate->logfiledata[c].description = NULL;
      }
    logstate->log_columns_used = 0;
  }

  /* While we're at it, let's flush the log to disk in case our job is
   * killed before ncptl_log_commit_data() is called again. */
  log_flush (logstate);

  /* Re-enable calls to ncptl_commit_data(). */
  within_commit_data = 0;
}


/* Add a special-purpose key:value pair as a log-file comment.  If key
 * is NULL, it will be replaced by "User comment #<something>".  This
 * function ncptl_strdup()s its arguments so it's permissible to pass
 * it local variables. */
void ncptl_log_add_comment (const char *key, const char *value)
{
  LOG_COMMENT *comment;    /* Pointer to the end of the comment queue */
  char *valuecopy;         /* Copy of VALUE */
  char *valueline;         /* Pointer to a one-line substring of VALUECOPY */

  /* Automatically create a queue the first time we're called. */
  if (!extra_log_comments)
    extra_log_comments = ncptl_queue_init (sizeof(LOG_COMMENT));

  /* Iterate over each embedded newline-termined substring of VALUE. */
  if (!value)
    ncptl_fatal ("Values passed to ncptl_log_add_comment() may not be NULL");
  valuecopy = ncptl_strdup (value);
  for (valueline=strtok(valuecopy, "\r\n"); valueline; valueline=strtok(NULL, "\r\n")) {
    /* Push key and value onto the end of the queue. */
    comment = (LOG_COMMENT *) ncptl_queue_allocate (extra_log_comments);
    if (key) {
      if (strchr (key, ':'))
        ncptl_fatal ("Keys passed to ncptl_log_add_comment() may not contain colons");
      comment->key = ncptl_strdup (key);
    }
    else
      comment->key = NULL;
    comment->value = ncptl_strdup (valueline);
  }
  ncptl_free (valuecopy);
}


/* Return the current contents of the log file as a string.  The
 * caller must not modify the string, free the string, or hold onto
 * the string past the next call that modifies the log file.  If the
 * log file contents were not maintained (because the log file is the
 * standard-output or null device), return NULL. */
const char *ncptl_log_get_contents (NCPTL_LOG_FILE_STATE *logstate)
{
  if (logstate->logfile
      && strcmp(logstate->filename, STANDARD_OUTPUT_NAME)
      && strcmp(logstate->filename, NULL_DEVICE_NAME)) {
    /* File */
    long log_offset;     /* Current byte offset into the log file */
    int fildes;          /* Low-level file descriptor representing the log file */

    /* Allocate enough memory to hold the log file's entire contents,
     * rewind the file pointer to the beginning, read the entire file,
     * and restore the file pointer. */
    if ((fildes=fileno(logstate->logfile)) == -1)
      NCPTL_SYSTEM_ERROR ("Unable to determine the log file's file descriptor");
    if ((log_offset=ftell(logstate->logfile)) == -1 && errno)
      NCPTL_SYSTEM_ERROR ("Unable to determine the log-file's current write offset");
    logstate->log_contents = ncptl_realloc(logstate->log_contents, log_offset, 0);
    if (fseek(logstate->logfile, 0L, SEEK_SET) == -1 && errno)
      NCPTL_SYSTEM_ERROR ("Failed to rewind the log-file pointer");
    if (fread(logstate->log_contents, 1, (size_t)log_offset, logstate->logfile) != (size_t)log_offset)
      NCPTL_SYSTEM_ERROR ("Failed to read the log file's complete contents");
    if (fseek(logstate->logfile, 0L, SEEK_END) == -1 && errno)
      NCPTL_SYSTEM_ERROR ("Failed to set the log-file pointer");
  }

  /* File or string */
  return logstate->log_contents;
}


/* Flush and close the log file and free most of the memory used to
 * store the log file's state.  We can't free logstate itself because
 * we don't know if ncptl_log_shutdown() will try to access it. */
void ncptl_log_close (NCPTL_LOG_FILE_STATE *logstate)
{
  ncptl_int c;

  /* Write the log to disk. */
  ncptl_log_commit_data (logstate);
  if (logstate->logfile && logstate->logfile != stdout)
    fclose (logstate->logfile);
  logstate->logfile = NULL;

  /* Free all of the memory we had previously allocated then zero out
   * all of the state. */
  for (c=0; c<logstate->log_columns_alloced; c++)
    if (logstate->logfiledata[c].description)
      ncptl_free (logstate->logfiledata[c].description);
  ncptl_free (logstate->logfiledata);
  ncptl_set_empty (logstate->log_database);
  ncptl_free (logstate->log_database);
  if (logstate->log_contents)
    ncptl_free (logstate->log_contents);
  ncptl_free (logstate->filename);
  memset ((void *)logstate, 0, sizeof(NCPTL_LOG_FILE_STATE));
}


/* Shut down all log files with an abnormal-termination message. */
void ncptl_log_shutdown (const char *format, va_list args)
{
  NCPTL_LOG_FILE_STATE **logstate_list;   /* List of all values returned by ncptl_log_open() */
  ncptl_int numstates;                    /* Number of entries in the above */
  static int within_log_shutdown = 0;     /* 0=currently within ncptl_log_shutdown() */
  ncptl_int i;

  /* Return if we never opened a log file. */
  if (!all_log_file_state)
    return;

  /* Avoid recursive invocations, such as ncptl_log_shutdown() -->
   * ncptl_fatal() --> ncptl_log_shutdown(). */
  if (within_log_shutdown)
    return;
  within_log_shutdown = 1;

  /* For each open log file, write the error message to the log file. */
  numstates = ncptl_queue_length (all_log_file_state);
  logstate_list = (NCPTL_LOG_FILE_STATE **) ncptl_queue_contents (all_log_file_state, 0);
  for (i=0; i<numstates; i++) {
    NCPTL_LOG_FILE_STATE *logstate = logstate_list[i];

    if (!logstate->logfile)
      continue;
    ncptl_log_commit_data (logstate);
    log_printf (logstate, log_section_separator);
    log_printf (logstate, "# Program aborted with the following error message:\n");
    log_printf (logstate, "#     ");
    vfprintf (logstate->logfile, format, args);
    va_end (args);
    log_printf (logstate, "\n");
    log_write_epilogue (logstate);
    log_printf (logstate, log_section_separator);
    if (ncptl_log_checkpoint_interval)
      log_truncate (logstate);

    /* Close the log file cleanly. */
    fclose (logstate->logfile);
    logstate->logfile = NULL;
  }

  /* Re-enable calls to ncptl_log_shutdown(). */
  within_log_shutdown = 0;
}


/* Store the name of the dynamic linker in the library's .interp section. */
#if defined(CAN_WRITE_INTERP) && defined(DYNAMIC_LINKER)
const char ncptl_dynamic_linker[] __attribute__((section(".interp"))) = DYNAMIC_LINKER;
#endif


/* Output a dataless log file to standard output.  This function is
 * intended to serve as the main() function when executing the shared
 * library (on systems that support that). */
void ncptl_log_output_dataless_log (void)
{
  char *libname = "N/A";
  NCPTL_LOG_FILE_STATE *logstate;
  char *log_uuid;

  ncptl_init (NCPTL_RUN_TIME_VERSION, libname);
  logstate = ncptl_log_open ("-", 0);
  log_uuid = ncptl_log_generate_uuid();
  ncptl_log_write_prologue (logstate, libname, log_uuid, "N/A", "N/A", 1, NULL, 0, NULL);
  ncptl_free (log_uuid);
  ncptl_log_write_epilogue (logstate);
  ncptl_log_close (logstate);
  ncptl_finalize();

  exit (EXIT_SUCCESS);
}
