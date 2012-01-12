/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * functions callable from a coNCePTuaL program
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2012, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2012).  Los Alamos National Security, LLC.  This software
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

/* Abort if a given value is NaN or +/- infinity. */
#define VALIDATE_FLOAT(NUMBER)                                          \
  if (!finite(NUMBER))                                                  \
     ncptl_fatal ("unable to perform a numeric operation on \"%f\"",    \
                  (NUMBER))

/* Believe it or not, some systems (the OpenBSD 3.5 system that I
 * tested and Microsoft Windows) lack a trunc() function.  Other
 * systems (the PowerPC/Linux system I tested with IBM's xlc compiler)
 * don't declare trunc(), thereby making it default to integer
 * type. */
#ifdef HAVE_TRUNC
extern double trunc(double);
#elif defined(HAVE_FLOOR)
# define trunc(X) ((X)<0.0 ? -floor(-(X)) : floor(X))
#elif defined(HAVE_FMOD)
# define trunc(X) ((X)-fmod((X), 1.0))
#else
# error unable to find or fabricate a trunc() function
#endif

/* Conditionally seed the unsynchronized random-number generator. */
#define SEED_UNSYNC_RNG()                       \
do {                                            \
  if (!ncptl_unsync_rand_state_seeded) {        \
    seed_unsync_rng();                          \
    ncptl_unsync_rand_state_seeded = 1;         \
  }                                             \
}                                               \
while (0)

/* ASCI Red lacks a getppid() function. */
#ifndef HAVE_GETPPID
# define getppid() (-1)
#endif


/************************************
 * Imported variables and functions *
 ************************************/

extern int ncptl_rng_seed;
extern ncptl_int ncptl_self_proc;
extern void ncptl_init_genrand (RNG_STATE *, uint64_t);
extern long ncptl_genrand_int64 (RNG_STATE *);
extern long ncptl_genrand_int64 (RNG_STATE *);
extern double ncptl_genrand_res53 (RNG_STATE *);


/**************************
 * Library-global variable
 **************************/

int ncptl_unsync_rand_state_seeded = 0;    /* 1=RNG is already seeded */


/************************************
 * Internal variables and functions *
 ************************************/

/* State for a random-number generator that is unsynchronized across
 * tasks. */
static RNG_STATE unsync_rand_state;         /* Random state */


/* Do most of the work of ncptl_func_ipower. */
static ncptl_int ncptl_ipower_helper (ncptl_int base, ncptl_int exponent)
{
  ncptl_int halfpowersq;   /* The square of (BASE raised to the EXPONENT/2 power) */

  if (exponent == 0)
    return 1;
  if (exponent == 1)
    return base;
  halfpowersq = ncptl_ipower_helper (base, exponent/2);
  halfpowersq *= halfpowersq;
  if ((exponent&1) == 0)
    return halfpowersq;
  else
    return halfpowersq * base;
}


/* Return the number of base-k digits needed to represent a given
 * number (helper function for ncptl_func_knomial_*). */
static ncptl_int knomial_numdigits (ncptl_int arity, ncptl_int number)
{
  ncptl_int numdigits = 1;
  ncptl_int powk = arity;

  while (powk-1 < number) {
    numdigits++;
    powk *= arity;
  }
  return numdigits;
}


/* Return the ith least significant digit of a base-k number (helper
 * function for ncptl_func_knomial_*). */
static ncptl_int knomial_getdigit (ncptl_int arity, ncptl_int number,
                                   ncptl_int digit)
{
  return (number / ncptl_func_power(arity, digit)) % arity;
}


/* Set the ith least significant digit of a base-k number to a given
 * value (helper function for ncptl_func_knomial_*). */
static ncptl_int knomial_setdigit (ncptl_int arity, ncptl_int number,
                                   ncptl_int digit, ncptl_int newdigit)
{
  ncptl_int result = number;
  ncptl_int shift_amount = ncptl_func_power (arity, digit);

  /* Subtract off the old digit and add in the new digit. */
  result -= knomial_getdigit (arity, number, digit) * shift_amount;
  result += newdigit * shift_amount;
  return result;
}


/* Seed the unsynchronized random-number generator to a value derived
 * from the synchronized random-number generator's seed. */
static void seed_unsync_rng (void)
{
  ncptl_int seed_to_use;
  const ncptl_int bigprime = 1083743797;

  /* Refuse to run without a seed. */
  if (!ncptl_rng_seed || ncptl_self_proc == -1)
    ncptl_fatal ("ncptl_seed_random_task() must be called before any of the other random-number functions");

  /* Seed the random-number generator. */
  seed_to_use = ((ncptl_rng_seed ? ncptl_rng_seed : 1) * bigprime
                 + (ncptl_self_proc<0 ? 0 : ncptl_self_proc));
  ncptl_init_genrand (&unsync_rand_state, (uint64_t)seed_to_use);
}


