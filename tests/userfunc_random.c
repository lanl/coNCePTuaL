/* ----------------------------------------------------------------------
 *
 * Ensure that all of the ncptl_func_random_*() and
 * ncptl_dfunc_random_*() functions work
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * 
 * Copyright (C) 2003, Triad National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2003).  Triad National Security, LLC.  This software
 * was produced under U.S. Government contract 89233218CNA000001 for
 * Los Alamos National Laboratory (LANL), which is operated by Los
 * Alamos National Security, LLC (Triad) for the U.S. Department
 * of Energy. The U.S. Government has rights to use, reproduce,
 * and distribute this software.  NEITHER THE GOVERNMENT NOR TRIAD
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
 *   * Neither the name of Triad National Security, LLC, Los Alamos
 *     National Laboratory, the U.S. Government, nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY TRIAD AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL TRIAD OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
 * OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
 * BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * 
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
#define RSHAPE 2             /* Shape of the Pareto RNGs */
#define RLOW 30              /* Low input for the bounded Pareto RNG */
#define RHIGH 70             /* High input for the bounded Pareto RNG */
#define R2MEAN 60            /* Mean for the Pareto RNG */
#define R3MEAN 42            /* Mean for the bounded Pareto RNG */

/* Check if an array is stuck at a constant value. */
#define CHECK_STUCK(ANAME, ADATA, AFMT)                                    \
  do {                                                                     \
    for (i=0; i<TRIALS && ADATA[i] == ADATA[0]; i++)                       \
      ;                                                                    \
    if (i == TRIALS) {                                                     \
      debug_printf ("\t   %s: values are apparently stuck at %" AFMT "\n", \
                    ANAME, ADATA[0]);                                      \
      RETURN_FAILURE();                                                    \
    }                                                                      \
  }                                                                        \
  while (0)

/* Check if the mean of an integer array is out of bounds. */
#define CHECK_MEAN(ANAME, ADATA, EXPECTED)                                    \
  do {                                                                        \
    ncptl_int imean = integer_mean (ADATA);                                   \
    if (imean<(EXPECTED)-MTOLERANCE || imean>(EXPECTED)+MTOLERANCE) {         \
      debug_printf ("\t   %s: expected a mean around %d but saw %" NICS "\n", \
                    ANAME, EXPECTED, imean);                                  \
      RETURN_FAILURE();                                                       \
    }                                                                         \
  }                                                                           \
  while (0)

/* Check if the mean of a floating-point array is out of bounds. */
#define CHECK_MEAN_D(ANAME, ADATA, EXPECTED)                                  \
  do {                                                                        \
    double dmean = fp_mean (ADATA);                                           \
    if (dmean<(double)((EXPECTED)-MTOLERANCE)                                 \
        || dmean>(double)((EXPECTED)+MTOLERANCE)) {                           \
      debug_printf ("\t   %s: expected a mean around %d but saw %g\n",        \
                    ANAME, EXPECTED, dmean);                                  \
      RETURN_FAILURE();                                                       \
    }                                                                         \
  }                                                                           \
  while (0)


