/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_random_task() works properly
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2009, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2009).  Los Alamos National Security, LLC.  This software
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

#include "ncptl_test.h"

#define RANGE 5
#define TRIALS (RANGE*1000)


#define SHOW_ATTEMPT(L, H, E)                                           \
  debug_printf ("\t   Trying ncptl_random_task (%2" NICS ", %2" NICS    \
                ", %2" NICS ") ...\n",                                  \
                L, H, E)

#define SHOW_PROBLEM(L, H, E, R, RC)                                    \
  debug_printf ("\t   ncptl_random_task (%" NICS ", %" NICS ", %" NICS  \
                ") --> %" NICS "  [expected %" NICS "]\n",              \
                L, H, E, R, (ncptl_int)RC)

#define SHOW_PROBLEM_2(L, H, E, R, RL, RH)                               \
  debug_printf ("\t   ncptl_random_task (%" NICS ", %" NICS ", %" NICS   \
                ") --> %" NICS                                           \
                "  [expected a value from %" NICS " to %" NICS "]\n",    \
                L, H, E, R, (ncptl_int)RL, (ncptl_int)RH)

int main (void)
{
  int seed;                   /* Random-number seed */
  ncptl_int randnum;          /* Generated pseudorandom number */
  ncptl_int lo, hi, excl=-1;  /* Lower bound, upper bound, number to exclude */
  int randset[RANGE+1];       /* 1=seen given value; 0=not seen */
  int i;

  /* Initialize the random-number generator. */
  debug_printf ("\tSeeding the random-number generator ...\n");
  seed = ncptl_seed_random_task (0, 0);
  debug_printf ("\t   ncptl_seed_random_task(0) --> %d\n", seed);

  /* Test the lower bound being greated than the upper bound (should
   * return -1). */
  debug_printf ("\tTesting misordered lower and upper bounds ...\n");
  for (lo=-RANGE; lo<=RANGE; lo++)
    for (hi=-RANGE; hi<lo; hi++) {
      for (excl=-RANGE; excl<=RANGE; excl++) {
        SHOW_ATTEMPT (lo, hi, excl);
        randnum = ncptl_random_task (lo, hi, excl);
        if (randnum != -1) {
          SHOW_PROBLEM (lo, hi, excl, randnum, -1);
          RETURN_FAILURE();
        }
      }
    }

  /* Test excluding the only number (should return -1). */
  debug_printf ("\tTesting excluding the only number in range ...\n");
  for (lo=-RANGE; lo<=RANGE; lo++) {
    SHOW_ATTEMPT (lo, lo, lo);
    randnum = ncptl_random_task (lo, lo, lo);
    if (randnum != -1) {
      SHOW_PROBLEM (lo, lo, lo, randnum, -1);
      RETURN_FAILURE();
    }
  }

  /* Test excluding an out-of-bounds number. */
  debug_printf ("\tTesting excluding an out-of-bounds number ...\n");
  for (i=0; i<=RANGE; i++)
    randset[i] = 0;
  for (lo=0; lo<=RANGE; lo++)
    for (hi=lo; hi<=RANGE; hi++) {
      for (excl=-RANGE; excl<=RANGE; excl++) {
        if (excl>=lo && excl<=hi)
          continue;
        SHOW_ATTEMPT (lo, hi, excl);
        for (i=0; i<TRIALS; i++) {
          randnum = ncptl_random_task (lo, hi, excl);
          if (randnum<lo || randnum>hi) {
            SHOW_PROBLEM_2 (lo, hi, excl, randnum, lo, hi);
            RETURN_FAILURE();
          }
          randset[randnum]++;
        }
      }
    }
  for (i=0; i<=RANGE; i++)
    if (!randset[i]) {
      debug_printf ("\t   ncptl_random_task (%" NICS ", %" NICS ", %" NICS
                    ") returned no  %" NICS "s in %" NICS " trials\n",
                    lo, hi, excl, (ncptl_int)i, (ncptl_int)TRIALS);
      RETURN_FAILURE();
    }

  /* Test excluding an in-bounds number. */
  debug_printf ("\tTesting excluding an in-bounds number ...\n");
  for (lo=0; lo<RANGE; lo++)
    for (hi=lo+1; hi<=RANGE; hi++) {
      for (excl=lo; excl<=hi; excl++) {
        SHOW_ATTEMPT (lo, hi, excl);
        for (i=0; i<=RANGE; i++)
          randset[i] = 0;
        for (i=0; i<TRIALS; i++) {
          randnum = ncptl_random_task (lo, hi, excl);
          if (randnum<lo || randnum>hi) {
            SHOW_PROBLEM_2 (lo, hi, excl, randnum, lo, hi);
            RETURN_FAILURE();
          }
          randset[randnum]++;
        }
        for (i=lo; i<=hi; i++)
          if (!randset[i] && i!=excl) {
            debug_printf ("\t   ncptl_random_task (%" NICS ", %" NICS ", %" NICS
                          ") returned no %" NICS "s in %" NICS " trials\n",
                          lo, hi, excl, (ncptl_int)i, (ncptl_int)TRIALS);
            RETURN_FAILURE();
          }
          if (randset[i] && i==excl) {
            debug_printf ("\t   ncptl_random_task (%" NICS ", %" NICS ", %" NICS
                          ") returned %" NICS " %" NICS "s in %" NICS " trials\n",
                          lo, hi, excl,
                          (ncptl_int)randset[i], (ncptl_int)i, (ncptl_int)TRIALS);
            RETURN_FAILURE();
          }
      }
    }

  RETURN_SUCCESS();
}
