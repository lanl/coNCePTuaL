/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * routines for touching memory
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

#include "runtimelib.h"


/************************************
 * Imported variables and functions *
 ************************************/

extern unsigned long ncptl_genrand_int64(RNG_STATE *);
extern void ncptl_init_genrand(RNG_STATE *, uint64_t);
extern MESSAGE_MEM *ncptl_get_message_info (ncptl_int);
extern ncptl_int ncptl_get_num_nonuniques (void);



/************************************
 * Internal variables and functions *
 ************************************/

/* Touch a "word" that's bigger than any native datatype. */
static inline void touch_big_word (void *buffer, ncptl_int wordbytes)
{
  ncptl_int intsperword = wordbytes / sizeof(int);
  volatile int *intbuffer = (volatile int *) buffer;
  ncptl_int j;

  for (j=0; j<intsperword; j++)
    intbuffer[j]++;
}


/* Touch a set of "words" that don't wrap around a buffer. */
static inline void touch_multiple_words (void *bufferbegin, void *bufferend,
                                         ncptl_int wordbytes,
                                         ncptl_int bytestride,
                                         ncptl_int repetitions)
{
#define TOUCHLOOP(TYPE)                                                     \
    do {                                                                    \
      volatile TYPE *bufferptr;                                             \
      for (; repetitions>0; repetitions--)                                  \
        for (bufferptr = (volatile TYPE *)bufferbegin;                      \
             bufferptr < (volatile TYPE *)bufferend;                        \
             bufferptr=(volatile TYPE *)((uint8_t *)bufferptr+bytestride))  \
          ++*bufferptr;                                                     \
    }                                                                       \
    while (0)

    switch (wordbytes) {
      case 1:
        /* Byte */
        TOUCHLOOP (uint8_t);
        break;

      case 2:
        /* Halfword */
        TOUCHLOOP (uint16_t);
        break;

      case 4:
        /* Word */
        TOUCHLOOP (uint32_t);
        break;

      case 8:
        /* Doubleword */
        TOUCHLOOP (uint64_t);
        break;

#ifndef MUST_FAKE_UINT128
      case 16:
        /* Quadword */
        TOUCHLOOP (uint128_t);
        break;
#endif

      /* None of the above */
      default:
        do {
          char *bufferptr;

          for (; repetitions>0; repetitions--)
            for (bufferptr=(char *)bufferbegin;
                 bufferptr<(char *)bufferend;
                 bufferptr += bytestride)
              touch_big_word (bufferptr, wordbytes);
        }
        while (0);
        break;
    }
#undef TOUCHLOOP
}


/* Support ncptl_touch_memory()'s random walk over a memory region. */
static void touch_memory_randomly (void *buffer, ncptl_int bufferwords,
                                   ncptl_int wordbytes, ncptl_int numaccesses)
{
  static uint64_t seed = 0;      /* Seed for the random-number generator */
  static RNG_STATE touch_state;  /* Current state of the RNG */
  ncptl_int index;               /* Index into BUFFER */
  ncptl_int i;

#define TOUCHLOOP(TYPE)                                         \
  do {                                                          \
    for (i=0; i<numaccesses; i++) {                             \
      index  = (ncptl_int) ncptl_genrand_int64 (&touch_state);  \
      index %= bufferwords;                                     \
      index  = index<0 ? -index : index;                        \
      (((volatile TYPE *)buffer)[index])++;                     \
    }                                                           \
  }                                                             \
  while (0)

  /* Initialize the random-number generator our first time through. */
  if (!seed) {
    seed = (uint64_t) time (NULL);
    ncptl_init_genrand (&touch_state, seed);
  }

  /* Access the elements of BUFFER at random. */
  switch (wordbytes) {
    case 1:
      /* Byte */
      TOUCHLOOP (uint8_t);
      break;

    case 2:
      /* Halfword */
      TOUCHLOOP (uint16_t);
      break;

    case 4:
      /* Word */
      TOUCHLOOP (uint32_t);
      break;

    case 8:
      /* Doubleword */
      TOUCHLOOP (uint64_t);
      break;

#ifndef MUST_FAKE_UINT128
    case 16:
      /* Quadword */
      TOUCHLOOP (uint128_t);
      break;
#endif

    /* None of the above */
    default:
      do {
        /* If we were given a multiple of the native word size, then
         * use an inner loop to touch every word in each "big
         * word". */
        ncptl_int intsperword = wordbytes / sizeof(int);
        for (i=0; i<numaccesses; i++) {
          volatile int *intbuffer;
          ncptl_int j;

          /* Select an index to access. */
          index  = (ncptl_int) ncptl_genrand_int64(&touch_state);
          index %= bufferwords;
          index  = index<0 ? -index : index;

          /* Touch the "big word". */
          intbuffer =
            (volatile int *) ((volatile char *)buffer + index*wordbytes);
          for (j=0; j<intsperword; j++)
            intbuffer[j]++;
        }
      }
      while (0);
      break;
  }
#undef TOUCHLOOP
}