ncptl_int uniform[TRIALS];   /* Random integers from a uniform distribution */
ncptl_int gaussian[TRIALS];  /* Random integers from a Gaussian distribution */
ncptl_int poisson[TRIALS];   /* Random integers from a Poisson distribution */
ncptl_int pareto2[TRIALS];   /* Random integers from a Pareto distribution */
ncptl_int pareto3[TRIALS];   /* Random integers from a bounded Pareto distribution */
double uniform_d[TRIALS];    /* Random doubles from a uniform distribution */
double gaussian_d[TRIALS];   /* Random doubles from a Gaussian distribution */
double poisson_d[TRIALS];    /* Random doubles from a Poisson distribution */
double pareto2_d[TRIALS];    /* Random doubles from a Pareto distribution */
double pareto3_d[TRIALS];    /* Random doubles from a bounded Pareto distribution */


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
  ncptl_int i;

  /* Initialize to a fixed seed. */
  ncptl_seed_random_task (RNG_SEED, (ncptl_int)0);

  /* Generate a large set of random numbers. */
  for (i=0; i<TRIALS; i++) {
    uniform[i] = ncptl_func_random_uniform ((ncptl_int)ULOW, (ncptl_int)UHIGH);
    gaussian[i] = ncptl_func_random_gaussian ((ncptl_int)GMEAN, (ncptl_int)GSTD);
    poisson[i] = ncptl_func_random_poisson ((ncptl_int)PMEAN);
    pareto2[i] = ncptl_func_random_pareto ((ncptl_int)RSHAPE, (ncptl_int)RLOW, (ncptl_int)RLOW);
    pareto3[i] = ncptl_func_random_pareto ((ncptl_int)RSHAPE, (ncptl_int)RLOW, (ncptl_int)RHIGH);
    uniform_d[i] = ncptl_dfunc_random_uniform ((double)ULOW, (double)UHIGH);
    gaussian_d[i] = ncptl_dfunc_random_gaussian ((double)GMEAN, (double)GSTD);
    poisson_d[i] = ncptl_dfunc_random_poisson ((double)PMEAN);
    pareto2_d[i] = ncptl_dfunc_random_pareto ((double)RSHAPE, (double)RLOW, (double)RLOW);
    pareto3_d[i] = ncptl_dfunc_random_pareto ((double)RSHAPE, (double)RLOW, (double)RHIGH);
  }

  /* Ensure that we're not seeing the name number over and over again. */
  debug_printf ("\tTesting pseudorandom-number variability ...\n");
  CHECK_STUCK("uniform",  uniform,    NICS);
  CHECK_STUCK("gaussian", gaussian,   NICS);
  CHECK_STUCK("poisson",  poisson,    NICS);
  CHECK_STUCK("pareto2",  pareto2,    NICS);
  CHECK_STUCK("pareto3",  pareto3,    NICS);
  CHECK_STUCK("uniform",  uniform_d,  "g");
  CHECK_STUCK("gaussian", gaussian_d, "g");
  CHECK_STUCK("poisson",  poisson_d,  "g");
  CHECK_STUCK("pareto2",  pareto2_d,  "g");
  CHECK_STUCK("pareto3",  pareto3_d,  "g");

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

  /* Ensure that the Pareto values are within the specified range. */
  debug_printf ("\tTesting the range of ncptl_*_random_pareto() ...\n");
  for (i=0; i<TRIALS; i++) {
    if (pareto2[i]<RLOW) {
      debug_printf ("\t   pareto2: generated value %" NICS " is outside the range [%d, +inf)\n",
                    pareto2[i], RLOW);
      RETURN_FAILURE();
    }
    if (pareto2_d[i]<(double)RLOW) {
      debug_printf ("\t   pareto2: generated value %g is outside the range [%g, +inf)\n",
                    pareto2_d[i], (double)RLOW);
      RETURN_FAILURE();
    }
    if (pareto3[i]<RLOW || pareto3[i]>RHIGH) {
      debug_printf ("\t   pareto3: generated value %" NICS " is outside the range [%d, %d]\n",
                    pareto3[i], RLOW, RHIGH);
      RETURN_FAILURE();
    }
    if (pareto3_d[i]<(double)RLOW || pareto3_d[i]>(double)RHIGH) {
      debug_printf ("\t   pareto3: generated value %g is outside the range [%g,%g)\n",
                    pareto3_d[i], (double)RLOW, (double)RHIGH);
      RETURN_FAILURE();
    }
  }

  /* Ensure that all of the integer means are within a given tolerance. */
  debug_printf ("\tTesting the mean of ncptl_func_random_*() ...\n");
  CHECK_MEAN("uniform",  uniform,  (ULOW+UHIGH)/2);
  CHECK_MEAN("gaussian", gaussian, GMEAN);
  CHECK_MEAN("poisson",  poisson,  PMEAN);
  CHECK_MEAN("pareto2",  pareto2,  R2MEAN);
  CHECK_MEAN("pareto3",  pareto3,  R3MEAN);

  /* Ensure that all of the floating-point means are within a given
   * tolerance. */
  debug_printf ("\tTesting the mean of ncptl_dfunc_random_*() ...\n");
  CHECK_MEAN_D("uniform",  uniform_d,  (ULOW+UHIGH)/2);
  CHECK_MEAN_D("gaussian", gaussian_d, GMEAN);
  CHECK_MEAN_D("poisson",  poisson_d,  PMEAN);
  CHECK_MEAN_D("pareto2",  pareto2_d,  R2MEAN);
  CHECK_MEAN_D("pareto3",  pareto3_d,  R3MEAN);

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
    if (pareto2[i] != (newvalue=ncptl_func_random_pareto ((ncptl_int)RSHAPE, (ncptl_int)RLOW, (ncptl_int)RLOW))) {
      debug_printf ("\t   pareto2: The same seed produced different values [%" NICS " != %" NICS "]\n",
                    pareto2[i], newvalue);
      RETURN_FAILURE();
    }
    if (pareto3[i] != (newvalue=ncptl_func_random_pareto ((ncptl_int)RSHAPE, (ncptl_int)RLOW, (ncptl_int)RHIGH))) {
      debug_printf ("\t   pareto3: The same seed produced different values [%" NICS " != %" NICS "]\n",
                    pareto3[i], newvalue);
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
    if (fabs(pareto2_d[i] - (newvalue_d=ncptl_dfunc_random_pareto ((double)RSHAPE, (double)RLOW, (double)RLOW))) > FPZERO) {
      debug_printf ("\t   pareto2: The same seed produced different values [%g != %g]\n",
                    pareto2_d[i], newvalue_d);
      RETURN_FAILURE();
    }
    if (fabs(pareto3_d[i] - (newvalue_d=ncptl_dfunc_random_pareto ((double)RSHAPE, (double)RLOW, (double)RHIGH))) > FPZERO) {
      debug_printf ("\t   pareto3: The same seed produced different values [%g != %g]\n",
                    pareto3_d[i], newvalue_d);
      RETURN_FAILURE();
    }
  }
  RETURN_SUCCESS();
}
