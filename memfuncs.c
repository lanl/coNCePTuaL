/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * functions for allocating and freeing heap memory
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


/*********************
 * Type declarations *
 *********************/

/* Define a type for a structure that stores information about a
 * heap-allocated memory region. */
typedef struct {
  uint64_t cookie;         /* Arbitrary number used for sanity-checking */
  ncptl_int buffer_size;   /* # of bytes requested from ncptl_malloc(), etc. */
  ncptl_int alloc_size;    /* # of bytes requested from malloc()/realloc() */
  void *buffer_pointer;    /* Pointer returned by malloc()/realloc() */
} ALLOCINFO;


/************************************
 * Internal variables and functions *
 ************************************/

/* Array of recyclable buffers */
static MESSAGE_MEM *nonunique = NULL;

/* # of entries in the above */
static ncptl_int num_nonuniques = 0;

/* Bytes of memory we currently have and ever had allocated */
static ncptl_int current_memory_allocation = UINT64_C(0);
static ncptl_int peak_memory_allocation = UINT64_C(0);



/* Given a buffer allocated with malloc() or realloc(), store the
 * buffer address in the first word of the buffer and return a pointer
 * to the second word.  This way, the memory is suitably aligned yet
 * can still be freed with ncptl_free(). */
static void *align_malloced_memory (void *malloced_buffer,
                                    ncptl_int numbytes,
                                    ncptl_int alignment,
                                    ncptl_int padded_numbytes)
{
  void *buffer = malloced_buffer;   /* Address to return to the caller */
  ALLOCINFO *allocinfo;             /* Information needed by realloc() and free() */

  /* Align the buffer appropriately and store the address we'll need
   * to free(). */
  if (alignment < CPU_MINIMUM_ALIGNMENT_BYTES)
    alignment = CPU_MINIMUM_ALIGNMENT_BYTES;
  if (alignment % CPU_MINIMUM_ALIGNMENT_BYTES)
    ncptl_fatal ("The %s cpu cannot align data on a %" NICS "-byte boundary",
                 CPU_TYPE, alignment);
  buffer = (void *) ((char *)buffer + alignment + sizeof(ALLOCINFO));
  if (alignment)
    buffer = (void *) ((uintptr_t)alignment * ((uintptr_t)buffer/(uintptr_t)alignment));
  allocinfo = ((ALLOCINFO *)buffer) - 1;
  allocinfo->cookie = ALLOC_MAGIC_COOKIE;
  allocinfo->buffer_size = numbytes;
  allocinfo->alloc_size = padded_numbytes;
  allocinfo->buffer_pointer = malloced_buffer;

  /* Return the newly allocated memory. */
  return buffer;
}


/****************************
 * Library-global functions *
 ****************************/

/* Given OUTSTANDING as defined in the comments to
 * ncptl_malloc_message(), return the corresponding buffer information
 * (pointer and byte count). */
MESSAGE_MEM *ncptl_get_message_info (ncptl_int outstanding)
{
  /* Out-of-bound buffer numbers take no space. */
  if (outstanding < 0)
    return (MESSAGE_MEM *)NULL;
  if (outstanding >= num_nonuniques)
    return (MESSAGE_MEM *)NULL;

  /* Return information about buffer #outstanding. */
  return &nonunique[outstanding];
}


/* Return the number of buffers for non-unique messages. */
ncptl_int ncptl_get_num_nonuniques (void)
{
  return num_nonuniques;
}


/* Return the peak number of bytes allocated at any given time. */
ncptl_int ncptl_get_peak_memory_usage (void)
{
  return (ncptl_int) peak_memory_allocation;
}


/* Concatenate a list of strings with intervening spaces.  The caller
 * must ncptl_free() the result.  If and only if all inputs are NULL
 * will ncptl_concatenate_strings() return NULL. */
char *ncptl_concatenate_strings (ncptl_int numstrings, ...)
{
  va_list arglist;           /* Variadic argument list */
  char *onestring;           /* The current argument string */
  char *finalstring = NULL;  /* Concatenation of all strings */
  ncptl_int stringlen = 0;   /* Length of the string so far */
  ncptl_int i;

  va_start (arglist, numstrings);
  for (i=0; i<numstrings; i++) {
    onestring = va_arg (arglist, char *);
    if (!onestring)
      continue;
    if (finalstring) {
      ncptl_int onestringlen = strlen (onestring);

      finalstring = ncptl_realloc (finalstring, stringlen+onestringlen+2, 0);
      sprintf (finalstring+stringlen, " %s", onestring);
      stringlen += onestringlen + 1;
    }
    else {
      finalstring = ncptl_strdup (onestring);
      stringlen = strlen (finalstring);
    }
  }
  va_end (arglist);
  return finalstring;
}