/* Return a task's x, y, and z coordinates on a 3-D mesh or -1 if the
 * task does not lie anywhere on the given 3-D mesh. */
static void get_mesh_coordinates (ncptl_int width, ncptl_int height, ncptl_int depth,
                                  ncptl_int task,
                                  ncptl_int *xpos, ncptl_int *ypos, ncptl_int *zpos)
{
  ncptl_int meshelts = width * height * depth;

  /* Abort if we were given unreasonable mesh dimensions. */
  if (!meshelts)
    ncptl_fatal ("neighbor calculations can't be performed on a zero-sized mesh/torus");
  if (width<0 || height<0 || depth<0)
    ncptl_fatal ("meshes/tori may not have negative dimensions");

  /* Tasks that are outside of the mesh have no neighbors. */
  if (task<0 || task>=meshelts) {
    *xpos = *ypos = *zpos = -1;
    return;
  }

  /* Map the task number from Z to Z^3. */
  *xpos = task % width;
  *ypos = (task % (width*height)) / width;
  *zpos = task / (width*height);
}


/**********************
 * Exported functions *
 **********************/

/* Return the largest integer x such that x*x <= num.  We use the
 * Newton-Raphson method as this should converge quickly, especially
 * for small inputs. */
ncptl_int ncptl_func_sqrt (ncptl_int num)
{
  if (num < 0) {
    ncptl_fatal ("unable to take SQRT(%" NICS "); result is undefined", num);
    return -1;      /* Appease idiotic compilers. */
  }
  else
    if (num <= 1)
      return num;
    else
      return ncptl_func_root (2, num);
}

/* Double version of the above */
double ncptl_dfunc_sqrt (double num)
{
  VALIDATE_FLOAT (num);
  if (num < 0)
    ncptl_fatal ("unable to take SQRT(%g); result is undefined", num);
  return sqrt(num);
}


/* Return the largest-in-magnitude integer x such that x*x*x <= num.
 * We use the Newton-Raphson method as this should converge quickly,
 * especially for small inputs.  Note that we do all of our arithmetic
 * with 64-bit integers as we expect NUM to be fairly small but still
 * large enough to overflow 32 bits when squared. */
ncptl_int ncptl_func_cbrt (ncptl_int num)
{
  if (num == 0)
    return 0;
  else
    if (num < 0)
      ncptl_fatal ("unable to take CBRT(%" NICS "); result is undefined", num);
    else
      return ncptl_func_root (3, num);
  return -1;      /* Appease idiotic compilers. */
}


/* Double version of the above */
double ncptl_dfunc_cbrt (double num)
{
  VALIDATE_FLOAT (num);
  if (num < 0.0)
    ncptl_fatal ("unable to take CBRT(%g); result is undefined", num);
#ifdef HAVE_CBRT
  return cbrt (num);
#else
  return pow (num, 1.0/3.0);
#endif
}


/* Return the largest-in-magnitude integer x with the same sign as NUM
 * such that |x^ROOT| <= |NUM|. */
ncptl_int ncptl_func_root (ncptl_int root, ncptl_int num)
{
  ncptl_int result = (ncptl_int) trunc (ncptl_dfunc_root ((double) root,
                                                          (double) num));

  /* Round manually in order to guarantee we found the desired integer. */
  if (ncptl_func_power (result+1, root) <= num)
    return result+1;
  else
    return result;
}


/* Define a double version of the above.  Basically, we rely on the C
 * math library's pow() function but we first do some additional error
 * checking of our own. */
double ncptl_dfunc_root (double root, double num)
{
  VALIDATE_FLOAT (root);
  VALIDATE_FLOAT (num);
  if (root==0.0 || num<0.0)
    ncptl_fatal ("unable to take ROOT(%g, %g); result is undefined",
                 root, num);
  return pow (num, 1.0/root);
}


/* Return the minimum number of bits needed to represent a given number. */
ncptl_int ncptl_func_bits (ncptl_int num)
{
  uint64_t unum = (uint64_t)num;
  ncptl_int numbits = 0;

  while (unum) {
    numbits++;
    unum >>= 1;
  }
  return numbits;
}


/* Double version of the above */
double ncptl_dfunc_bits (double num)
{
  VALIDATE_FLOAT (num);
  return (double) ncptl_func_bits ((ncptl_int)ceil((double)(ncptl_int)num));
}


