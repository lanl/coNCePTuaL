/* ----------------------------------------------------------------------
 *
 * Header file to be used by all run-time-library and user-function
 * test cases
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2015, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2015).  Los Alamos National Security, LLC.  This software
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

#ifndef _NCPTL_TEST_H_
#define _NCPTL_TEST_H_

#include "../config.h"
#include "../ncptl.h"


/* MinGW (on Microsoft Windows) lacks a sleep() function. */
#ifndef HAVE_SLEEP
# ifdef _WIN32
#  define sleep(S) Sleep(1000*(S))
# else
#  error Unable to continue without a sleep() function
# endif
#endif


/* Define debug_printf() as a simple printf().  Previous versions of
 * this file had debug_printf() either call printf() or do nothing,
 * based on the contents of the DEBUG environment variable.  However,
 * now that Automake's test framework obliviously redirects standard
 * output to a file there's no longer a need to suppress status
 * messages to reduce clutter. */
#define debug_printf printf


/* Define macros to return success, failure, or inapplicability. */
#define RETURN_SUCCESS() do {                                   \
  debug_printf ("\t\tTEST PASSED.\n");                          \
  return 0;                                                     \
} while (0)
#define RETURN_FAILURE() do {                                   \
  debug_printf ("\t\tTEST FAILED.\n");                          \
  return 1;                                                     \
} while (0)
#define RETURN_NOTAPPLICABLE() do {                             \
  debug_printf ("\t\tTEST CANNOT RUN ON THIS PLATFORM.\n");     \
  return 77;                                                    \
} while (0)

#endif