/* Touch the same "word" repeatedly. */
static void touch_memory_stride_zero (void *buffer, ncptl_int wordbytes,
                                      ncptl_int numaccesses)
{
  ncptl_int i;

#define TOUCHLOOP(TYPE)                                         \
  do {                                                          \
    volatile TYPE *typedbuffer = (volatile TYPE *) buffer;      \
    for (i=0; i<numaccesses; i++)                               \
      ++*typedbuffer;                                           \
  }                                                             \
  while (0)

  switch (wordbytes) {
    case 1:
      /* Byte */
      TOUCHLOOP (uint8_t);
      break;

    case 2:
      /* Halfword */
      TOUCHLOOP (uint16_t);
      break;

    case 4:
      /* Word */
      TOUCHLOOP (uint32_t);
      break;

    case 8:
      /* Doubleword */
      TOUCHLOOP (uint64_t);
      break;

#ifndef MUST_FAKE_UINT128
    case 16:
      /* Quadword */
      TOUCHLOOP (uint128_t);
      break;
#endif

    /* None of the above */
    default:
      for (i=0; i<numaccesses; i++)
        touch_big_word (buffer, wordbytes);
      break;
  }
#undef TOUCHLOOP
}


/* Support ncptl_touch_memory()'s strided walk over a memory region. */
static void touch_memory_strided (void *buffer, ncptl_int bufferbytes,
                                  ncptl_int wordbytes, ncptl_int firstbyte,
                                  ncptl_int numaccesses, ncptl_int bytestride)
{
  /* Force BYTESTRIDE into the range [0, BUFFERBYTES). */
  if (bytestride<0 || bytestride>=bufferbytes)
    bytestride = ncptl_func_modulo (bytestride, bufferbytes);

  /* We have two cases to contend with: nonzero BYTESTRIDE and zero
   * BYTESTRIDE */
  if (bytestride) {
    /* BYTESTRIDE is nonzero. */
    uint8_t *bytebuffer = (uint8_t *)buffer;      /* Byte version of BUFFER */
    void *bufferend = (void *) (bytebuffer + bufferbytes);  /* One byte past the end of the buffer */
    void *untouchable = (void *) ((uint8_t *)bufferend - wordbytes + 1);  /* One byte past where we can touch */
    uint8_t *firsttouch;          /* First byte to touch */
    uint8_t *lasttouch;           /* Last byte to touch */
    ncptl_int leftover_bytes = 0; /* # of bytes left over at the end of the buffer */

    /* Handle the case in which we never wrap around BUFFER. */
    firsttouch = bytebuffer + firstbyte;
    lasttouch = firsttouch + numaccesses*bytestride;
    if (firstbyte+numaccesses*(int64_t)bytestride+wordbytes-1 <= bufferbytes) {
      touch_multiple_words ((void *)firsttouch, (void *)lasttouch, wordbytes,
                            bytestride, 1);
      return;
    }

    /* Ensure we weren't given input that causes a single "word" to
     * wrap around BUFFER. */
    if (wordbytes > 1) {
      leftover_bytes = ((bufferbytes-firstbyte) % bytestride) % wordbytes;
      if (leftover_bytes)
	ncptl_fatal ("A touch operation extended past the end of the buffer");
    }

    /* Handle the case in which we wrap back to the beginning of BUFFER. */
    if (firstbyte%bytestride==0 && leftover_bytes==0) {
      ncptl_int accesses_left = numaccesses;    /* # of accesses remaining */
      ncptl_int complete_walks;                 /* # of touches of all of BUFFER */
      ncptl_int touches_per_buffer =            /* # of touches in a complete walk of BUFFER */
        ((uintptr_t)untouchable-(uintptr_t)bytebuffer+bytestride-1) / bytestride;

      /* Touch to the end of BUFFER. */
      touch_multiple_words ((void *)firsttouch, untouchable, wordbytes,
                            bytestride, 1);
      accesses_left -= ((uint8_t *)untouchable-firsttouch+bytestride-1) / bytestride;

      /* Wrap to the beginning of BUFFER and do some number of
       * complete walks. */
      complete_walks = accesses_left / touches_per_buffer;
      touch_multiple_words ((void *)bytebuffer, untouchable, wordbytes,
                            bytestride, complete_walks);

      /* Perform any touches we have remaining */
      accesses_left -= complete_walks * touches_per_buffer;
      touch_multiple_words ((void *)bytebuffer,
                            bytebuffer+accesses_left*bytestride,
                            wordbytes, bytestride, 1);
      return;
    }

    /* Handle the remaining case, in which we wrap but not to the
     * beginning of BUFFER. */
    do {
      ncptl_int accesses_left = numaccesses;    /* # of accesses remaining */
      ncptl_int touches_per_buffer;             /* # of touches in a complete walk of BUFFER */

      while (accesses_left) {
        touches_per_buffer = ((uintptr_t)untouchable-(uintptr_t)bytebuffer-firstbyte+bytestride-1) / bytestride;
        if (accesses_left >= touches_per_buffer) {
          /* Not the final pass */
          touch_multiple_words ((void *)(bytebuffer+firstbyte), untouchable,
                                wordbytes, bytestride, 1);
          accesses_left -= touches_per_buffer;
          firstbyte = (firstbyte + bytestride*touches_per_buffer) % (bufferbytes-wordbytes);
        }
        else {
          /* Final, partial pass */
          touch_multiple_words ((void *)(bytebuffer+firstbyte),
                                (void *)(bytebuffer+firstbyte+accesses_left*bytestride),
                                wordbytes, bytestride, 1);
          accesses_left = 0;
        }
      }
    }
    while (0);
  }
  else
    /* BYTESTRIDE is zero.  Just touch the same "word" NUMACCESSES times. */
    touch_memory_stride_zero ((void *)((char *)buffer+firstbyte),
                              wordbytes, numaccesses);
}