/* Left-shift a number by a given number of bits.  A negative number
 * of bits results in a right shift. */
ncptl_int ncptl_func_shift_left (ncptl_int num, ncptl_int bits)
{
  return bits>=0 ? num<<bits : num>>-bits;
}


/* Double version of the above */
double ncptl_dfunc_shift_left (double num, double bits)
{
  VALIDATE_FLOAT (num);
  VALIDATE_FLOAT (bits);
  return (double) ncptl_func_shift_left ((ncptl_int)num, (ncptl_int)bits);
}


/* Return the floor of the base-10 logarithm of a given number. */
ncptl_int ncptl_func_log10 (ncptl_int num)
{
  if (num <= 0)
    ncptl_fatal ("unable to take the base-10 logarithm of a non-positive number (%" NICS ")",
                 num);
  return (ncptl_int) floor(log10(num));
}


/* Double version of the above */
double ncptl_dfunc_log10 (double num)
{
  VALIDATE_FLOAT (num);
  return log10(num);
}


/* Integer version of the following */
ncptl_int ncptl_func_factor10 (ncptl_int num)
{
  return (ncptl_int) ncptl_dfunc_factor10 ((double) num);
}


/* Return the given number rounded down to the nearest factor of a
 * power of 10. */
double ncptl_dfunc_factor10 (double num)
{
  VALIDATE_FLOAT (num);
  if (num == 0)
    return 0.0;
  else
    if (num > 0) {
      double floorlog10 = floor(log10(num));
      double pow10 = pow (10.0, floorlog10);
      double factor = floor (num / pow10);
      return factor * pow10;
    }
    else {
      double floorlog10 = floor(log10(-num));
      double pow10 = pow (10.0, floorlog10);
      double factor = floor (-num / pow10);
      return -factor * pow10;
    }
}


/* Return the absolute value of a given number. */
ncptl_int ncptl_func_abs (ncptl_int number)
{
  if (number == NCPTL_INT_MIN)
    ncptl_fatal ("the absolute value of %" NICS " is not defined in %lu-bit arithmetic",
                 number, (unsigned long)(8*sizeof(ncptl_int)));
#ifdef HAVE_LLABS
  return (ncptl_int) llabs ((uint64_t) number);
#else
  return number>=0 ? number : -number;
#endif
}


/* Double version of the above */
double ncptl_dfunc_abs (double num)
{
  VALIDATE_FLOAT (num);
  return fabs(num);
}


/* Return one integer raised to the power of another integer (called
 * by coNCePTuaL's "**" operator). */
ncptl_int ncptl_func_power (ncptl_int base, ncptl_int exponent)
{
  if (base==0 && exponent==0)
    ncptl_fatal ("unable to raise zero to the zeroth power");
  if (exponent < 0) {
    ncptl_int result = 0;

    switch (base) {
      case 0:
        ncptl_fatal ("unable to raise zero to a negative power");
        break;

      case 1:
        result = 1;
        break;

      case (-1):
        result = exponent&1 ? -1 : 1;
        break;

      default:
        result = 0;
        break;
    }
    return result;
  }
  return ncptl_ipower_helper (base, exponent);
}


/* Define a double version of the above.  Basically, we rely on the C
 * math library's pow() function but we first do some additional error
 * checking of our own. */
double ncptl_dfunc_power (double base, double exponent)
{
  const char *undefined_power_msg =    /* Format string for ncptl_fatal() */
    "unable to take (%g)**(%g); result is undefined";

  /* Abort if we can't represent BASE**EXPONENT. */
  VALIDATE_FLOAT (base);
  VALIDATE_FLOAT (exponent);
  if (base==0.0 && exponent<=0.0)
    /* Zero to a negative or zero power */
    ncptl_fatal (undefined_power_msg, base, exponent);
  if (base<0.0 && exponent!=trunc(exponent))
    /* Negative number to a non-integral power */
    ncptl_fatal (undefined_power_msg, base, exponent);

  /* At this point, either BASE is non-negative or EXPONENT is an
   * integer.  The math library's pow() function should therefore be
   * safe to use. */
  return pow (base, exponent);
}


/* Return the remainder of dividing one number by another.  The result
 * is guaranteed to be a nonnegative integer. */
ncptl_int ncptl_func_modulo (ncptl_int numerator, ncptl_int denominator)
{
  ncptl_int result;

  if (!denominator)
    ncptl_fatal ("%" NICS " modulo 0 is not defined", numerator);
  if (denominator < 0)
    denominator = -denominator;
  result = numerator % denominator;
  return result<0 ? result+denominator : result;
}

