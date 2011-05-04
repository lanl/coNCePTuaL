/* ----------------------------------------------------------------------
 *
 * Ensure that all of the ncptl_func_random_*() and
 * ncptl_dfunc_random_*() functions work
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
 * ---------------------------------------------------------------------- */

#include "ncptl_test.h"

#define RNG_SEED 12345678    /* Seed for the random-number generator */
#define TRIALS 100000        /* Number of trials to perform */
#define MTOLERANCE 5         /* Maximum tolerable distance between the expected and measured mean */
#define FPZERO 0.000001      /* "Close enough" to zero for a floating-point number */
#define ULOW 0               /* Low input for the uniform RNG */
#define UHIGH 100            /* High input for the uniform RNG */
#define GMEAN 100            /* Mean for the Gaussian RNG */
#define GSTD 10              /* Standard deviation for the Gaussian RNG */
#define PMEAN 50             /* Mean for the Poisson RNG */

ncptl_int uniform[TRIALS];   /* Random integers from a uniform distribution */
ncptl_int gaussian[TRIALS];  /* Random integers from a Gaussian distribution */
ncptl_int poisson[TRIALS];   /* Random integers from a Poisson distribution */
double uniform_d[TRIALS];    /* Random doubles from a uniform distribution */
double gaussian_d[TRIALS];   /* Random doubles from a Gaussian distribution */
double poisson_d[TRIALS];    /* Random doubles from a Poisson distribution */


/* Return the mean of an array of integers. */
ncptl_int integer_mean (ncptl_int *array)
{
  ncptl_int imean = 0;
  ncptl_int i;

  for (i=0; i<TRIALS; i++)
    imean += array[i];
  return imean/TRIALS;
}


/* Return the mean of an array of doubles. */
double fp_mean (double *array)
{
  double dmean = 0;
  ncptl_int i;

  for (i=0; i<TRIALS; i++)
    dmean += array[i];
  return dmean/TRIALS;
}


