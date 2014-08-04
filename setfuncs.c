/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * functions for manipulating unordered sets of data
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


/*********************
 * Type declarations *
 *********************/

/* Define a key:value type to use as one element in a set. */
typedef struct {
  void *key;
  void *value;
} NCPTL_SET_ELT;


/**********************
 * Internal functions *
 **********************/

/* Hash a key to an integer (a chain number). */
static uint64_t set_hash_key (const NCPTL_SET *set, const void *key)
{
  ncptl_int bytesremaining;           /* # of input bytes left to hash */
  const unsigned char *keychars;      /* Pointer into the key bytes */
  uint64_t hashvalue = 0;             /* Resulting hash value */
  const uint64_t bigprime1 = 6678383;
  const uint64_t bigprime2 = 6618401;

  /* Multiply each byte by one prime and add a second prime. */
  for (bytesremaining=set->keybytes, keychars=(const unsigned char *)key;
       bytesremaining;
       bytesremaining--, keychars++)
    hashvalue += *keychars*bigprime1 + bigprime2;
  return (uint64_t) (hashvalue % set->numchains);
}


/**********************
 * Exported functions *
 **********************/

/* Initialize an unordered set. */
NCPTL_SET *ncptl_set_init (ncptl_int numchains, ncptl_int keybytes, ncptl_int valuebytes)
{
  NCPTL_SET *newset = (NCPTL_SET *) ncptl_malloc (sizeof(NCPTL_SET), 0);

  newset->numchains = numchains;
  newset->keybytes = keybytes;
  newset->valuebytes = valuebytes;
  newset->numelts = 0;
  newset->chains = (NCPTL_QUEUE **) NULL;
  return newset;
}


/* Given a key, return a pointer to the corresponding value or NULL if
 * the key is not found. */
void *ncptl_set_find (NCPTL_SET *set, void *key)
{
  NCPTL_QUEUE *chain;         /* Pointer to the bucket chain containing KEY */
  NCPTL_SET_ELT *chaindata;   /* Array of buckets */
  ncptl_int i;

  /* If the set is empty there's no point searching it. */
  if (!set->chains)
    return NULL;

  /* Linear-search the bucket chain. */
  chain = set->chains[set_hash_key(set, key)];
  chaindata = (NCPTL_SET_ELT *) ncptl_queue_contents (chain, 0);
  for (i=0; i<ncptl_queue_length(chain); i++)
    if (!memcmp(key, chaindata[i].key, set->keybytes)) {
      if (i > 0) {
	/* For performance, bubble up the element we just found. */
	NCPTL_SET_ELT prevelt = chaindata[i-1];
	chaindata[i-1] = chaindata[i];
	chaindata[i] = prevelt;
	return chaindata[i-1].value;
      }
      else
	return chaindata[i].value;
    }
  return NULL;
}


/* Insert a copy of a key:value pair into a set.  Abort if the key is
 * already in the set. */
void ncptl_set_insert (NCPTL_SET *set, void *key, void *value)
{
  NCPTL_QUEUE *chain;  /* Bucket chain in which to insert the key:value pair */
  NCPTL_SET_ELT newelt;  /* key:value pair to insert */
  
  if (ncptl_set_find (set, key))
    ncptl_fatal ("internal error -- ncptl_set_insert() inserted the same key twice");
  if (!set->chains) {
    /* This is the first invocation since set creation/emptying --
     * allocate all of the bucket chains. */
    ncptl_int i;
    set->chains = (NCPTL_QUEUE **) ncptl_malloc (set->numchains*sizeof(NCPTL_QUEUE *), 0);
    for (i=0; i<set->numchains; i++)
      set->chains[i] = ncptl_queue_init (sizeof(NCPTL_SET_ELT));
  }
  chain = set->chains[set_hash_key(set, key)];
  newelt.key = ncptl_malloc (set->keybytes, 0);
  memcpy (newelt.key, key, set->keybytes);
  newelt.value = ncptl_malloc (set->valuebytes, 0);
  memcpy (newelt.value, value, set->valuebytes);
  ncptl_queue_push (chain, &newelt);
  set->numelts++;
}


/* Invoke a user-defined function for every key:value pair in a set. */
void ncptl_set_walk (NCPTL_SET *set, void (*userfunc)(void *, void *))
{
  ncptl_int i;

  if (!set->chains)
    return;
  for (i=0; i<set->numchains; i++) {
    NCPTL_SET_ELT *chaindata = (NCPTL_SET_ELT *) ncptl_queue_contents (set->chains[i], 0);
    ncptl_int j;

    for (j=ncptl_queue_length (set->chains[i])-1; j>=0; j--)
      (*userfunc)(chaindata[j].key, chaindata[j].value);
  }
}


/* Given a key, remove the corresponding key:value pair from a set.
 * Abort if the key is not in the set. */
void ncptl_set_remove (NCPTL_SET *set, void *key)
{
  if (set->chains) {
    NCPTL_QUEUE *chain = set->chains[set_hash_key(set, key)];
    NCPTL_SET_ELT *chaindata = (NCPTL_SET_ELT *) ncptl_queue_contents (chain, 0);
    ncptl_int numelts = ncptl_queue_length(chain);
    ncptl_int i;

    for (i=0; i<numelts; i++)
      if (!memcmp(key, chaindata[i].key, set->keybytes)) {
	/* Move the element to the head of the queue then pop the queue. */
	if (i > 0) {
	  NCPTL_SET_ELT firstelt = chaindata[0];
	  chaindata[0] = chaindata[i];
	  chaindata[i] = firstelt;
	}
	ncptl_free (chaindata[0].key);
	ncptl_free (chaindata[0].value);
	(void) ncptl_queue_pop (chain);
	set->numelts--;
	return;
      }
  }
  ncptl_fatal ("internal error -- ncptl_set_remove() tried to remove a nonexistent key");
}


/* Empty a set, freeing the memory it had previously used. */
void ncptl_set_empty (NCPTL_SET *set)
{
  ncptl_int i;

  if (!set->chains)
    return;
  for (i=0; i<set->numchains; i++) {
    NCPTL_SET_ELT *chaindata = (NCPTL_SET_ELT *) ncptl_queue_contents (set->chains[i], 0);
    ncptl_int j;

    for (j=ncptl_queue_length (set->chains[i])-1; j>=0; j--) {
      ncptl_free (chaindata[j].key);
      ncptl_free (chaindata[j].value);
    }
    ncptl_queue_empty (set->chains[i]);
  }
  ncptl_free (set->chains);
  set->chains = NULL;
  set->numelts = 0;
}