/* Double version of the above */
double ncptl_dfunc_modulo (double numerator, double denominator)
{
  /* coNCePTuaL really has no need for floating-point remainder.
   * Hence, we perform the modulo operation with integers instead of
   * invoking fmod() or drem(). */
  VALIDATE_FLOAT (numerator);
  VALIDATE_FLOAT (denominator);
  return (double) ncptl_func_modulo ((ncptl_int)numerator, (ncptl_int)denominator);
}


/* Return the floor of a number (identity function for integers). */
ncptl_int ncptl_func_floor (ncptl_int number)
{
  return number;
}

/* Double version of the above */
double ncptl_dfunc_floor (double number)
{
  VALIDATE_FLOAT (number);
  return floor(number);
}


/* Return the ceiling of a number (identity function for integers). */
ncptl_int ncptl_func_ceiling (ncptl_int number)
{
  return number;
}

/* Double version of the above */
double ncptl_dfunc_ceiling (double number)
{
  VALIDATE_FLOAT (number);
  return ceil(number);
}


/* Return a number rounded away from zero (identity function for integers). */
ncptl_int ncptl_func_round (ncptl_int number)
{
  return number;
}

/* Double version of the above */
double ncptl_dfunc_round (double number)
{
  VALIDATE_FLOAT (number);
#if defined(HAVE_ROUND) && defined(ROUND_WORKS)
  /* Round away from zero. */
  return round(number);
#elif HAVE_NEARBYINT
  /* Round away from zero assuming the current rounding mode says to do so. */
  return nearbyint(number);
#elif HAVE_RINT
  /* Same as nearbyint() but potentially raise an "inexact" exception. */
  return rint(number);
#else
  /* Implement rounding in terms of truncation. */
  return number<0.0 ? trunc(number-0.5) : trunc(number+0.5);
#endif
}


/* Return a task's parent in an N-ary tree. */
ncptl_int ncptl_func_tree_parent (ncptl_int task, ncptl_int arity)
{
  if (arity < 1)
    ncptl_fatal ("an N-ary tree requires a positive value of N");
  return task<=0 ? -1 : (task-1)/arity;
}

/* Double version of the above */
double ncptl_dfunc_tree_parent (double task, double arity)
{
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (arity);
  return (double) ncptl_func_tree_parent ((ncptl_int)task, (ncptl_int)arity);
}


/* Return a child of a task in an N-ary tree. */
ncptl_int ncptl_func_tree_child (ncptl_int task, ncptl_int child, ncptl_int arity)
{
  if (arity < 1)
    ncptl_fatal ("an N-ary tree requires a positive value of N");
  if (child<0 || child>=arity)
    return -1;
  return task*arity + child + 1;
}

/* Double version of the above */
double ncptl_dfunc_tree_child (double task, double child, double arity)
{
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (child);
  VALIDATE_FLOAT (arity);
  return (double) ncptl_func_tree_child ((ncptl_int) task,
                                         (ncptl_int) child,
                                         (ncptl_int) arity);
}


/* Return a task's x, y, or z coordinate on a 3-D mesh or torus. */
ncptl_int ncptl_func_mesh_coord (ncptl_int width, ncptl_int height, ncptl_int depth,
                                 ncptl_int task, ncptl_int coord)
{
  ncptl_int xpos, ypos, zpos;

  get_mesh_coordinates (width, height, depth, task, &xpos, &ypos, &zpos);
  switch (coord) {
    case 0:
      return xpos;
    case 1:
      return ypos;
    case 2:
      return zpos;
    default:
      ncptl_fatal ("mesh/torus coordinate must be 0, 1, or 2 (for x, y, or z, respectively)");
      break;
  }
  return -1;      /* Appease idiotic compilers. */
}

/* Double version of the above */
double ncptl_dfunc_mesh_coord (double width, double height, double depth,
                               double task, double coord)
{
  VALIDATE_FLOAT (width);
  VALIDATE_FLOAT (height);
  VALIDATE_FLOAT (depth);
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (coord);
  return (double) ncptl_func_mesh_coord ((ncptl_int) width,
                                         (ncptl_int) height,
                                         (ncptl_int) depth,
                                         (ncptl_int) task,
                                         (ncptl_int) coord);
}


