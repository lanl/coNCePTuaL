/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_func_factor10() and ncptl_dfunc_factor10() work
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

#define BIGNUM 100000        /* Maximum value to test */
#define RNG_SEED 23456789    /* Seed for the random-number generator */

int main (void)
{
  ncptl_int i;

  /* Test ncptl_func_factor10() on positive and negative integers. */
  debug_printf ("\tTesting ncptl_func_factor10() ...\n");
  for (i=-BIGNUM; i<BIGNUM; i++) {
    ncptl_int result = ncptl_func_factor10(i); /* Actual result */
    ncptl_int pos_result;                      /* Positive version of result */
    ncptl_int correct_result;                  /* Expected result */

    /* Compute the expected result. */
    pos_result = result<0 ? -result : result;
    if (pos_result < 10)
      correct_result = result;
    else if (pos_result < 100)
      correct_result = (result/10)*10;
    else if (pos_result < 1000)
      correct_result = (result/100)*100;
    else if (pos_result < 10000)
      correct_result = (result/1000)*1000;
    else if (pos_result < 100000)
      correct_result = (result/10000)*10000;
    else if (pos_result < 1000000)
      correct_result = (result/100000)*100000;
    else if (pos_result < 10000000)
      correct_result = (result/1000000)*1000000;
    else {
      debug_printf ("\t   internal error at %s, line %d\n", __FILE__, __LINE__);
      RETURN_FAILURE();
    }

    /* Complain if we observed a mismatch. */
    if (result != correct_result) {
      debug_printf ("\t   ncptl_func_factor10(%" NICS ") --> %" NICS "  [should be %" NICS "]\n",
		    i, result, correct_result);
      RETURN_FAILURE();
    }
  }

  /* Test ncptl_dfunc_factor10() on positive and negative integers. */
  debug_printf ("\tTesting ncptl_dfunc_factor10() ...\n");
  for (i=-BIGNUM; i<BIGNUM; i++) {
    double result = ncptl_dfunc_factor10((double)i);  /* Actual result */
    double pos_result;                       /* Positive version of result */
    double correct_result;                   /* Expected result */

    /* Compute the expected result. */
    pos_result = result<0.0 ? -result : result;
    if (pos_result < 10.0)
      correct_result = result;
    else if (pos_result < 100.0)
      correct_result = floor(result/10.0)*10.0;
    else if (pos_result < 1000.0)
      correct_result = floor(result/100.0)*100.0;
    else if (pos_result < 10000.0)
      correct_result = floor(result/1000.0)*1000.0;
    else if (pos_result < 100000.0)
      correct_result = floor(result/10000.0)*10000.0;
    else if (pos_result < 1000000.0)
      correct_result = floor(result/100000.0)*100000.0;
    else if (pos_result < 10000000.0)
      correct_result = floor(result/1000000.0)*1000000.0;
    else {
      debug_printf ("\t   internal error at %s, line %d\n", __FILE__, __LINE__);
      RETURN_FAILURE();
    }

    /* Complain if we observed a mismatch. */
    if (result != correct_result) {
      debug_printf ("\t   ncptl_dfunc_factor10(%.10g) --> %.10g  [should be %.10g]\n",
		    (double)i, result, correct_result);
      RETURN_FAILURE();
    }
  }

  /* Test ncptl_dfunc_factor10() on positive and negative fractions. */
  ncptl_seed_random_task (RNG_SEED, (ncptl_int)0);
  for (i=-BIGNUM; i<BIGNUM; i++) {
    double value = ncptl_dfunc_random_uniform ((double)-BIGNUM, (double)BIGNUM);
    double result = ncptl_dfunc_factor10((double)value);  /* Actual result */

    /* Ensure the magnitude of the result is within reasonable bounds. */
    if (ncptl_dfunc_abs(result) > ncptl_dfunc_abs(value)) {
      debug_printf ("\t   ncptl_dfunc_factor10(%.10g) --> %.10g  [too large in magnitude]\n",
		    value, result);
      RETURN_FAILURE();
    }
    if (ncptl_dfunc_abs(result)*10.0 < ncptl_dfunc_abs(value)) {
      debug_printf ("\t   ncptl_dfunc_factor10(%.10g) --> %.10g  [too small in magnitude]\n",
		    value, result);
      RETURN_FAILURE();
    }
  }

  RETURN_SUCCESS();
}