/************************************
 * Exported variables and functions *
 ************************************/

/* Touch every byte in a given message buffer. */
void ncptl_touch_data (void *buffer, ncptl_int numbytes)
{
  volatile int *intbuffer = (volatile int *) buffer;
  ncptl_int numwords = numbytes / sizeof(int);
  volatile char *charbuffer;
  ncptl_int numextrabytes = numbytes - numwords*sizeof(int);
  ncptl_int i;

  for (i=0; i<numwords; i++)
    *intbuffer++;
  charbuffer = (volatile char *)intbuffer;
  for (i=0; i<numextrabytes; i++)
    *charbuffer++;
}


/* Walk a memory region BUFFER of size BUFFERBYTES bytes.  Each "word"
 * to touch contains WORDBYTES bytes.  FIRSTBYTE indicates the byte
 * index into BUFFER from which to start touching.  The function will
 * read and write NUMACCESSES "words" with stride BYTESTRIDE bytes.  A
 * BYTESTRIDE of NCPTL_INT_MIN implies a random stride.  As a special
 * case, if FIRSTBYTE is -1, then ncptl_touch_memory() will touch one
 * or more message buffers instead of the given BUFFER.  In that case,
 * BUFFERBYTES stores the buffer number; if it's -1 then all message
 * buffers are touched.  All other parameters to ncptl_touch_memory()
 * are ignored. */
void ncptl_touch_memory (void *buffer, ncptl_int bufferbytes,
                         ncptl_int wordbytes, ncptl_int firstbyte,
                         ncptl_int numaccesses, ncptl_int bytestride)
{
  ncptl_int bufferwords;        /* # of words in BUFFER */

  /* If firstbyte is -1, this indicates that we're supposed to derive
   * many of the other parameters from message-buffer memory. */
  if (firstbyte == -1) {
    ncptl_int bufnum;           /* Buffer # in which we're interested */
    MESSAGE_MEM *message_info;  /* Size and address of buffer bufnum */

    firstbyte = 0;
    if (bufferbytes == -1) {
      /* Touch all bytes in all message buffers. */
      for (bufnum=ncptl_get_num_nonuniques()-1; bufnum>=0; bufnum--) {
        message_info = ncptl_get_message_info (bufnum);
	if (message_info && message_info->buffer)
	  ncptl_touch_data (message_info->buffer, message_info->bytes);
      }
    }
    else {
      /* Touch all bytes in a specific message buffer. */
      bufnum = bufferbytes;
      message_info = ncptl_get_message_info (bufnum);
      if (message_info && message_info->buffer)
	ncptl_touch_data (message_info->buffer, message_info->bytes);
    }
    return;
  }

  /* We touch a word at a time.  Abort if we're told to touch fewer
   * than one word. */
  if (wordbytes < 1)
    ncptl_fatal ("Memory-region walking cannot handle %" NICS "-byte accesses",
                 wordbytes);
  bufferwords = bufferbytes / wordbytes;

  /* Abort if the buffer size is negative. */
  if (bufferbytes < 0)
    ncptl_fatal ("Unable to touch a buffer of negative size (%" NICS " bytes)",
		 bufferbytes);

  /* Abort if we're trying to touch a "word" that's bigger than our
   * buffer. */
  if (wordbytes > bufferbytes)
    ncptl_fatal ("Unable to touch a word of %" NICS " bytes in a buffer that contains only %" NICS " bytes",
                 wordbytes, bufferbytes);

  /* Abort if our first "word" if out of bounds. */
  if (firstbyte<0 || firstbyte+wordbytes>bufferbytes)
    ncptl_fatal ("First word to touch is out of the bounds of the memory region");

  /* Abort if we're trying to touch a "word" of irregular size. */
  switch (wordbytes) {
    case 1:
    case 2:
    case 4:
    case 8:
#ifndef MUST_FAKE_UINT128
    case 16:
#endif
      break;

    default:
      if (wordbytes%sizeof(int) != 0)
        ncptl_fatal ("Memory-region walking cannot handle %" NICS "-byte accesses",
                     wordbytes);
      break;
  }

  /* Determine if we're supposed to touch data at random or with a
   * regular stride. */
  if (bytestride == NCPTL_INT_MIN)
    touch_memory_randomly (buffer, bufferwords, wordbytes, numaccesses);
  else
    touch_memory_strided (buffer, bufferbytes, wordbytes, firstbyte,
                          numaccesses, bytestride);
}