/* Return a task's neighbor on a 3-D mesh or torus. */
ncptl_int ncptl_func_mesh_neighbor (ncptl_int width, ncptl_int height, ncptl_int depth,
                                    ncptl_int xtorus, ncptl_int ytorus, ncptl_int ztorus,
                                    ncptl_int task,
                                    ncptl_int xdelta, ncptl_int ydelta, ncptl_int zdelta)
{
  ncptl_int xpos, ypos, zpos;

  /* Add deltas to each coordinate in turn.  If we fall off the end of
     a row, column, or pile, we wrap around (torus case) or return an
     invalid neighbor (mesh case). */
  get_mesh_coordinates (width, height, depth, task, &xpos, &ypos, &zpos);
  if (xpos == -1)
    return -1;
  xpos += xdelta;
  ypos += ydelta;
  zpos += zdelta;
  if (xtorus)
    xpos = ncptl_func_modulo (xpos, width);
  if (ytorus)
    ypos = ncptl_func_modulo (ypos, height);
  if (ztorus)
    zpos = ncptl_func_modulo (zpos, depth);
  if (xpos<0 || xpos>=width ||
      ypos<0 || ypos>=height ||
      zpos<0 || zpos>=depth)
    return -1;

  /* Map back from Z^3 to Z. */
  return zpos*height*width + ypos*width + xpos;
}

/* Double version of the above */
double ncptl_dfunc_mesh_neighbor (double width, double height, double depth,
                                  double xtorus, double ytorus, double ztorus,
                                  double task,
                                  double xdelta, double ydelta, double zdelta)
{
  VALIDATE_FLOAT (width);
  VALIDATE_FLOAT (height);
  VALIDATE_FLOAT (depth);
  VALIDATE_FLOAT (xtorus);
  VALIDATE_FLOAT (ytorus);
  VALIDATE_FLOAT (ztorus);
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (xdelta);
  VALIDATE_FLOAT (ydelta);
  VALIDATE_FLOAT (zdelta);
  return (double) ncptl_func_mesh_neighbor ((ncptl_int) width,
                                            (ncptl_int) height,
                                            (ncptl_int) depth,
                                            (ncptl_int) xtorus,
                                            (ncptl_int) ytorus,
                                            (ncptl_int) ztorus,
                                            (ncptl_int) task,
                                            (ncptl_int) xdelta,
                                            (ncptl_int) ydelta,
                                            (ncptl_int) zdelta);
}


/* Return the Manhattan distance between two tasks on a 3-D mesh or torus. */
ncptl_int ncptl_func_mesh_distance (ncptl_int width, ncptl_int height, ncptl_int depth,
                                    ncptl_int xtorus, ncptl_int ytorus, ncptl_int ztorus,

                                    ncptl_int task1, ncptl_int task2)
{
  ncptl_int xpos1, ypos1, zpos1;
  ncptl_int xpos2, ypos2, zpos2;
  ncptl_int xdelta, ydelta, zdelta;

  /* Get each task's x, y, and z coordinates.  Return -1 if either
   * task does not lie on the mesh/torus. */
  get_mesh_coordinates (width, height, depth, task1, &xpos1, &ypos1, &zpos1);
  get_mesh_coordinates (width, height, depth, task2, &xpos2, &ypos2, &zpos2);
  if (xpos1 == -1 || xpos2 == -1)
    return -1;

  /* Compute the distance between each pair of coordinates on a mesh. */
  xdelta = ncptl_func_abs (xpos1 - xpos2);
  ydelta = ncptl_func_abs (ypos1 - ypos2);
  zdelta = ncptl_func_abs (zpos1 - zpos2);

  /* See if we can take shortcuts across any torus edges. */
  if (xtorus && xdelta > width/2)
    xdelta = width - xdelta;
  if (ytorus && ydelta > height/2)
    ydelta = height - ydelta;
  if (ztorus && zdelta > depth/2)
    zdelta = depth - zdelta;

  /* Return the Manhattan distance between the two tasks. */
  return xdelta + ydelta + zdelta;
}

/* Double version of the above */
double ncptl_dfunc_mesh_distance (double width, double height, double depth,
                                  double xtorus, double ytorus, double ztorus,
                                  double task1, double task2)
{
  VALIDATE_FLOAT (width);
  VALIDATE_FLOAT (height);
  VALIDATE_FLOAT (depth);
  VALIDATE_FLOAT (xtorus);
  VALIDATE_FLOAT (ytorus);
  VALIDATE_FLOAT (ztorus);
  VALIDATE_FLOAT (task1);
  VALIDATE_FLOAT (task2);
  return (double) ncptl_func_mesh_distance ((ncptl_int) width,
                                            (ncptl_int) height,
                                            (ncptl_int) depth,
                                            (ncptl_int) xtorus,
                                            (ncptl_int) ytorus,
                                            (ncptl_int) ztorus,
                                            (ncptl_int) task1,
                                            (ncptl_int) task2);
}


