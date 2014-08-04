/* ----------------------------------------------------------------------
 *
 * Extra definitions needed by SWIG to properly wrap the coNCePTuaL
 * run-time library for use by scripting languages
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


/* The SWIG typemap interface changed completely circa version 1.3. */
#if defined(SWIG_VERSION) && SWIG_VERSION >= 0x010300
# define NEW_TYPEMAPS
#endif


/* ----------------
 * Global variables
 * ---------------- */
%{
/* Get access to the OS page size. */
extern int ncptl_pagesize;

/* Enable backends to initialize faster at the expense of getting
 * completely bogus timing measurements. */
extern int ncptl_fast_init;
%}


/* ----------------
 * Helper functions
 * ---------------- */

#ifdef SWIGPYTHON
%{
/* Used by various other functions to enable Python to pass either an
 * int or a long to a C function expecting an ncptl_int. */
static ncptl_int convert_python_integer_to_long_long (PyObject *pyinteger)
{
  if (PyInt_Check (pyinteger))
    return (ncptl_int) PyInt_AsLong (pyinteger);
  else
    return (ncptl_int) PyLong_AsLongLong (pyinteger);
}


/* Implement the body of the "(python, in) ncptl_int *ncptl_int_ARRAY"
 * typemap. */
static ncptl_int *construct_ncptl_int_array (PyObject *pyarray)
{
  ncptl_int *values;
  int numvalues = PyList_Size (pyarray);
  int i;

  values = (ncptl_int *) malloc (numvalues * sizeof(ncptl_int));
  for (i=0; i<numvalues; i++)
    values[i] = convert_python_integer_to_long_long (PyList_GetItem (pyarray, i));
  return values;
}


/* Implement the body of the "(python, freearg) ncptl_int
 * *ncptl_int_ARRAY" typemap. */
static void free_ncptl_int_array (PyObject *pytarget, ncptl_int *csource)
{
  int numvalues = PyList_Size (pytarget);
  int i;

  /* Before freeing the temporary ncptl_int list, first modify the
   * input list to reflect the new values that were assigned. */
  for (i=0; i<numvalues; i++)
    PyList_SetItem (pytarget, i, PyLong_FromLongLong (csource[i]));
  free (csource);
}


/* Implement the body of the "(python, in) NCPTL_CMDLINE *" typemap. */
static NCPTL_CMDLINE *construct_NCPTL_CMDLINE_array (PyObject *pycmdline)
{
  int numoptions;                     /* Number of command-line options */
  NCPTL_CMDLINE *option_list = NULL;  /* List of options to return */
  int i;

  /* Allocate space for the list of command-line options. */
  if (!PyList_Check (pycmdline)) {
    PyErr_SetString(PyExc_TypeError, "not a list");
    return NULL;
  }
  numoptions = PyList_Size (pycmdline);
  option_list = malloc ((numoptions+1) * sizeof(NCPTL_CMDLINE));
  memset (option_list, 0, numoptions * sizeof(NCPTL_CMDLINE));

  /* Convert each Python [varname, description, longname, shortname, value]
   * list to an NCPTL_CMDLINE.  Note that varname is currently ignored. */
  for (i=0; i<numoptions; i++) {
    PyObject *onestruct = PyList_GetItem (pycmdline, i);  /* One list element */
    PyObject *valuefield;    /* Value field (number or string) */
    PyObject *descfield;     /* Description of that value */
    PyObject *longfield;     /* Long (multi-character) command-line option */
    PyObject *shortfield;    /* Short (single-character) command-line option */

    /* Sanity-check our arguments. */
    if (!PyList_Check (onestruct)) {
      PyErr_SetString(PyExc_TypeError, "not a list");
      free (option_list);
      return NULL;
    }
    if (PyList_Size (onestruct) != 5) {
      PyErr_SetString(PyExc_TypeError, "list must be of length 5");
      free (option_list);
      return NULL;
    }

    /* Construct an NCPTL_CMDLINE out of onestruct. */
    descfield = PyList_GetItem (onestruct, 1);
    option_list[i].description = PyString_AsString (descfield);
    longfield = PyList_GetItem (onestruct, 2);
    option_list[i].longname = PyString_AsString (longfield);
    shortfield = PyList_GetItem (onestruct, 3);
    option_list[i].shortname = (PyString_AsString (shortfield))[0];
    valuefield = PyList_GetItem (onestruct, 4);
    if (PyLong_Check (valuefield) || PyInt_Check (valuefield)) {
      option_list[i].type = NCPTL_TYPE_INT;
      option_list[i].defaultvalue.intval = convert_python_integer_to_long_long (valuefield);
    }
    else if (PyString_Check (valuefield)) {
      option_list[i].type = NCPTL_TYPE_STRING;
      option_list[i].defaultvalue.stringval = PyString_AsString (valuefield);
    }
    else {
      PyErr_SetString(PyExc_TypeError, "not an integer or string");
      free (option_list);
      return NULL;
    }
    option_list[i].variable = &option_list[i].defaultvalue;
  }
  return option_list;
}


/* Implement the body of the "(python, free) NCPTL_CMDLINE *" typemap. */
static void free_NCPTL_CMDLINE_array (PyObject *pytarget, NCPTL_CMDLINE *csource)
{
  int numoptions;                     /* Number of command-line options */
  int i;

  /* Write the new values back to the variables. */
  numoptions = PyList_Size (pytarget);
  for (i=0; i<numoptions; i++) {
    PyObject *onestruct = PyList_GetItem (pytarget, i);  /* One list element */

    if (csource[i].type == NCPTL_TYPE_STRING)
      PyList_SetItem (onestruct, 4,
                      PyString_FromString (csource[i].variable->stringval));
    else
      if (csource[i].type == NCPTL_TYPE_INT)
        PyList_SetItem (onestruct, 4,
                        PyLong_FromLongLong (csource[i].variable->intval));
  }

  /* Free the memory we had allocated. */
  free ((void *) csource);
}


/* Implement the body of the "(python, in) char **" typemap.  This
 * code fragment was taken almost verbatim from the SWIG manual. */
static char **construct_string_array (PyObject *pyarray)
{
  char **carray;

  /* Check if is a list */
  if (PyList_Check(pyarray)) {
    int size = PyList_Size(pyarray);
    int i = 0;
    carray = (char **) malloc((size+1)*sizeof(char *));
    for (i = 0; i < size; i++) {
      PyObject *o = PyList_GetItem(pyarray,i);
      if (PyString_Check(o))
        carray[i] = PyString_AsString(PyList_GetItem(pyarray,i));
      else {
        PyErr_SetString(PyExc_TypeError,"list must contain strings");
        free(carray);
        return NULL;
      }
    }
    carray[i] = 0;
  } else {
    PyErr_SetString(PyExc_TypeError,"not a list");
    return NULL;
  }
  return carray;
}

%}
#endif


