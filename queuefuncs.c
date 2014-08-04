/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * functions for manipulating dynamically growing queues
 *
 * By Scott Pakin <pakin@lanl.gov>
 *
 * ----------------------------------------------------------------------
 *
 * Copyright (C) 2014, Los Alamos National Security, LLC
 * All rights reserved.
 * 
 * Copyright (2014).  Los Alamos National Security, LLC.  This software
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

/* Align to a given number of bytes rounded down to a multiple of
 * CPU_MINIMUM_ALIGNMENT_BYTES. */
#define ALIGN_NICELY(P) (CPU_MINIMUM_ALIGNMENT_BYTES*((P)/CPU_MINIMUM_ALIGNMENT_BYTES))


/**********************
 * Exported functions *
 **********************/

/* Initialize a dynamically growing queue. */
NCPTL_QUEUE *ncptl_queue_init (ncptl_int eltbytes)
{
  NCPTL_QUEUE *newqueue = (NCPTL_QUEUE *) ncptl_malloc (sizeof(NCPTL_QUEUE), 0);

  newqueue->eltbytes = eltbytes;
  newqueue->alloced = 0;
  newqueue->used = 0;
  newqueue->head = 0;
  newqueue->array = NULL;
  return newqueue;
}


/* Allocate a new data element at the end of a queue. */
void *ncptl_queue_allocate (NCPTL_QUEUE *queue)
{
  /* The first time through we allocate some initial memory. */
  if (!queue->alloced) {
    queue->alloced = 16;     /* Arbitrary number to start with */
    queue->array = (void *) ncptl_malloc (queue->eltbytes * queue->alloced,
                                          ALIGN_NICELY(queue->eltbytes));
  }

  /* Allocate more elements if we're short. */
  if (queue->alloced == queue->used) {
    queue->alloced *= 2;     /* Allocate twice as many events as before. */
    queue->array =
      (void *) ncptl_realloc (queue->array,
                              queue->eltbytes * queue->alloced,
                              ALIGN_NICELY(queue->eltbytes));
  }

  /* Return a pointer into the dynamically allocated array. */
  return (void *) ((char *)queue->array + queue->eltbytes*queue->used++);
}


/* Return the queue as an array of elements, optionally copying them
 * to new memory. */
void *ncptl_queue_contents (NCPTL_QUEUE *queue, int copyelts)
{
  if (queue->array == NULL)
    return NULL;
  else {
    void *arraystart =
      (void *) ((char *)queue->array + queue->eltbytes*queue->head);

    if (copyelts) {
      ncptl_int numbytes = (queue->used - queue->head) * queue->eltbytes;
      void *datacopy = ncptl_malloc (numbytes, ALIGN_NICELY(queue->eltbytes));
      memcpy (datacopy, arraystart, (size_t)numbytes);
      return datacopy;
    }
    else
      return arraystart;
  }
}


/* Empty a queue, freeing the memory it had previously used. */
void ncptl_queue_empty (NCPTL_QUEUE *queue)
{
  if (queue->array)
    ncptl_free (queue->array);
  queue->array = NULL;
  queue->alloced = 0;
  queue->used = 0;
  queue->head = 0;
}


/* Pop a value from a queue.  Return NULL if the queue is empty.  The
 * returned memory remains valid until the next invocation of
 * ncptl_queue_empty(). */
void *ncptl_queue_pop (NCPTL_QUEUE *queue)
{
  if (queue->head == queue->used)
    return NULL;
  else
    return (void *) ((char *)queue->array + queue->eltbytes*queue->head++);
}


/* Pop a value from the tail of a queue.  Return NULL if the queue is
 * empty.  The returned memory remains valid until the next invocation
 * of ncptl_queue_empty(), ncptl_queue_allocate(), or
 * ncptl_queue_push(). */
void *ncptl_queue_pop_tail (NCPTL_QUEUE *queue)
{
  if (queue->head == queue->used)
    return NULL;
  else
    return (void *) ((char *)queue->array + queue->eltbytes*--queue->used);
}


/* Given two compatible queues (same element size), push all elements
 * of the second queue onto the first queue.  The second queue is left
 * unmodified. */
void ncptl_queue_push_all (NCPTL_QUEUE *targetQ, NCPTL_QUEUE *sourceQ)
{
  ncptl_int numnewelts;    /* Number of new elements to push onto targetQ */
  void *firstnewelt;       /* Pointer to the first new element in targetQ */
  ncptl_int i;

  /* Validate our arguments. */
  if (targetQ->eltbytes != sourceQ->eltbytes)
    ncptl_fatal("ncptl_queue_push_all() requires compatible queues (%" NICS " vs. %" NICS ")",
                targetQ->eltbytes, sourceQ->eltbytes);
  numnewelts = sourceQ->used;
  if (numnewelts == 0)
    return;

  /* Allocate space for numnewelts new elements. */
  firstnewelt = ncptl_queue_allocate(targetQ);
  for (i=1; i<numnewelts; i++)
    ncptl_queue_allocate(targetQ);

  /* Copy all elements en masse. */
  memcpy(firstnewelt, ncptl_queue_contents(sourceQ, 0), numnewelts*sourceQ->eltbytes);
}