/* Return a task's parent in an k-nomial tree. */
ncptl_int ncptl_func_knomial_parent (ncptl_int task, ncptl_int arity,
                                     ncptl_int numtasks)
{
  ncptl_int digit;    /* Current base-k digit of the task ID */

  /* Sanity check our arguments. */
  if (arity < 2)
    ncptl_fatal ("a k-nomial tree requires that k be at least 2");
  if (task<=0 || task>=numtasks)
    return -1;

  /* Find the most significant non-zero digit (base k) and set that
   * digit to zero. */
  for (digit=knomial_numdigits(arity, numtasks-1)-1; digit>=0; digit--)
    if (knomial_getdigit (arity, task, digit))
      return knomial_setdigit (arity, task, digit, 0);
  ncptl_fatal ("internal error in %s, line %d", __FILE__, __LINE__);
  return -1;      /* Appease idiotic compilers. */
}

/* Double version of the above */
double ncptl_dfunc_knomial_parent (double task, double arity, double numtasks)
{
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (arity);
  VALIDATE_FLOAT (numtasks);
  return (double) ncptl_func_knomial_parent ((ncptl_int) task,
                                             (ncptl_int) arity,
                                             (ncptl_int) numtasks);
}


/* If count_only is 0, return a task's ith child in a k-nomial tree.
 * If count_only is 1, return the number of children a task has in a
 * k-nomial tree. */
ncptl_int ncptl_func_knomial_child (ncptl_int task, ncptl_int child,
                                    ncptl_int arity, ncptl_int numtasks,
                                    ncptl_int count_only)
{
  static struct {     /* Previous values of various arguments */
    ncptl_int task;
    ncptl_int arity;
    ncptl_int numtasks;
  } previous = {0, 0, 0};
  static ncptl_int *children = NULL;    /* Complete list of children */
  static ncptl_int num_children = 0;    /* # of elements in the above */
  ncptl_int digit;    /* Current base-k digit of the task ID */

  /* Sanity check our arguments. */
  if (arity < 2)
    ncptl_fatal ("a k-nomial tree requires that k be at least 2");
  if (task>=numtasks || child<0)
    return -1;

  /* If we were given the same arguments on the previous iteration
   * that we can recycle children[] and num_children. */
  if (task!=previous.task || arity!=previous.arity || numtasks!=previous.numtasks) {
    /* For each zero digit (base k) down to the most significant
     * non-zero digit, compute a child ID by setting that digit in
     * turn to each of {0, ..., k-1}. */
    num_children = 0;
    children = (ncptl_int *) realloc (children, numtasks*sizeof(ncptl_int));
    if (!children)
      ncptl_fatal ("unable to allocate %" NICS " bytes for storing k-nomial children",
                   numtasks*(ncptl_int)sizeof(ncptl_int));
    for (digit=knomial_numdigits(arity, numtasks-1)-1; digit>=0; digit--) {
      ncptl_int nonz;     /* Each possible nonzero value of a base-k digit */

      if (knomial_getdigit (arity, task, digit))
        break;
      for (nonz=arity-1; nonz>=1; nonz--) {
        ncptl_int childID = knomial_setdigit (arity, task, digit, nonz);
        if (childID < numtasks)
          children[num_children++] = childID;
      }
    }

    /* Store the current values of some of our arguments on the
     * assumption that the caller will loop over a set of children. */
    previous.task = task;
    previous.arity = arity;
    previous.numtasks = numtasks;
  }

  /* Return either a child ID or the total number of children. */
  if (count_only)
    return num_children;
  else
    return child<num_children ? children[num_children-child-1] : -1;
}

/* Double version of the above */
double ncptl_dfunc_knomial_child (double task, double child,
                                  double arity, double numtasks,
                                  double count_only)
{
  VALIDATE_FLOAT (task);
  VALIDATE_FLOAT (child);
  VALIDATE_FLOAT (arity);
  VALIDATE_FLOAT (numtasks);
  VALIDATE_FLOAT (count_only);
  return (double) ncptl_func_knomial_child ((ncptl_int) task,
                                            (ncptl_int) child,
                                            (ncptl_int) arity,
                                            (ncptl_int) numtasks,
                                            (ncptl_int) count_only);
}