/* ------------------
 * Support for
 * variadic functions
 * ------------------ */

/* SWIG doesn't currently like stdarg functions.  ncptl_func_min(),
 * ncptl_func_max(), ncptl_dfunc_min(), and ncptl_dfunc_max() are too
 * trivial to bother with.  However, we can make ncptl_fatal() work by
 * preparing a wrapper function that accepts only a single argument.
 * The scripting language can deal with formatting that argument. */

%{
extern void ncptl_fatal (const char *, ...)
#ifdef __GNUC__
# if __GNUC__ > 2 || (__GNUC__ == 2 &&  __GNUC_MINOR__ >= 96)
  __attribute__((format (printf, 1, 2)))  /* Function is like printf(). */
  __attribute__((noreturn))               /* Function never returns. */
# endif
#endif
;

void ncptl_fatal_one_arg (char *error_message)
{
  ncptl_fatal ("%s", error_message);
}
%}

#if defined(SWIG_VERSION) && SWIG_VERSION >= 0x010300
%rename(ncptl_fatal) ncptl_fatal_one_arg;
extern void ncptl_fatal_one_arg (char *);
#else
%name(ncptl_fatal) extern void ncptl_fatal_one_arg (char *);
#endif   /* SWIG_VERSION >= 0x010300 */


/* ------------
 * Access to
 * timing flags
 * ------------ */

/* Enable scripting languages to allocate, clear, test, and free a
 * flag that can be passed to ncptl_set_flag_after_usecs(). */