/**********************
 * Exported functions *
 **********************/

/* Allocate NUMBYTES bytes of memory from the heap with alignment
 * ALIGNMENT bytes or 0 for the the default alignment. */
void *ncptl_malloc (ncptl_int numbytes, ncptl_int alignment)
{
  void *malloced_buffer;   /* Address received from malloc() */
  ncptl_int padded_numbytes;  /* Data bytes + metadata bytes + padding */

  /* Even though the system may be capable of arbitrary alignment, we
   * may get better performance by aligning on a larger boundary. */
  if (!alignment)
    alignment = sizeof(ncptl_int);

  /* Allocate the number of bytes requested plus enough additional
   * memory for padding and for storing the unpadded address. */
  padded_numbytes =
    numbytes
    + (alignment<CPU_MINIMUM_ALIGNMENT_BYTES ? CPU_MINIMUM_ALIGNMENT_BYTES : alignment)
    + sizeof(ALLOCINFO);
  malloced_buffer = malloc0 (padded_numbytes);
  if (!malloced_buffer) {
    if (alignment)
      ncptl_fatal ("Failed to allocate %" NICS " %" NICS "-byte aligned bytes",
                   numbytes, alignment);
    else
      ncptl_fatal ("Failed to allocate %" NICS " unaligned bytes", numbytes);
  }
  current_memory_allocation += (uint64_t) padded_numbytes;
  if (peak_memory_allocation < current_memory_allocation)
    peak_memory_allocation = current_memory_allocation;

  /* Return to the caller an aligned version of the buffer. */
  return align_malloced_memory (malloced_buffer, numbytes, alignment, padded_numbytes);
}


/* Free memory previously allocated by ncptl_malloc().  BUFFER may be
 * different from what libc returned.  However, we wisely saved the
 * original libc address at a known location.  Like free(),
 * ncptl_free() does nothing when given a NULL pointer. */
void ncptl_free (void *buffer)
{
  ALLOCINFO *allocinfo = (ALLOCINFO *)buffer - 1;

  if (!buffer)
    return;
  if (allocinfo->cookie != ALLOC_MAGIC_COOKIE)
    ncptl_fatal ("Attempted to ncptl_free() memory not allocated with ncptl_malloc()");
  current_memory_allocation -= (uint64_t) allocinfo->alloc_size;
  free (allocinfo->buffer_pointer);
}


/* Reallocate NUMBYTES bytes of memory from the heap with alignment
 * ALIGNMENT bytes or 0 for the the default alignment. */
