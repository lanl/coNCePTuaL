/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * pseudorandom-number primitives (used internally)
 *
 * See authorship comments below.
 *
 * ----------------------------------------------------------------------
 */

/*
   A C-program for MT19937-64 (2004/9/29 version).
   Coded by Takuji Nishimura and Makoto Matsumoto.

   This is a 64-bit version of Mersenne Twister pseudorandom number
   generator.

   Before using, initialize the state by using init_genrand64(seed)
   or init_by_array64(init_key, key_length).

   Copyright (C) 2004, Makoto Matsumoto and Takuji Nishimura,
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

     1. Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

     2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

     3. The names of its contributors may not be used to endorse or promote
        products derived from this software without specific prior written
        permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
   A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

   References:
   T. Nishimura, ``Tables of 64-bit Mersenne Twisters''
     ACM Transactions on Modeling and
     Computer Simulation 10. (2000) 348--357.
   M. Matsumoto and T. Nishimura,
     ``Mersenne Twister: a 623-dimensionally equidistributed
       uniform pseudorandom number generator''
     ACM Transactions on Modeling and
     Computer Simulation 8. (Jan. 1998) 3--30.

   Any feedback is very welcome.
   http://www.math.hiroshima-u.ac.jp/~m-mat/MT/emt.html
   email: m-mat @ math.sci.hiroshima-u.ac.jp (remove spaces)
*/

#include <stdio.h>
#include "runtimelib.h"

/* Period parameters */
#define NN 312
#define MM 156
#define MATRIX_A UINT64_C(0xB5026F5AA96619E9)
#define UM UINT64_C(0xFFFFFFFF80000000)       /* Most significant 33 bits */
#define LM UINT64_C(0x7FFFFFFF)               /* Least significant 31 bits */

/* Primary modification by Scott Pakin: Store all state values in a
 * structure instead of retaining them globally. */
typedef struct {
  uint64_t mt[NN];     /* The array for the state vector */
  int mti;             /* mti==NN+1 means mt[NN] needs to be reinitialized */
} MT_STATE;


/* initializes mt[NN] with a seed */
void ncptl_init_genrand(MT_STATE *statevar, uint64_t seed)
{
  int mti;

  statevar->mt[0] = seed;
  for (mti=1; mti<NN; mti++)
    statevar->mt[mti] =  (UINT64_C(6364136223846793005) * (statevar->mt[mti-1] ^ (statevar->mt[mti-1] >> 62)) + mti);
  statevar->mti = mti;
}


/* initialize by an array with array-length */
/* init_key is the array for initializing keys */
/* key_length is its length */
void ncptl_init_by_array(MT_STATE *statevar, uint64_t init_key[], uint64_t key_length)
{
  unsigned long long i, j, k;

  ncptl_init_genrand(statevar, UINT64_C(19650218));
  i=1; j=0;
  k = (NN>key_length ? NN : key_length);
  for (; k; k--) {
    statevar->mt[i] = (statevar->mt[i] ^ ((statevar->mt[i-1] ^ (statevar->mt[i-1] >> 62)) * UINT64_C(3935559000370003845)))
      + init_key[j] + j; /* non linear */
    i++; j++;
    if (i>=NN) { statevar->mt[0] = statevar->mt[NN-1]; i=1; }
    if (j>=key_length) j=0;
  }
  for (k=NN-1; k; k--) {
    statevar->mt[i] = (statevar->mt[i] ^ ((statevar->mt[i-1] ^ (statevar->mt[i-1] >> 62)) * UINT64_C(2862933555777941757)))
      - i; /* non linear */
    i++;
    if (i>=NN) { statevar->mt[0] = statevar->mt[NN-1]; i=1; }
  }

  statevar->mt[0] = UINT64_C(1) << 63; /* MSB is 1; assuring non-zero initial array */
}


/* generates a random number on [0, 2^64-1]-interval */
uint64_t ncptl_genrand_int64 (MT_STATE *statevar)
{
  int i;
  uint64_t x;
  static uint64_t mag01[2] = {UINT64_C(0), MATRIX_A};

  if (statevar->mti >= NN) { /* generate NN words at one time */

    /* if init_genrand64() has not been called, */
    /* a default initial seed is used     */
    if (statevar->mti == NN+1)
      ncptl_init_genrand (statevar, UINT64_C(5489));

    for (i=0;i<NN-MM;i++) {
      x = (statevar->mt[i]&UM)|(statevar->mt[i+1]&LM);
      statevar->mt[i] = statevar->mt[i+MM] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];
    }
    for (;i<NN-1;i++) {
      x = (statevar->mt[i]&UM)|(statevar->mt[i+1]&LM);
      statevar->mt[i] = statevar->mt[i+(MM-NN)] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];
    }
    x = (statevar->mt[NN-1]&UM)|(statevar->mt[0]&LM);
    statevar->mt[NN-1] = statevar->mt[MM-1] ^ (x>>1) ^ mag01[(int)(x&UINT64_C(1))];

    statevar->mti = 0;
  }

  x = statevar->mt[statevar->mti++];

  x ^= (x >> 29) & UINT64_C(0x5555555555555555);
  x ^= (x << 17) & UINT64_C(0x71D67FFFEDA60000);
  x ^= (x << 37) & UINT64_C(0xFFF7EEE000000000);
  x ^= (x >> 43);

  return x;
}


/* generates a random number on [0, 2^63-1]-interval */
int64_t ncptl_genrand_int63 (MT_STATE *statevar)
{
  return (int64_t) (ncptl_genrand_int64(statevar) >> 1);
}


/* generates a random number on [0,1]-real-interval */
double ncptl_genrand_real1 (MT_STATE *statevar)
{
  return (ncptl_genrand_int64(statevar) >> 11) * (1.0/9007199254740991.0);
}


/* generates a random number on [0,1)-real-interval */
double ncptl_genrand_real2 (MT_STATE *statevar)
{
  return (ncptl_genrand_int64(statevar) >> 11) * (1.0/9007199254740992.0);
}


/* generates a random number on (0,1)-real-interval */
double ncptl_genrand64_real3 (MT_STATE *statevar)
{
  return ((ncptl_genrand_int64(statevar) >> 12) + 0.5) * (1.0/4503599627370496.0);
}


/* generates a random number on [0, 2^32-1]-interval */
uint32_t ncptl_genrand_int32 (MT_STATE *statevar)
{
  return (uint32_t) (ncptl_genrand_int64(statevar) & 0xFFFFFFFF);
}


/* generates a random number on [0,1) with 53-bit resolution*/
double ncptl_genrand_res53 (MT_STATE *statevar) 
{ 
  uint32_t a=ncptl_genrand_int32(statevar)>>5, b=ncptl_genrand_int32(statevar)>>6; 
  return(a*67108864.0+b)*(1.0/9007199254740992.0); 
} 
/* These real versions are due to Isaku Wada, 2002/01/09 added */