%{
/* Allocate an int. */
int *ncptl_allocate_timing_flag (void)
{
  extern void *ncptl_malloc(ncptl_int, ncptl_int);
  int *flag = (int *) ncptl_malloc ((ncptl_int)sizeof(int), (ncptl_int)sizeof(int));
  *flag = 0;
  return flag;
}

/* Clear an int. */
void ncptl_reset_timing_flag (int *flag)
{
  *flag = 0;
}

/* Test an int. */
int ncptl_test_timing_flag (int *flag)
{
  return *flag;
}

/* Free an int. */
void ncptl_free_timing_flag (int *flag)
{
  extern void ncptl_free(void *);
  ncptl_free ((void *)flag);
}
%}

extern int *ncptl_allocate_timing_flag (void);
extern void ncptl_reset_timing_flag (int *);
extern int ncptl_test_timing_flag (int *);
extern void ncptl_free_timing_flag (int *);


/* ----------------
 * Python interface
 * to ncptl_int
 * ---------------- */

#ifdef NEW_TYPEMAPS

# ifdef SWIGPYTHON
%typemap (in) ncptl_int {
  $1 = convert_python_integer_to_long_long ($input);
}

%typemap (out) ncptl_int {
  $result = PyLong_FromLongLong ($1);
}

%typemap (in) ncptl_int *ncptl_int_ARRAY (PyObject *pyresult) {
  pyresult = $input;
  $1 = ($basetype *) construct_ncptl_int_array ($input);
}

%typemap (freearg) ncptl_int *ncptl_int_ARRAY {
  free_ncptl_int_array (pyresult$argnum, $1);
}
# endif   /* SWIGPYTHON */

#else   /* NEW_TYPEMAPS */

/* ncptl_int types should be passed by value, not by reference.  When
 * we do want to pass an ncptl_int by reference, we use a dummy formal
 * parameter called ncptl_int_ARRAY.  (Is there a better way to do
 * this?) */

%typemap (python, in) ncptl_int * (ncptl_int temp) {
  temp = convert_python_integer_to_long_long ($source);
  $target = ($basetype *) &temp;
}

%typemap (python, out) ncptl_int {
  $target = PyLong_FromLongLong (*$source);
}

%typemap (python, in) ncptl_int *ncptl_int_ARRAY {
  $target = ($basetype *) construct_ncptl_int_array ($source);
}

%typemap (python, freearg) ncptl_int *ncptl_int_ARRAY {
  free_ncptl_int_array ($target, $source);
}

#endif   /* NEW_TYPEMAPS */


/* Assume that uint64_t and int64_t should be treated the same as ncptl_int. */
%apply ncptl_int { uint64_t }
%apply ncptl_int { int64_t }


/* ----------------
 * Python interface
 * to NCPTL_CMDLINE
 * ---------------- */

/* Provide a hook that lets Python create a list of NCPTL_CMDLINE
 * structures which it can then pass to ncptl_log_write_prologue() or
 * ncptl_parse_command_line(). */

#ifdef NEW_TYPEMAPS

# ifdef SWIGPYTHON
%typemap (in) NCPTL_CMDLINE * (PyObject *pycmdline) {
  pycmdline = $input;
  $1 = construct_NCPTL_CMDLINE_array ($input);
}

%typemap (freearg) NCPTL_CMDLINE * {
  free_NCPTL_CMDLINE_array (pycmdline$argnum, $1);
}
# endif   /* SWIGPYTHON */

#else   /* NEW_TYPEMAPS */

%typemap (python, in) NCPTL_CMDLINE * {
  $target = construct_NCPTL_CMDLINE_array ($source);
}

%typemap (python, freearg) NCPTL_CMDLINE * {
  free_NCPTL_CMDLINE_array ($target, $source);
}

#endif   /* NEW_TYPEMAPS */


/* ----------------
 * Python interface
 * to char **
 * ---------------- */

#ifdef NEW_TYPEMAPS

# ifdef SWIGPYTHON
%typemap (in) char ** {
  $1 = construct_string_array ($input);
}

%typemap (freearg) char ** {
  free ((char *) $1);
}
# endif   /* SWIGPYTHON */

#else   /* NEW_TYPEMAPS */

%typemap (python, in) char ** {
  $target = construct_string_array ($source);
}

%typemap (python, freearg) char ** {
  free ((char *) $source);
}

#endif   /* NEW_TYPEMAPS */