void *ncptl_realloc (void *oldbuffer, ncptl_int numbytes, ncptl_int alignment)
{
  void *realloced_buffer;     /* Address received from realloc() */
  ncptl_int padded_numbytes;  /* Data bytes + metadata bytes + padding */
  ALLOCINFO oldinfo;          /* Information about the previous buffer */

  /* Reallocating a null pointer merely passes control to
   * ncptl_malloc(). */
  if (!oldbuffer)
    return ncptl_malloc (numbytes, alignment);

  /* Store whatever information we need from the old buffer before it
   * goes away. */
  oldinfo = ((ALLOCINFO *)oldbuffer)[-1];
  if (oldinfo.cookie != ALLOC_MAGIC_COOKIE)
    ncptl_fatal ("Attempted to ncptl_realloc() memory not allocated with ncptl_malloc()");

  /* Even though the system may be capable of arbitrary alignment, we
   * may get better performance by aligning on a larger boundary. */
  if (!alignment)
    alignment = sizeof(ncptl_int);

  /* Allocate the number of bytes requested plus enough additional
   * memory for padding and for storing the unpadded address. */
  padded_numbytes =
    numbytes
    +(alignment<CPU_MINIMUM_ALIGNMENT_BYTES ? CPU_MINIMUM_ALIGNMENT_BYTES : alignment)
    + sizeof(ALLOCINFO);
  realloced_buffer = realloc0 (oldinfo.buffer_pointer, padded_numbytes);
  if (!realloced_buffer) {
    if (alignment)
      ncptl_fatal ("Failed to allocate %" NICS " %" NICS "-byte aligned bytes",
                   numbytes, alignment);
    else
      ncptl_fatal ("Failed to allocate %" NICS " unaligned bytes", numbytes);
  }
  current_memory_allocation += (uint64_t) padded_numbytes;
  current_memory_allocation -= (uint64_t) oldinfo.alloc_size;
  if (peak_memory_allocation < current_memory_allocation)
    peak_memory_allocation = current_memory_allocation;

  /* If the buffer's alignment changed, we need to copy the data
   * explicitly because it'll otherwise not be located at offset 0 of
   * the buffer we plan to return to the caller. */
  if (alignment < CPU_MINIMUM_ALIGNMENT_BYTES)
    alignment = CPU_MINIMUM_ALIGNMENT_BYTES;
  if ((uintptr_t)realloced_buffer%alignment !=
      (uintptr_t)oldinfo.buffer_pointer % alignment) {
    void *newbuffer = ncptl_malloc (numbytes, alignment);
    memcpy (newbuffer,
            (void *)((char *)realloced_buffer +
                     (uintptr_t)oldbuffer - (uintptr_t)oldinfo.buffer_pointer),
            numbytes<oldinfo.buffer_size ? numbytes : oldinfo.buffer_size);
    current_memory_allocation -= (uint64_t) padded_numbytes;
    free (realloced_buffer);
    return newbuffer;
  }

  /* Return to the caller an aligned version of the buffer. */
  return align_malloced_memory (realloced_buffer, numbytes, alignment, padded_numbytes);
}


/* Provide the same functionality as strdup() but use ncptl_malloc()
 * instead of malloc() to allocate memory.  This way, we can
 * consistently call ncptl_free() everywhere instead of sometimes
 * requiring ordinary free(). */
char *ncptl_strdup (const char *instring)
{
  size_t numbytes = strlen (instring);
  char *outstring = (char *) ncptl_malloc (numbytes+1, 0);

  return strcpy (outstring, instring);
}


/* Allocate NUMBYTES of memory from the heap aligned on an
 * ALIGNMENT-byte boundary (if MISALIGNED is 0) or ALIGNMENT bytes
 * past a page boundary (if MISALIGNED is 1).  All calls with the same
 * value of OUTSTANDING will share a buffer.  ncptl_malloc_message()
 * is intended to be used in two passes.  The first time the function
 * is called on a set of messages it determines how much memory to
 * allocate.  The second time, it returns valid memory buffers.  Note
 * that the returned pointer can be neither free()'d nor
 * ncptl_free()'d. */
void *ncptl_malloc_message (ncptl_int numbytes,
                            ncptl_int alignment,
                            ncptl_int outstanding,
                            int misaligned)
{
  MESSAGE_MEM *thismsg;                  /* Pointer into NONUNIQUE */
  ncptl_int truebytes;         /* # of bytes to allocate for this message */
  ncptl_int i;

  /* Ensure that ALIGNMENT is valid and that OUTSTANDING is nonnegative. */
  if (misaligned) {
    /* Put ALIGNMENT within the range [0, ncptl_pagesize). */
    if ((alignment = alignment % ncptl_pagesize) < 0)
      alignment += ncptl_pagesize;
  }
  else {
    if (!alignment)
      alignment = CPU_MINIMUM_ALIGNMENT_BYTES;
    if (alignment < 0)
      ncptl_fatal ("Negative message alignments (%" NICS ") are not allowed",
                   alignment);
  }
  if (alignment % CPU_MINIMUM_ALIGNMENT_BYTES)
    ncptl_fatal ("The %s cpu cannot align data on a %" NICS "-byte boundary",
                 CPU_TYPE, alignment);
  if (outstanding < 0)
    ncptl_fatal ("Negative offset (%" NICS ") was passed to ncptl_malloc_message()",
                 outstanding);

  /* Allocate recyclable message state. */
  if (outstanding >= num_nonuniques) {
    ncptl_int old_num_nonuniques = num_nonuniques;   /* Preserve the previous value. */
    num_nonuniques = 2*outstanding + 1;
    nonunique =
      (MESSAGE_MEM *) ncptl_realloc (nonunique,
                                     num_nonuniques * sizeof(MESSAGE_MEM),
                                     0);
    for (i=old_num_nonuniques; i<num_nonuniques; i++) {
      nonunique[i].buffer = NULL;
      nonunique[i].bytes = -1;
    }
  }

  /* Recycle or allocate memory for a single message and return a
   * suitably aligned version of the memory.  Note that we don't
   * specify an alignment to ncptl_realloc() but rather compute the
   * aligned offset manually.  This enables us to reuse the same
   * buffer but return it with a different alignment on each call. */
  thismsg = &nonunique[outstanding];
  truebytes = numbytes + alignment + (misaligned ? ncptl_pagesize : 0) - 1;
  if (truebytes > thismsg->bytes) {
    /* We need more memory for message OUTSTANDING. */
    thismsg->bytes = truebytes;
    thismsg->buffer = (void *) ncptl_realloc (thismsg->buffer, thismsg->bytes, 0);
  }
#define NCPTL_CEIL_DIV(N,D) (((((N)%(D))!=0) + (N)/(D)) * (D))
  if (misaligned)
    return (void *) (alignment
                     + (char *) NCPTL_CEIL_DIV ((uintptr_t)thismsg->buffer,
                                                (uintptr_t)ncptl_pagesize));
  else
    return (void *) NCPTL_CEIL_DIV ((uintptr_t)thismsg->buffer, (uintptr_t)alignment);
#undef NCPTL_CEIL_DIV
}


