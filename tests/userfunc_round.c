/* ----------------------------------------------------------------------
 *
 * Ensure that ncptl_dfunc_floor(), ncptl_dfunc_ceiling() and
 * ncptl_dfunc_round() all work
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

#include "ncptl_test.h"

int main (void)
{
  typedef struct {         /* Input and correct results */
    double input;
    double floored;
    double ceilinged;
    double rounded;
  } RESULT;
  RESULT resultlist[] = {
    /* Positive numbers */
    {123.0, 123.0, 123.0, 123.0},
    {123.1, 123.0, 124.0, 123.0},
    {123.2, 123.0, 124.0, 123.0},
    {123.3, 123.0, 124.0, 123.0},
    {123.4, 123.0, 124.0, 123.0},
    /* {123.5, 123.0, 124.0, 124.0}, */
    {123.6, 123.0, 124.0, 124.0},
    {123.7, 123.0, 124.0, 124.0},
    {123.8, 123.0, 124.0, 124.0},
    {123.9, 123.0, 124.0, 124.0},
    {124.0, 124.0, 124.0, 124.0},

    /* Zero */
    {0, 0, 0, 0},

    /* Negative numbers */
    {-124.0, -124.0, -124.0, -124.0},
    {-123.9, -124.0, -123.0, -124.0},
    {-123.8, -124.0, -123.0, -124.0},
    {-123.7, -124.0, -123.0, -124.0},
    {-123.6, -124.0, -123.0, -124.0},
    /* {-123.5, -124.0, -123.0, -124.0}, */
    {-123.4, -124.0, -123.0, -123.0},
    {-123.3, -124.0, -123.0, -123.0},
    {-123.2, -124.0, -123.0, -123.0},
    {-123.1, -124.0, -123.0, -123.0},
    {-123.0, -123.0, -123.0, -123.0}
  };
  unsigned int i, j;
  char *testname[] = {"floor", "ceiling", "round"};

  for (j=0; j<3; j++) {
    if (j)
      debug_printf ("\n");
    debug_printf ("\tTesting ncptl_dfunc_%s() ...\n", testname[j]);
    for (i=0; i<sizeof(resultlist)/sizeof(RESULT); i++) {
      double correct;     /* Correct function result */
      double actual;      /* Actual function result */

      switch (j) {
        case 0:
          correct = resultlist[i].floored;
          actual = ncptl_dfunc_floor(resultlist[i].input);
          break;

        case 1:
          correct = resultlist[i].ceilinged;
          actual = ncptl_dfunc_ceiling(resultlist[i].input);
          break;

        case 2:
          correct = resultlist[i].rounded;
          actual = ncptl_dfunc_round(resultlist[i].input);
          break;

        default:
          abort();
          break;
      }

      debug_printf ("\t   ncptl_dfunc_%s (%.1lf) --> %.10lg",
                    testname[j], resultlist[i].input, actual);
      if ((ncptl_int)actual != (ncptl_int)correct) {
        debug_printf (" (should be %.1lf)\n", correct);
        RETURN_FAILURE();
      }
      debug_printf ("\n");
    }
  }

  RETURN_SUCCESS();
}