int main (void)
{
  ncptl_int imean;
  double dmean;
  ncptl_int i;

  /* Initialize to a fixed seed. */
  ncptl_seed_random_task (RNG_SEED, (ncptl_int)0);

  /* Generate a large set of random numbers. */
  for (i=0; i<TRIALS; i++) {
    uniform[i] = ncptl_func_random_uniform ((ncptl_int)ULOW, (ncptl_int)UHIGH);
    gaussian[i] = ncptl_func_random_gaussian ((ncptl_int)GMEAN, (ncptl_int)GSTD);
    poisson[i] = ncptl_func_random_poisson ((ncptl_int)PMEAN);
    uniform_d[i] = ncptl_dfunc_random_uniform ((double)ULOW, (double)UHIGH);
    gaussian_d[i] = ncptl_dfunc_random_gaussian ((double)GMEAN, (double)GSTD);
    poisson_d[i] = ncptl_dfunc_random_poisson ((double)PMEAN);
  }

  /* Ensure that the uniform values are within the specified range. */
  debug_printf ("\tTesting the range of ncptl_*_random_uniform() ...\n");
  for (i=0; i<TRIALS; i++) {
    if (uniform[i]<ULOW || uniform[i]>=UHIGH) {
      debug_printf ("\t   uniform: generated value %" NICS " is outside the range [%d, %d)\n",
                    uniform[i], ULOW, UHIGH);
      RETURN_FAILURE();
    }
    if (uniform_d[i]<(double)ULOW || uniform_d[i]>=(double)UHIGH) {
      debug_printf ("\t   uniform: generated value %g is outside the range [%g,%g)\n",
                    uniform_d[i], (double)ULOW, (double)UHIGH);
      RETURN_FAILURE();
    }
  }

  /* Ensure that all of the integer means are within a given tolerance. */
  debug_printf ("\tTesting the mean of ncptl_func_random_*() ...\n");
  imean = integer_mean (uniform);
  if (imean<(ULOW+UHIGH)/2-MTOLERANCE || imean>(ULOW+UHIGH)/2+MTOLERANCE) {
    debug_printf ("\t   uniform: expected a mean around %d but saw %" NICS "\n",
                  (ULOW+UHIGH)/2, imean);
    RETURN_FAILURE();
  }
  imean = integer_mean (gaussian);
  if (imean<GMEAN-MTOLERANCE || imean>GMEAN+MTOLERANCE) {
    debug_printf ("\t   gaussian: expected a mean around %d but saw %" NICS "\n",
                  GMEAN, imean);
    RETURN_FAILURE();
  }
  imean = integer_mean (poisson);
  if (imean<PMEAN-MTOLERANCE || imean>PMEAN+MTOLERANCE) {
    debug_printf ("\t   poisson: expected a mean around %d but saw %" NICS "\n",
                  PMEAN, imean);
    RETURN_FAILURE();
  }

  /* Ensure that all of the floating-point means are within a given tolerance. */
  debug_printf ("\tTesting the mean of ncptl_dfunc_random_*() ...\n");
  dmean = fp_mean (uniform_d);
  if (dmean<(ULOW+UHIGH)/2.0-MTOLERANCE || dmean>(ULOW+UHIGH)/2.0+MTOLERANCE) {
    debug_printf ("\t   uniform: expected a mean around %g but saw %g\n",
                  (ULOW+UHIGH)/2.0, dmean);
    RETURN_FAILURE();
  }
  dmean = fp_mean (gaussian_d);
  if (dmean<(double)(GMEAN-MTOLERANCE) || dmean>(double)(GMEAN+MTOLERANCE)) {
    debug_printf ("\t   gaussian: expected a mean around %g but saw %g\n",
                  (double)GMEAN, dmean);
    RETURN_FAILURE();
  }
  dmean = fp_mean (poisson_d);
  if (dmean<(double)(PMEAN-MTOLERANCE) || dmean>(double)(PMEAN+MTOLERANCE)) {
    debug_printf ("\t   poisson: expected a mean around %g but saw %g\n",
                  (double)PMEAN, dmean);
    RETURN_FAILURE();
  }

  /* Re-seed with the original seed and ensure that the generated
   * numbers are the same as before. */
  debug_printf ("\tTesting pseudorandom-number reproducibility ...\n");
  ncptl_seed_random_task (RNG_SEED, 0);
  for (i=0; i<TRIALS; i++) {
    ncptl_int newvalue;
    double newvalue_d;

    /* Check the integer functions. */
    if (uniform[i] != (newvalue=ncptl_func_random_uniform ((ncptl_int)ULOW, (ncptl_int)UHIGH))) {
      debug_printf ("\t   uniform: The same seed produced different values [%" NICS " != %" NICS "]\n",
                    uniform[i], newvalue);
      RETURN_FAILURE();
    }
    if (gaussian[i] != (newvalue=ncptl_func_random_gaussian ((ncptl_int)GMEAN, (ncptl_int)GSTD))) {
      debug_printf ("\t   gaussian: The same seed produced different values [%" NICS " != %" NICS "]\n",
                    gaussian[i], newvalue);
      RETURN_FAILURE();
    }
    if (poisson[i] != (newvalue=ncptl_func_random_poisson ((ncptl_int)PMEAN))) {
      debug_printf ("\t   poisson: The same seed produced different values [%" NICS " != %" NICS "]\n",
                    poisson[i], newvalue);
      RETURN_FAILURE();
    }

    /* Check the floating-point functions. */
    if (fabs(uniform_d[i] - (newvalue_d=ncptl_dfunc_random_uniform ((double)ULOW, (double)UHIGH))) > FPZERO) {
      debug_printf ("\t   uniform: The same seed produced different values [%g != %g]\n",
                    uniform_d[i], newvalue_d);
      RETURN_FAILURE();
    }
    if (fabs(gaussian_d[i] - (newvalue_d=ncptl_dfunc_random_gaussian ((double)GMEAN, (double)GSTD))) > FPZERO) {
      debug_printf ("\t   gaussian: The same seed produced different values [%g != %g]\n",
                    gaussian_d[i], newvalue_d);
      RETURN_FAILURE();
    }
    if (fabs(poisson_d[i] - (newvalue_d=ncptl_dfunc_random_poisson ((double)PMEAN))) > FPZERO) {
      debug_printf ("\t   poisson: The same seed produced different values [%g != %g]\n",
                    poisson_d[i], newvalue_d);
      RETURN_FAILURE();
    }
  }
  RETURN_SUCCESS();
}