/* Allocate NUMBYTES bytes of memory from the heap aligned ALIGNMENT
 * bytes from a page boundary. */
void *ncptl_malloc_misaligned (ncptl_int numbytes, ncptl_int alignment)
{
  void *malloced_buffer;      /* Address received from malloc() */
  void *buffer;               /* Address to return to the caller */
  ncptl_int padded_numbytes;  /* Data bytes + metadata bytes + padding */
  ALLOCINFO *allocinfo;       /* Information needed by realloc() and free() */

  /* Sanity check the alignment. */
  if (alignment % CPU_MINIMUM_ALIGNMENT_BYTES)
    ncptl_fatal ("The %s cpu cannot align data on a %" NICS "-byte boundary",
                 CPU_TYPE, alignment);
  if ((alignment = alignment % ncptl_pagesize) < 0)
    alignment += ncptl_pagesize;

  /* Allocate the number of bytes requested plus enough additional
   * memory for padding and for storing the unpadded address. */
  padded_numbytes =
    numbytes
    + ncptl_pagesize
    + alignment
    + sizeof(ALLOCINFO);
  malloced_buffer = malloc0 (padded_numbytes);
  if (!malloced_buffer)
    ncptl_fatal ("Failed to allocate %" NICS " %" NICS "-byte misaligned bytes",
                 numbytes, alignment);
  current_memory_allocation += (uint64_t) padded_numbytes;
  if (peak_memory_allocation < current_memory_allocation)
    peak_memory_allocation = current_memory_allocation;

  /* Return to the caller a suitably misaligned version of the buffer. */
  buffer = (void *) ((char *)malloced_buffer + ncptl_pagesize + sizeof(ALLOCINFO));
  buffer = (void *) ((uintptr_t)ncptl_pagesize * ((uintptr_t)buffer/(uintptr_t)ncptl_pagesize));
  buffer = (void *) ((char *)buffer + alignment);
  allocinfo = ((ALLOCINFO *)buffer) - 1;
  allocinfo->cookie = ALLOC_MAGIC_COOKIE;
  allocinfo->buffer_size = numbytes;
  allocinfo->alloc_size = padded_numbytes;
  allocinfo->buffer_pointer = malloced_buffer;

  /* Return the newly allocated memory. */
  return buffer;
}


/* Given a message-buffer number, return a pointer to the
 * corresponding buffer data or NULL if the message buffer has not
 * been initialized. */
void *ncptl_get_message_buffer (ncptl_int buffernum)
{
  /* Out-of-bound buffer numbers take no space. */
  if (buffernum < 0)
    return NULL;
  if (buffernum >= num_nonuniques)
    return NULL;

  /* Return a pointer to buffer #buffernum.  (Note: may be NULL). */
  return nonunique[buffernum].buffer;
}