/* Return the minimum of a list of numbers. */
ncptl_int ncptl_func_min (ncptl_int count, ...)
{
  va_list arglist;          /* Opaque type representing the argument list */
  ncptl_int result;         /* Minimum-valued argument */

  /* Sanity-check the list length. */
  if (count <= 0)
    ncptl_fatal ("internal error -- ncptl_func_min() requires a count of at least 1");

  /* Iterate over all COUNT numbers in the list. */
  va_start (arglist, count);
  result = (ncptl_int) va_arg (arglist, ncptl_int);
  while (--count > 0) {
    ncptl_int newvalue = (ncptl_int) va_arg (arglist, ncptl_int);
    if (result > newvalue)
      result = newvalue;
  }
  va_end (arglist);
  return result;
}

/* Double version of the above */
double ncptl_dfunc_min (double count_d, ...)
{
  ncptl_int count;       /* Integer version of COUNT_D */
  va_list arglist;       /* Opaque type representing the argument list */
  double result;         /* Minimum-valued argument */

  /* Sanity-check the list length. */
  VALIDATE_FLOAT (count_d);
  count = (ncptl_int) count_d;
  if (count <= 0)
    ncptl_fatal ("internal error -- ncptl_dfunc_min() requires a count of at least 1");

  /* Iterate over all COUNT numbers in the list. */
  va_start (arglist, count_d);
  result = (double) va_arg (arglist, double);
  while (--count > 0) {
    double newvalue = (double) va_arg (arglist, double);
    if (result > newvalue)
      result = newvalue;
  }
  va_end (arglist);
  return result;
}


/* Return the maximum of a list of numbers. */
ncptl_int ncptl_func_max (ncptl_int count, ...)
{
  va_list arglist;          /* Opaque type representing the argument list */
  ncptl_int result;         /* Maximum-valued argument */

  /* Sanity-check the list length. */
  if (count <= 0)
    ncptl_fatal ("internal error -- ncptl_func_max() requires a count of at least 1");

  /* Iterate over all COUNT numbers in the list. */
  va_start (arglist, count);
  result = (ncptl_int) va_arg (arglist, ncptl_int);
  while (--count > 0) {
    ncptl_int newvalue = (ncptl_int) va_arg (arglist, ncptl_int);
    if (result < newvalue)
      result = newvalue;
  }
  va_end (arglist);
  return result;
}

/* Double version of the above */
double ncptl_dfunc_max (double count_d, ...)
{
  ncptl_int count;       /* Integer version of COUNT_D */
  va_list arglist;       /* Opaque type representing the argument list */
  double result;         /* Maximum-valued argument */

  /* Sanity-check the list length. */
  VALIDATE_FLOAT (count_d);
  count = (ncptl_int) count_d;
  if (count <= 0)
    ncptl_fatal ("internal error -- ncptl_dfunc_max() requires a count of at least 1");

  /* Iterate over all COUNT numbers in the list. */
  va_start (arglist, count_d);
  result = (double) va_arg (arglist, double);
  while (--count > 0) {
    double newvalue = (double) va_arg (arglist, double);
    if (result < newvalue)
      result = newvalue;
  }
  va_end (arglist);
  return result;
}


/* Return a uniform random number in the range [LOWER, UPPER).
 * Currently, UPPER must be less than 2^63. */
ncptl_int ncptl_func_random_uniform (ncptl_int lowerbound, ncptl_int upperbound)
{
  ncptl_int result;

  SEED_UNSYNC_RNG();
  if (lowerbound >= upperbound)
    ncptl_fatal ("RANDOM_UNIFORM requires the upper bound to be greater than the lower bound");
  result = ncptl_genrand_int64 (&unsync_rand_state);
  result = ncptl_func_modulo (result, upperbound-lowerbound) + lowerbound;
  return result;
}

/* Double version of the above */
double ncptl_dfunc_random_uniform (double lowerbound, double upperbound)
{
  double result;

  SEED_UNSYNC_RNG();
  VALIDATE_FLOAT (lowerbound);
  VALIDATE_FLOAT (upperbound);
  if (lowerbound >= upperbound)
    ncptl_fatal ("RANDOM_UNIFORM requires the upper bound to be greater than the lower bound");
  result = ncptl_genrand_res53 (&unsync_rand_state);
  result = result * (upperbound-lowerbound) + lowerbound;
  return result;
}


/* Return a randomly selected number from a Gaussian distribution with
 * mean MEAN and standard deviation STDDEV. */
ncptl_int ncptl_func_random_gaussian (ncptl_int mean, ncptl_int stddev)
{
  /* Let the double version do all of the work. */
  return (ncptl_int) ncptl_dfunc_random_gaussian ((double)mean, (double)stddev);
}

/* Double version of the above */
double ncptl_dfunc_random_gaussian (double mean, double stddev)
{
  double gaussian;                 /* Current Gaussian on [0,1) to use */
  static double next_gaussian;     /* Next Gaussian on [0,1) to use */
  static int have_gaussian = 0;    /* 1=next_gaussian contains valid data */

  /* Ensure our inputs are okay. */
  VALIDATE_FLOAT (mean);
  VALIDATE_FLOAT (stddev);

  /* Store a random Gaussian on [0,1) in GAUSSIAN. */
  if (have_gaussian) {
    /* Use the previously generated random number. */
    gaussian = next_gaussian;
    have_gaussian = 0;
  }
  else {
    double r1, r2;       /* Two random numbers from a uniform distribution */
    double hyp2;         /* The square of the length of the hypotenuse */
    double scalefact;    /* Scaling factor for the Gaussian distribution */

    /* Generate two new random numbers using the polar form of the
     * Box-Muller transformation. */
    do {
      r1 = 2.0 * ncptl_dfunc_random_uniform (0.0, 1.0) - 1.0;
      r2 = 2.0 * ncptl_dfunc_random_uniform (0.0, 1.0) - 1.0;
      hyp2 = r1*r1 + r2*r2;
    }
    while (hyp2 >= 1.0);
    scalefact = sqrt ((-2.0*log(hyp2)) / hyp2);
    gaussian = r1 * scalefact;
    next_gaussian = r2 * scalefact;
    have_gaussian = 1;
  }

  /* Return an appropriately scaled version of GAUSSIAN. */
  return gaussian*stddev + mean;
}


/* Return a randomly selected integer from a Poisson distribution with
 * mean MEAN and variance also MEAN.  Note that we're just using a
 * simple rejection algorithm whose time is linear in MEAN.  A
 * logarithmic-time algorithm (e.g., the one described in Knuth's
 * Seminumerical Algorithms) would be nice but is probably not
 * necessary, as random-number generation probably won't occur within
 * the timing loop, anyway. */
ncptl_int ncptl_func_random_poisson (ncptl_int mean)
{
  double expmean = exp (-(double)mean);
  double rnum = ncptl_dfunc_random_uniform (0.0, 1.0);
  ncptl_int result = 0;

  if (mean < 0)
    ncptl_fatal ("unable to take RANDOM_POISSON(%" NICS "); result is undefined", mean);
  while (rnum >= expmean) {
    result++;
    rnum *= ncptl_dfunc_random_uniform (0.0, 1.0);
  }
  return result;
}

/* Double version of the above */
double ncptl_dfunc_random_poisson (double mean)
{
  VALIDATE_FLOAT (mean);
  if (mean < 0.0)
    ncptl_fatal ("unable to take RANDOM_POISSON(%g); result is undefined", mean);
  return (double) ncptl_func_random_poisson ((ncptl_int) mean);
}


/* Return a randomly selected number from a Pareto distribution with
 * shape SHAPE and either bounds [LOW, HIGH] or scale LOW if LOW=HIGH. */
ncptl_int ncptl_func_random_pareto (ncptl_int shape, ncptl_int low, ncptl_int high)
{
  double rnum;

  /* Let the double version do all of the work. */
  do
    rnum = ncptl_dfunc_round(ncptl_dfunc_random_pareto((double)shape, (double)low, (double)high));
  while (rnum > (double)NCPTL_INT_MAX);
  return rnum;
}

/* Double version of the above */
double ncptl_dfunc_random_pareto (double shape, double low, double high)
{
  double urandnum;    /* Random number on the interval (0, 1) */

  VALIDATE_FLOAT (shape);
  VALIDATE_FLOAT (low);
  VALIDATE_FLOAT (high);
  if (shape <= 0.0 || low <= 0.0 || low > high)
    ncptl_fatal ("unable to take RANDOM_PARETO(%g, %g, %g); result is undefined",
                 shape, low, high);
  do
    urandnum = ncptl_dfunc_random_uniform(0.0, 1.0);
  while (urandnum == 0.0);
  if (low == high)
    /* Ordinary Pareto distribution */
    return low / ncptl_dfunc_power(urandnum, 1.0/shape);
  else {
    /* Bounded Pareto distribution */
    double high_shape = ncptl_dfunc_power(high, shape);
    double low_shape = ncptl_dfunc_power(low, shape);
    double num = urandnum*high_shape - urandnum*low_shape - high_shape;
    double den = high_shape * low_shape;
    return ncptl_dfunc_power(-num/den, -1.0/shape);
  }
}
