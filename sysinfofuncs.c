/* ----------------------------------------------------------------------
 *
 * coNCePTuaL run-time library:
 * internal functions for acquiring system information
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

/* For convenience, combine multiple #if checks into one. */
#if defined(HAVE_INVENT_H) && defined(HAVE_GETINVENT)
# define GETINVENT_OKAY
#endif
#if defined(HAVE_SYS_SYSMP_H) && defined(HAVE_SYSMP)
# define SYSMP_OKAY
#endif

/* Assign a variable unless it's already been assigned. */
#define ASSIGN(LHS,RHS) LHS = (LHS) ? (LHS) : (RHS)


/************************************
 * Imported variables and functions *
 ************************************/

extern char *ncptl_concatenate_strings (ncptl_int numstrings, ...);
extern int ncptl_fork_works;

/************************************
 * Internal variables and functions *
 ************************************/

#ifdef HAVE_BGLPERSONALITY
/* Store the personality of the BG/L partition. */
BGLPersonality ncptl_bgl_personality;
#endif

#ifdef HAVE_BGPPERSONALITY
/* Store the personality of the BG/P partition. */
_BGP_Personality_t ncptl_bgp_personality;
#endif

#ifdef HAVE_PCIUTILS
/* Note if an error occurred while processing the PCI bus. */
int pciutils_error = 0;
#endif


/* Given a "key : value\n" string, copy and return key. */
static char *extract_key (char *key_value)
{
  char *eos;
  char *result = ncptl_strdup (key_value);

  for (eos=strchr(result, ':'); eos>=result && isspace((int)eos[-1]); eos--)
    eos[-1] = '\0';
  return result;
}


/* Given a "key : value\n" string, copy and return value. */
static char *extract_value (char *key_value)
{
  char *colonptr = strchr (key_value, ':');
  char *result = ncptl_strdup (colonptr+2);
  result[strlen(result)-1] = '\0';    /* Remove the newline character */
  return result;
}


/* Read and return the first NCPTL_MAX_LINE_LEN bytes of a given file
 * or NULL on failure.  If is_binary is set, do no extra processing.
 * If is_binary is not set, truncate the text at the first newline
 * character. */
static char *read_first_line (char *filename, int is_binary)
{
  FILE *fh;
  char *oneline;
  char *c;

  if (!(fh = fopen(filename, is_binary ? "rb" : "r")))
    return NULL;
  oneline = ncptl_malloc(NCPTL_MAX_LINE_LEN+1, 0);
  memset(oneline, 0, NCPTL_MAX_LINE_LEN+1);
  if (fread(oneline, 1, NCPTL_MAX_LINE_LEN, fh) == 0) {
    /* Treat a read of zero bytes as a failure. */
    fclose(fh);
    ncptl_free(oneline);
    return NULL;
  }
  fclose(fh);
  if (!is_binary) {
    for (c=oneline; *c != '\n' && *c != '\r' && *c != '\0'; c++)
      ;
    *c = '\0';   /* Safe because we allocated N+1 bytes but read only N */
    oneline = ncptl_realloc (oneline, c-oneline+1, 0);
  }
  return oneline;
}


#ifdef HAVE_SYSCTL
# ifdef CTL_HW
/* Return the value of an integer sysctl variable. */
static unsigned int get_sysctl_int (int category, int variable)
{
  int mib[2];
  unsigned int result = 0;
  size_t intsize = sizeof(unsigned int);

  mib[0] = category;
  mib[1] = variable;
  (void) sysctl (mib, 2, (void *)&result, &intsize, NULL, 0);
  return result;
}
#endif

# if defined(CTL_KERN) || defined(CTL_HW)
/* Return the value of a string sysctl variable.  The caller must
 * ncptl_free() the result. */
static char *get_sysctl_string (int category, int variable)
{
  int mib[2];
  char resultstr[NCPTL_MAX_LINE_LEN];
  size_t stringsize = NCPTL_MAX_LINE_LEN;

  mib[0] = category;
  mib[1] = variable;
  if (!sysctl (mib, 2, (void *)resultstr, &stringsize, NULL, 0))
    return ncptl_strdup (resultstr);
  else
    return NULL;
}
# endif
#endif


#ifdef HAVE_HAL
/* Connect to the HAL daemon and read a property string from it.  The
 * caller must ncptl_free() the result.  NULL is returned if the UDI
 * or property is unavailable. */
static char *get_hal_property_string (const char *udi, const char *propname)
{
  LibHalContext *hal_ctx;     /* HAL context */
  DBusConnection *conn;       /* Connection to the DBus */
  DBusError errval;           /* Error value returned from the dbus library */
  char *propvalue;            /* Value corresponding to {uid, propname} */
  char *propvaluecopy;        /* Copy of the above to return to the user */

  /* Connect to the DBus. */
  dbus_error_init (&errval);
  if (!(conn=dbus_bus_get(DBUS_BUS_SYSTEM, &errval))) {
    if (dbus_error_is_set (&errval))
      dbus_error_free (&errval);
    return NULL;
  }

  /* Create a HAL context (which implies connecting to the HAL daemon). */
  if (!(hal_ctx=libhal_ctx_new()))
    return NULL;
  if (!libhal_ctx_set_dbus_connection(hal_ctx, conn))
    return NULL;
  if (!libhal_ctx_init(hal_ctx, &errval)) {
    if (dbus_error_is_set (&errval))
      dbus_error_free (&errval);
    return NULL;
  }

  /* Query HAL for the property. */
  propvalue = libhal_device_get_property_string (hal_ctx, udi, propname, &errval);
  if (!propvalue) {
    if (dbus_error_is_set (&errval))
      dbus_error_free (&errval);
    return NULL;
  }
  propvaluecopy = ncptl_strdup (propvalue);
  libhal_free_string (propvalue);

  /* Destroy our HAL context. */
  libhal_ctx_shutdown (hal_ctx, &errval);
  libhal_ctx_free (hal_ctx);

  /* Disconnect from the DBus. */
  dbus_connection_unref (conn);
  dbus_error_free (&errval);

  /* Return the coNCePTuaL-allocated string. */
  return propvaluecopy;
}


/* Fill in various pieces of system information using HAL. */
static void fill_in_sys_desc_hal (SYSTEM_INFORMATION *info)
{
  const char *computer_udi = "/org/freedesktop/Hal/devices/computer";

  /* Try to read the computer make and model information. */
  if (!info->computer) {
    char *vendor;
    char *product;

    /* Read the computer vendor and product. */
    vendor = get_hal_property_string(computer_udi, "system.vendor");
    product = get_hal_property_string(computer_udi, "system.product");
    info->computer = ncptl_concatenate_strings (2, vendor, product);
    ncptl_free (vendor);
    ncptl_free (product);
  }

  /* Try to read the BIOS vendor and version. */
  if (!info->bios) {
    char *vendor;
    char *version;
    char *release_date;

    vendor = get_hal_property_string(computer_udi, "smbios.bios.vendor");
    version = get_hal_property_string(computer_udi, "smbios.bios.version");
    release_date = get_hal_property_string(computer_udi, "smbios.bios.release_date");
    info->bios = ncptl_concatenate_strings (3, vendor, version, release_date);
    ncptl_free (vendor);
    ncptl_free (version);
    ncptl_free (release_date);
  }
}
#endif


/* Fill in the name of the OS distribution if possible. */
static void fill_in_osdist (SYSTEM_INFORMATION *info)
{
  /* Run the lsb_release script to determine the OS distribution. */
#if defined(HAVE_POPEN)
  /* popen() uses fork() which may not work properly. */
  if (ncptl_fork_works) {
    FILE *lsb_pipe;                     /* Pipe from "lsb_release" */
    char oneline[NCPTL_MAX_LINE_LEN];   /* One line read from lsb_pipe */

    if ((lsb_pipe=popen("lsb_release -d 2>&1", "r"))) {
      while (fgets (oneline, NCPTL_MAX_LINE_LEN-1, lsb_pipe))
        if (!strncmp (oneline, "Description:", 12)) {
          ASSIGN (info->osdist, ncptl_strdup (oneline+13));
          break;
        }
      pclose(lsb_pipe);
    }
  }
  if (info->osdist)
    return;
#endif

  /* Read the distribution from *-release (fedora-release,
   * redhat-release, system-release, etc.).  This is of course a bit
   * risky because there may happen to be a binary *-release file in
   * /etc.  We simply take our chances and hope for the best. */
#ifdef HAVE_GLOB
  if (1) {
    glob_t globinfo;       /* Information about the expanded pathname */
    unsigned int i;

    if (glob("/etc/*-release", 0, NULL, &globinfo) == 0) {
      /* Iterate over each filename in turn. */
      for (i=0; i<globinfo.gl_pathc && !info->osdist; i++)
        ASSIGN (info->osdist, read_first_line(globinfo.gl_pathv[i], 0));
      globfree(&globinfo);
    }
  }
#endif
}


/* Fill in the host, arch, os, osdist, and computer fields. */
static void fill_in_sys_desc (SYSTEM_INFORMATION *info)
{
#if defined(HAVE_UNAME) && defined(HAVE_SYS_UTSNAME_H)
  struct utsname hostinfo;                  /* Various bit of description */
#endif
#ifdef HOST_NAME_MAX_VAR
  char thishostname[HOST_NAME_MAX_VAR+1];   /* Host name only */
#endif

  /* If we have /proc/version, try reading the OS version from there. */
  if (!info->os)
    info->os = read_first_line ("/proc/version", 0);

  /* Try to determine the name of the OS distribution. */
  fill_in_osdist(info);

#if defined(HAVE_SYSCTL) && defined(CTL_KERN) && defined(KERN_VERSION)
  /* sysctl() can return the full OS name at times when uname() can't. */
  ASSIGN (info->os, get_sysctl_string (CTL_KERN, KERN_VERSION));
#endif

#if defined(HAVE_UNAME) && defined(HAVE_SYS_UTSNAME_H)
  if (uname (&hostinfo) != -1) {
    ASSIGN (info->hostname, ncptl_strdup (hostinfo.nodename));
    ASSIGN (info->arch,     ncptl_strdup (hostinfo.machine));
    if (!info->os) {
      info->os = (char *) ncptl_malloc (strlen(hostinfo.sysname) + 1 +
                                        strlen(hostinfo.release) + 1 +
                                        strlen(hostinfo.version) + 1,
                                        0);
      sprintf (info->os, "%s %s %s",
               hostinfo.sysname, hostinfo.release, hostinfo.version);
    }
  }
#endif
#ifdef HOST_NAME_MAX_VAR
  if (!gethostname (thishostname, HOST_NAME_MAX_VAR))
    ASSIGN (info->hostname, ncptl_strdup (thishostname));
#endif
  if (info->hostname && info->hostname[0]=='\0') {
    /* At the time of this writing, BlueGene/L returns an empty hostname. */
    ncptl_free (info->hostname);
    info->hostname = NULL;
    ASSIGN (info->hostname, ncptl_strdup ("unknown"));
  }

#ifdef HAVE_GETHOSTBYNAME
  /* Try to replace the host name with a more "official" host name. */
  if (info->hostname) {
    struct hostent *thishostinfo = gethostbyname (info->hostname);

    if (thishostinfo && thishostinfo->h_name && thishostinfo->h_name != '\0') {
      ncptl_free (info->hostname);
      info->hostname = ncptl_strdup (thishostinfo->h_name);
    }
  }
#endif

#ifdef HAVE_HAL
  fill_in_sys_desc_hal (info);
#endif
}


#ifdef USE_PAPI
/* Fill in the CPU-related fields using PAPI. */
static void fill_in_cpu_info_PAPI (SYSTEM_INFORMATION *info)
{
  const PAPI_hw_info_t *hardwareinfo;   /* Hardware (mostly CPU) information */

  if ((hardwareinfo=PAPI_get_hardware_info())) {
    ASSIGN (info->contexts_per_node, hardwareinfo->ncpu);
    ASSIGN (info->cpu_vendor,        ncptl_strdup (hardwareinfo->vendor_string));
    ASSIGN (info->cpu_model,         ncptl_strdup (hardwareinfo->model_string));
    ASSIGN (info->cpu_freq,          1.0e6 * hardwareinfo->mhz);
  }
}
#endif


#if defined(HAVE_SYSCTL) && defined(CTL_HW)
/* Fill in the CPU-related fields using sysctl(). */
static void fill_in_cpu_info_sysctl (SYSTEM_INFORMATION *info)
{
  /* CPU speed */
#ifdef HW_NCPU
  ASSIGN (info->contexts_per_node, (int) get_sysctl_int (CTL_HW, HW_NCPU));
#endif
#ifdef HW_MODEL
  ASSIGN (info->cpu_model, get_sysctl_string (CTL_HW, HW_MODEL));
#endif
#ifdef HW_CPU_FREQ
  ASSIGN (info->cpu_freq, (double) get_sysctl_int (CTL_HW, HW_CPU_FREQ));
#endif
#ifdef HW_CPUSPEED
  ASSIGN (info->cpu_freq, 1.0e6 * get_sysctl_int (CTL_HW, HW_CPUSPEED));
#endif

  /* Cycle-counter speed */
#ifdef HW_TB_FREQ
  ASSIGN (info->timer_freq, (double) get_sysctl_int (CTL_HW, HW_TB_FREQ));
#endif

  /* Keep compilers from complaining about unused info */
  if (0)
    printf ("%p", info);
}
#endif


/* Fill in the CPU-related fields using sysconf(). */
#ifdef HAVE_SYSCONF
static void fill_in_cpu_info_sysconf (SYSTEM_INFORMATION *info)
{
# ifdef _SC_NPROCESSORS_ONLN
  /* Note that we store the number of processors online instead of the
   * number of processors configured.  The idea is to help detect poor
   * performance caused by unexpected multiprogramming when a CPU is
   * offline. */
  if (sysconf(_SC_NPROCESSORS_ONLN) > 0)
    ASSIGN (info->contexts_per_node, (int) sysconf(_SC_NPROCESSORS_ONLN));
#else
  /* Keep compilers from complaining about unused info */
  if (0)
    printf ("%p", info);
# endif
}
#endif


#ifdef HAVE_KSTAT_DATA_LOOKUP
/* Fill in the CPU-related fields using kstat_data_lookup(). */
static void fill_in_cpu_info_kstat (SYSTEM_INFORMATION *info)
{
  kstat_ctl_t *kcontrol;         /* kstat control */
  kstat_t *thekstat;             /* The kstat itself */
  kstat_named_t *kstatdata;      /* Value encountered */

  /* Open the kernel statistics. */
  if (!(kcontrol=kstat_open()))
    return;

  /* CPU model and frequency */
  if (!info->cpu_model &&
      (thekstat=kstat_lookup(kcontrol, "cpu_info", -1, "cpu_info0")) &&
      (kstat_read(kcontrol, thekstat, NULL) != -1)) {
    /* CPU model */
    if ((kstatdata=(kstat_named_t *)kstat_data_lookup (thekstat, "cpu_type")) &&
        kstatdata->data_type == KSTAT_DATA_CHAR)
      ASSIGN (info->cpu_model, ncptl_strdup (kstatdata->value.c));

    /* CPU frequency */
    if ((kstatdata=(kstat_named_t *)kstat_data_lookup (thekstat, "clock_MHz")) &&
        kstatdata->data_type == KSTAT_DATA_INT32)
      ASSIGN (info->cpu_freq, 1.0e6 * kstatdata->value.i32);
  }

  /* Number of CPUs */
  if (!info->contexts_per_node &&
      (thekstat=kstat_lookup(kcontrol, "unix", -1, "system_misc")) &&
      (kstat_read(kcontrol, thekstat, NULL) != -1)) {
    if ((kstatdata=(kstat_named_t *)kstat_data_lookup (thekstat, "ncpus")) &&
        kstatdata->data_type == KSTAT_DATA_UINT32)
      ASSIGN (info->contexts_per_node, (int)kstatdata->value.ui32);
  }

  /* Close the kernel statistics. */
  (void) kstat_close (kcontrol);
}
#endif


#ifdef HAVE_BGPPERSONALITY
/* Fill in the CPU-related fields using BG/P's Kernel_GetPersonality(). */
static void fill_in_cpu_info_bgp (SYSTEM_INFORMATION *info)
{
  ASSIGN (info->cpu_freq, ncptl_bgp_personality.Kernel_Config.FreqMHz*1e6);
}
#endif


#ifdef HAVE_BGLPERSONALITY
/* Fill in the CPU-related fields using BG/L's rts_get_personality(). */
static void fill_in_cpu_info_bgl (SYSTEM_INFORMATION *info)
{
  ASSIGN (info->cpu_freq, (double) BGLPersonality_clockHz(&ncptl_bgl_personality));
  ASSIGN (info->contexts_per_node,
          BGLPersonality_virtualNodeMode(&ncptl_bgl_personality) ? 2 : 1);
}
#endif


#ifdef HAVE___CPU_MHZ
/* Fill in the clock speed using the Cray XT's __cpu_mhz variable. */
static void fill_in_cpu_info_xt (SYSTEM_INFORMATION *info)
{
  extern uint32_t __cpu_mhz;

  ASSIGN (info->cpu_freq, 1e6 * __cpu_mhz);
}
#endif


#if defined(SYSMP_OKAY) && defined(MP_NPROCS)
/* Fill in the CPU-related fields using IRIX and UNICOS's sysmp(). */
static void fill_in_cpu_info_sysmp (SYSTEM_INFORMATION *info)
{
  int64_t numcpus = (int64_t) sysmp (MP_NPROCS);

  if (numcpus > 0)
    ASSIGN (info->contexts_per_node, numcpus);
}
#endif


#ifdef GETINVENT_OKAY
/* Fill in the CPU-related fields using SGI and Cray's getinvent(). */
static void fill_in_cpu_info_getinvent (SYSTEM_INFORMATION *info)
{
  inventory_t *invitem;
  setinvent();

  while ((invitem=getinvent()))
    if (invitem->inv_class==INV_PROCESSOR && invitem->inv_type==INV_CPUBOARD)
      ASSIGN (info->cpu_freq, 1e6 * (double) invitem->inv_controller);
}
#endif


#if defined(HAVE_SYS_SYSINFO_H) && defined(GSI_CPU_INFO)
/* Fill in the CPU-related fields using OSF1's getsysinfo(). */
static void fill_in_cpu_info_getsysinfo (SYSTEM_INFORMATION *info)
{
  struct cpu_info CPU_information;
  int startloc = 0;

  if (getsysinfo (GSI_CPU_INFO, (caddr_t)&CPU_information,
                  sizeof(CPU_information), &startloc, NULL, NULL) >= -1) {
    ASSIGN (info->contexts_per_node, CPU_information.cpus_in_box);
    ASSIGN (info->cpu_freq, 1e6 * (double) CPU_information.mhz);
  }
}
#endif


#ifdef ODM_IS_SUPPORTED
/* Fill in the CPU-related fields using AIX's Object Data Manager. */
static void fill_in_cpu_info_odm (SYSTEM_INFORMATION *info)
{
  struct CuAt *cuat_info;
  int num_instances;

  if (odm_initialize())
    return;
  if (!info->cpu_freq && (cuat_info=getattr ("proc0", "frequency", 0, &num_instances)))
    sscanf (cuat_info->value, "%lf", &info->cpu_freq);
  if ((cuat_info=getattr ("proc0", "type", 0, &num_instances)))
    ASSIGN (info->cpu_model, ncptl_strdup (cuat_info->value));
  if (!info->threads_per_core && (cuat_info=getattr ("proc0", "smt_threads", 0, &num_instances)))
    sscanf (cuat_info->value, "%d", &info->threads_per_core);
  (void) odm_terminate();
}
#endif


#ifdef _WIN32
/* Fill in the CPU-related fields using Win32 functions. */
static void fill_in_cpu_info_win32 (SYSTEM_INFORMATION *info)
{
  LARGE_INTEGER timerfreq;
  SYSTEM_INFO sysinfo;
  MEMORYSTATUSEX meminfo;
  OSVERSIONINFOEX osinfo;
  HKEY cpukey;

  /* Read the timer frequency. */
  if (QueryPerformanceFrequency(&timerfreq))
    ASSIGN (info->timer_freq, (double)timerfreq.QuadPart);

  /* Store both the fully-qualified DNS name and the NetBIOS name. */
  if (!info->hostname) {
    char hostname[NCPTL_MAX_LINE_LEN];
    DWORD namelen;

    namelen = NCPTL_MAX_LINE_LEN;
    if (GetComputerNameA (hostname, &namelen)) {
      info->hostname = (char *) ncptl_malloc (NCPTL_MAX_LINE_LEN, 0);
      strcpy (info->hostname, hostname);
      namelen = NCPTL_MAX_LINE_LEN;
      if (GetComputerNameExA (ComputerNamePhysicalDnsFullyQualified, hostname, &namelen))
        sprintf (info->hostname + strlen(info->hostname), " (%s)", hostname);
      info->hostname = ncptl_realloc (info->hostname, strlen(info->hostname)+1, 0);
    }
  }

  /* Get information about the CPU and memory system. */
  GetSystemInfo (&sysinfo);
  ASSIGN (info->pagesize, (uint64_t)sysinfo.dwPageSize);
  ASSIGN (info->contexts_per_node, (uint64_t)sysinfo.dwNumberOfProcessors);
  if (!info->arch)
    switch (sysinfo.wProcessorArchitecture) {
      case PROCESSOR_ARCHITECTURE_INTEL:
        info->arch = (char *) ncptl_malloc (NCPTL_MAX_LINE_LEN, 0);
        if (sysinfo.wProcessorLevel < 10)
          sprintf (info->arch, "i%d86", sysinfo.wProcessorLevel);
        else if (sysinfo.wProcessorLevel == 15)
          sprintf (info->arch, "i686");
        else
          sprintf (info->arch, "Intel processor level %d", sysinfo.wProcessorLevel);
        info->arch = ncptl_realloc (info->arch, strlen(info->arch)+1, 0);
        break;

      case PROCESSOR_ARCHITECTURE_IA64:
        info->arch = "ia64";
        break;

      case PROCESSOR_ARCHITECTURE_AMD64:
        info->arch = "x86_64";
        break;

      default:
        break;
    }
  meminfo.dwLength = sizeof (MEMORYSTATUSEX);
  GlobalMemoryStatusEx (&meminfo);
  ASSIGN (info->physmem, (uint64_t)meminfo.ullTotalPhys);

  /* Get more information about the CPU by reading the Windows registry. */
  if (RegOpenKeyEx (HKEY_LOCAL_MACHINE,
                    "Hardware\\Description\\System\\CentralProcessor\\0",
                    0, KEY_READ, &cpukey) == ERROR_SUCCESS) {
    char buffer[NCPTL_MAX_LINE_LEN];
    DWORD bufferlen;

    /* Processor description */
    bufferlen = NCPTL_MAX_LINE_LEN;
    if (!info->cpu_model &&
        RegQueryValueEx (cpukey, "ProcessorNameString", NULL, NULL,
                         buffer, &bufferlen) == ERROR_SUCCESS)
      ASSIGN (info->cpu_model, ncptl_strdup(buffer));

    /* Vendor identifier */
    bufferlen = NCPTL_MAX_LINE_LEN;
    if (!info->cpu_vendor &&
        RegQueryValueEx (cpukey, "VendorIdentifier", NULL, NULL,
                         buffer, &bufferlen) == ERROR_SUCCESS)
      ASSIGN (info->cpu_vendor, ncptl_strdup(buffer));

    /* CPU frequency */
    bufferlen = NCPTL_MAX_LINE_LEN;
    if (!info->cpu_freq &&
        RegQueryValueEx (cpukey, "~MHz", NULL, NULL,
                         buffer, &bufferlen) == ERROR_SUCCESS)
      ASSIGN (info->cpu_freq, 1.0e6 * (double)*(DWORD *)buffer);

    /* We're finished with the CPU registry key. */
    (void) RegCloseKey (cpukey);
  }

  /* Pretty-print the version of Windows that the user is running. */
  if (!info->os) {
    osinfo.dwOSVersionInfoSize = sizeof (OSVERSIONINFOEX);
    if (GetVersionEx ((LPOSVERSIONINFO) &osinfo)) {
      DWORD majver = osinfo.dwMajorVersion;
      DWORD minver = osinfo.dwMinorVersion;
      char *osstring = NULL;

      info->os = (char *) ncptl_malloc (NCPTL_MAX_LINE_LEN, 0);
      sprintf (info->os, "Microsoft Windows ");
      if (majver == 6)
        osstring = "Vista";
      else if (majver == 5) {
        if (minver == 2)
          osstring = "Server 2003";
        else if (minver == 1)
          osstring = "XP";
        else if (minver == 0)
          osstring = "2000";
      }
      else if (majver == 4)
        osstring = "NT 4";
      if (osstring)
        strcat (info->os, osstring);
      else
        sprintf (info->os + strlen(info->os),
                 "(unrecognized version %d.%d)",
                 majver, minver);
      if (osinfo.szCSDVersion[0]) {
        strcat (info->os, " ");
        strcat (info->os, osinfo.szCSDVersion);
      }
      sprintf (info->os + strlen(info->os), " (Build %u)", osinfo.dwBuildNumber);
      info->os = ncptl_realloc (info->os, strlen(info->os)+1, 0);
    }
  }
}
#endif


/* Fill in the CPU-related fields by reading /proc/cpuinfo. */
static void fill_in_cpu_info_cpuinfo (SYSTEM_INFORMATION *info)
{
  FILE *procinfo;     /* Handle to /proc/cpuinfo */
  char oneline[NCPTL_MAX_LINE_LEN+1];   /* One line read from /proc/cpuinfo */
  double frequency;   /* CPU or timer frequency */
  int cpucount;       /* Number of active CPU cores */
  int have_ncpus = info->contexts_per_node!=0;  /* 1=already assigned the total number of CPU cores */
  int cpu_cores;      /* Number of CPU cores per socket */
  int physical_id;    /* Physical ID of the current socket */
  char *cpu_family = NULL;    /* CPU family name */
  char *cpu_model = NULL;     /* CPU model number */
  char *cpu_revision = NULL;  /* CPU revision number */

  /* Read interesting information from /proc/cpuinfo. */
  if (!(procinfo=fopen ("/proc/cpuinfo", "r")))
    return;
  while (fgets (oneline, NCPTL_MAX_LINE_LEN, procinfo)) {
    char *keyname = extract_key (oneline);

    /* CPU speed */
    if (!info->cpu_freq) {
      /* IA-32 and IA-64 */
      if (sscanf (oneline, "cpu MHz : %lf", &frequency))
        ASSIGN (info->cpu_freq, 1.0e6 * frequency);
      /* PowerPC */
      else if (sscanf (oneline, "clock : %lfMHz", &frequency))
        ASSIGN (info->cpu_freq, 1.0e6 * frequency);
      else if (sscanf (oneline, "clock : %lfGHz", &frequency))
        ASSIGN (info->cpu_freq, 1.0e9 * frequency);
      /* Alpha */
      else if (sscanf (oneline, "cycle frequency [Hz] : %lf", &frequency))
        ASSIGN (info->cpu_freq, frequency);
    }

    /* CPU model */
    if (!info->cpu_model) {
      /* IA-32 */
      if (!strcmp (keyname, "model name"))
        ASSIGN (info->cpu_model, extract_value (oneline));
      /* PowerPC */
      else if (!strcmp (keyname, "cpu"))
        ASSIGN (info->cpu_model, extract_value (oneline));
      /* IA-64 */
      else if (!strcmp (keyname, "family")) {
        uint64_t cpu_family_number;   /* Numeric version of cpu_family */
        char *firstbad;               /* Pointer to first nonnumeric character */

        cpu_family = extract_value (oneline);
        errno = 0;
        cpu_family_number = strtoull (cpu_family, &firstbad, 10);
        if (*firstbad == '\0') {
          /* Family is entirely numeric -- prefix with the word "Family". */
          char cpu_family_string[NCPTL_MAX_LINE_LEN];
          sprintf (cpu_family_string, "family %s", cpu_family);
          ncptl_free (cpu_family);
          cpu_family = ncptl_strdup (cpu_family_string);
        }
      }
      else if (!strcmp (keyname, "model"))
        cpu_model = extract_value (oneline);
      else if (!strcmp (keyname, "revision"))
        cpu_revision = extract_value (oneline);
      if (cpu_family && cpu_model && cpu_revision) {
        char cpu_description[NCPTL_MAX_LINE_LEN];

        sprintf (cpu_description, "%s, model %s, revision %s",
                 cpu_family, cpu_model, cpu_revision);
        info->cpu_model = ncptl_strdup (cpu_description);
      }
    }
    else
      /* Alpha defines both "cpu" and "cpu model"; we want only the latter. */
      if (!strcmp (keyname, "cpu model")) {
        if (info->cpu_model) {
          ncptl_free (info->cpu_model);
          info->cpu_model = NULL;
        }
        ASSIGN (info->cpu_model, extract_value (oneline));
      }

    /* CPU vendor */
    if (!info->cpu_vendor) {
      /* IA-32 */
      if (!strcmp (keyname, "vendor_id"))
        ASSIGN (info->cpu_vendor, extract_value (oneline));
      /* IA-64 */
      else if (!strcmp (keyname, "vendor"))
        ASSIGN (info->cpu_vendor, extract_value (oneline));
    }

    /* Total number of CPU compute contexts (threads*cores*dies*sockets) */
    /* IA-32, IA-64, and PowerPC */
    if (!have_ncpus && !strcmp (keyname, "processor"))
      info->contexts_per_node++;
    /* Alpha */
    else if (sscanf (oneline, "cpus active : %d", &cpucount))
      ASSIGN (info->contexts_per_node, cpucount);

    /* Cycle-counter speed */
    /* IA-64 */
    if (sscanf (oneline, "itc MHz : %lf", &frequency))
      ASSIGN (info->timer_freq, 1.0e6 * frequency);
    /* PowerPC */
    else if (sscanf (oneline, "timebase : %lf", &frequency))
      ASSIGN (info->timer_freq, frequency);

    /* Number of sockets and cores */
    if (sscanf (oneline, "cpu cores : %d", &cpu_cores))
      ASSIGN(info->cores_per_socket, cpu_cores);
    if (sscanf (oneline, "physical id : %d", &physical_id)
        && physical_id+1 > info->sockets_per_node)
      info->sockets_per_node = physical_id + 1;

    /* CPU flags */
    if (!strcmp (keyname, "flags"))
      ASSIGN (info->cpu_flags, extract_value (oneline));

    /* Clean up before the next iteration. */
    ncptl_free (keyname);
  }
  fclose (procinfo);

  /* Clean up any memory we may have allocated. */
  ncptl_free (cpu_family);
  ncptl_free (cpu_model);
  ncptl_free (cpu_revision);
}


/* Fill in the CPU-related fields by reading files under /sys. */
static void fill_in_cpu_info_sysfs (SYSTEM_INFORMATION *info)
{
  char *maxfreq_str;   /* Maximum CPU frequency in KHz as a text string */
  double maxfreq;      /* Maximum CPU frequency in KHz */

  /* As a last-ditch effort to find the timebase frequency, use the
   * highest frequency at which the CPU can run.  This is probably a
   * decent guess but is not guaranteed to return the correct
   * timebase.  Alas, reading the correct value from the x86 MSRs can
   * currently be done only from kernel mode. */
  if (info->timer_freq)
    return;
  maxfreq_str = read_first_line ("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", 0);
  if (!maxfreq_str)
    return;
  if (sscanf (maxfreq_str, "%lf", &maxfreq) == 1)
    ASSIGN (info->timer_freq, maxfreq*1000.0);
  ncptl_free (maxfreq_str);
}


/* Fill in all of the the CPU-related fields. */
static void fill_in_cpu_info (SYSTEM_INFORMATION *info)
{
#ifdef CYCLES_PER_USEC
  ASSIGN (info->timer_freq, 1.0e6 * CYCLES_PER_USEC);
#endif

  fill_in_cpu_info_cpuinfo (info);
#ifdef USE_PAPI
  fill_in_cpu_info_PAPI (info);
#endif
#ifdef HAVE_BGPPERSONALITY
  fill_in_cpu_info_bgp (info);
#endif
#ifdef HAVE_BGLPERSONALITY
  fill_in_cpu_info_bgl (info);
#endif
#ifdef HAVE___CPU_MHZ
  fill_in_cpu_info_xt (info);
#endif
#ifdef ODM_IS_SUPPORTED
  fill_in_cpu_info_odm (info);
#endif
#ifdef SYSMP_OKAY
  fill_in_cpu_info_sysmp (info);
#endif
#ifdef GETINVENT_OKAY
  fill_in_cpu_info_getinvent (info);
#endif
#if defined(HAVE_SYS_SYSINFO_H) && defined(GSI_CPU_INFO)
  fill_in_cpu_info_getsysinfo (info);
#endif
#if defined(HAVE_SYSCTL) && defined(CTL_HW)
  fill_in_cpu_info_sysctl (info);
#endif
#ifdef HAVE_SYSCONF
  fill_in_cpu_info_sysconf (info);
#endif
#ifdef HAVE_KSTAT_DATA_LOOKUP
  fill_in_cpu_info_kstat (info);
#endif
#ifdef _WIN32
  fill_in_cpu_info_win32 (info);
#endif
#if defined(TIMEBASE_FREQUENCY_FILENAME)
  if (!info->timer_freq) {
    char *timebase_bits;

    timebase_bits = read_first_line (TIMEBASE_FREQUENCY_FILENAME, 1);
    if (timebase_bits) {
      ASSIGN (info->timer_freq, *(double *)timebase_bits);
      ncptl_free (timebase_bits);
    }
  }
#endif
  fill_in_cpu_info_sysfs (info);

  /* If contexts_per_node is 1, then cores_per_socket,
   * sockets_per_node, and threads_per_core must all also be 1. */
  if (info->contexts_per_node == 1) {
    ASSIGN(info->cores_per_socket, 1);
    ASSIGN(info->sockets_per_node, 1);
    ASSIGN(info->threads_per_core, 1);
  }

  /* If we know contexts_per_node, cores_per_socket, and
   * sockets_per_node, we can easily compute threads_per_core if
   * necessary. */
  if (info->contexts_per_node
      && info->cores_per_socket
      && info->sockets_per_node
      && !info->threads_per_core)
    info->threads_per_core =
      info->contexts_per_node / (info->cores_per_socket * info->sockets_per_node);
}


/* Fill in all of the memory-related fields. */
static void fill_in_mem_info (SYSTEM_INFORMATION *info)
{
  /* OS page size */
#ifdef OS_PAGE_SIZE
  ASSIGN (info->pagesize, (uint64_t) OS_PAGE_SIZE);
#else
# if defined(HAVE_SYSCONF) && defined(_SC_PAGESIZE)
  if (sysconf(_SC_PAGESIZE) > 0)
    ASSIGN (info->pagesize, (uint64_t) sysconf(_SC_PAGESIZE));
# endif
# if defined(HAVE_SYSCONF) && defined(_SC_PAGE_SIZE)
  if (sysconf(_SC_PAGE_SIZE) > 0)
    ASSIGN (info->pagesize, (uint64_t) sysconf(_SC_PAGE_SIZE));
# endif
# if defined(HAVE_GETPAGESIZE)
  ASSIGN (info->pagesize, (uint64_t) getpagesize());
# endif
#endif

  /* Physical memory */
#if defined(HAVE_BGPPERSONALITY)
  ASSIGN (info->physmem, (uint64_t) ncptl_bgp_personality.DDR_Config.DDRSizeMB*1048576);
#endif
#if defined(HAVE_BGLPERSONALITY)
  ASSIGN (info->physmem, (uint64_t) BGLPersonality_DDRSize(&ncptl_bgl_personality));
#endif
#ifdef HAVE_SYSCONF
# ifdef _SC_AIX_REALMEM
  if (sysconf (_SC_AIX_REALMEM) > 0)
    ASSIGN (info->physmem, 1024 * (uint64_t) sysconf (_SC_AIX_REALMEM));

# elif defined(_SC_PHYS_PAGES)
  if (sysconf (_SC_PHYS_PAGES) > 0)
    ASSIGN (info->physmem, info->pagesize * (uint64_t) sysconf (_SC_PHYS_PAGES));
# endif
#endif
#if defined(GETINVENT_OKAY) && defined(INV_MEMORY) && defined(INV_MAIN_MB)
  {
    inventory_t *invitem;
    setinvent();
    while ((invitem=getinvent()))
      if (invitem->inv_class==INV_MEMORY && invitem->inv_type==INV_MAIN_MB)
        ASSIGN (info->physmem, (uint64_t)invitem->inv_state * 1048576);
  }
#endif
#if defined(HAVE_SYS_SYSINFO_H) && defined(GSI_PHYSMEM)
  {
    int phys_kilobytes;
    int startloc = 0;

    if (getsysinfo (GSI_PHYSMEM, (caddr_t)&phys_kilobytes,
                    (unsigned long) sizeof(int),
                    &startloc, NULL, NULL) >= 1)
      ASSIGN (info->physmem, (uint64_t) phys_kilobytes * 1024);
  }
#endif
#if defined(HAVE_SYSCTL) && defined(HW_CTL) && defined(HW_PHYSMEM)
  ASSIGN (info->physmem, (uint64_t) get_sysctl_int (HW_CTL, HW_PHYSMEM));
#endif
}


#ifdef HAVE_PCIUTILS
/* Remember PCI Utilities errors but output nothing. */
static void catch_pciutils_error (char *format, ...)
{
  va_list args;               /* Argument list */

  va_start (args, format);
  pciutils_error = 1;
  va_end (args);
}


/* Remember PCI Utilities warnings but output nothing. */
static void catch_pciutils_warning (char *format, ...)
{
  va_list args;               /* Argument list */

  va_start (args, format);
  va_end (args);
}


/* Use the PCI Utilities to fill in information about PCI-based networks. */
static void fill_in_network_info_pciutils (SYSTEM_INFORMATION *info)
{
  struct pci_access *pcibus;     /* PCI bus abstraction */
  struct pci_dev *dev;           /* One device on a PCI bus */
  NCPTL_QUEUE *devqueue;         /* List of device strings */

  /* Define a macro to clean up no-longer-needed state and return. */
# define CLEAN_UP_AND_RETURN                    \
  do {                                          \
    pci_cleanup (pcibus);                       \
    ncptl_queue_empty (devqueue);               \
    ncptl_free (devqueue);                      \
    return;                                     \
  }                                             \
  while (0)

  /* Define a macro to execute a statement and return if an error occurred. */
# define CALL_AND_CHECK(STMT)                   \
  do {                                          \
    STMT;                                       \
    if (pciutils_error)                         \
      CLEAN_UP_AND_RETURN;                      \
  }                                             \
  while (0)

  /* Initialize the PCI Utilities. */
  pcibus = pci_alloc();
  pcibus->error = catch_pciutils_error;
  pcibus->warning = catch_pciutils_warning;
  devqueue = ncptl_queue_init (sizeof(char *));
  pci_init (pcibus);

  /* See what devices are on the bus. */
  CALL_AND_CHECK (pci_scan_bus(pcibus));

  /* Walk the linked list of devices. */
  for (dev=pcibus->devices; dev; dev=dev->next) {
    uint8_t devicemem[128];      /* Device PCI memory */
    int devmemsize = 64;         /* Number of valid bytes in the above */
    char classbuf[NCPTL_MAX_LINE_LEN];  /* Buffer of class information */
    char devicebuf[NCPTL_MAX_LINE_LEN]; /* Buffer of device information */
    uint16_t classID;            /* Device's class identifier */
    char *classname;             /* Name of the device's class */
    char *devicename;            /* Name of the device */
    uint8_t revision;            /* Device revision number */
    char *device_string;         /* Textual description of the device */

    /* Read and cache the device's memory (up to 128 bytes). */
    memset (devicemem, 0, 128);
    if (!pci_read_block (dev, 0, devicemem, 64))
      CLEAN_UP_AND_RETURN;
    if ((devicemem[PCI_HEADER_TYPE] & 0x7f) == PCI_HEADER_TYPE_CARDBUS) {
      /* For cardbus bridges, we need to fetch 64 bytes more to get
       * the full standard header... */
      if (!pci_read_block (dev, 64, devicemem+64, 64))
        CLEAN_UP_AND_RETURN;
      devmemsize += 64;
    }
    CALL_AND_CHECK (pci_setup_cache (dev, devicemem, devmemsize));

    /* Acquire the device's class ID, class name, device name, and revision. */
    if (!pci_fill_info (dev,
                        PCI_FILL_IDENT | PCI_FILL_IRQ | PCI_FILL_BASES | PCI_FILL_ROM_BASE | PCI_FILL_SIZES))
      CLEAN_UP_AND_RETURN;
    classID = (uint16_t)devicemem[PCI_CLASS_DEVICE+1]<<8 | (uint16_t)devicemem[PCI_CLASS_DEVICE];
    CALL_AND_CHECK (classname = pci_lookup_name (pcibus, classbuf,
                                                 NCPTL_MAX_LINE_LEN,
                                                 PCI_LOOKUP_CLASS,
                                                 classID, 0, 0, 0));
    CALL_AND_CHECK (devicename = pci_lookup_name (pcibus, devicebuf,
                                                  NCPTL_MAX_LINE_LEN,
                                                  PCI_LOOKUP_VENDOR|PCI_LOOKUP_DEVICE,
                                                  dev->vendor_id,
                                                  dev->device_id, 0, 0));
    revision = devicemem[PCI_REVISION_ID];

    /* Determine if the device is a network device. */
    if (!((classID&0xFF00) == 0x0200  /* Network controller */
#ifdef HAVE_STRCASESTR
          || strcasestr(devicename, "net")   /* Anything with "net" in the name */
          || strcasestr(devicename, "interconnect")   /* Anything with "interconnect" in the name */
#else
          || strstr(devicename, "net")
          || strstr(devicename, "Net")
          || strstr(devicename, "NET")
          || strstr(devicename, "interconnect")
          || strstr(devicename, "Interconnect")
          || strstr(devicename, "INTERCONNECT")
#endif
          || classID == 0x0C06))      /* Serial bus controller, InfiniBand */

      continue;
    device_string = ncptl_malloc (strlen(devicename) + 20 + strlen(classname), 0);
    if (revision)
      sprintf (device_string, "%s, revision 0x%02X (%s)", devicename, revision, classname);
    else
      sprintf (device_string, "%s (%s)", devicename, classname);
    ncptl_queue_push (devqueue, &device_string);
  }

  /* Store the list of devices and return. */
  info->networks = devqueue;
  pci_cleanup (pcibus);
}
#endif


/* Fill in all of the network-related fields. */
static void fill_in_network_info (SYSTEM_INFORMATION *info)
{
#ifdef HAVE_PCIUTILS
  fill_in_network_info_pciutils (info);
#else
  info->networks = NULL;    /* Prevent whiny C compilers from complaining. */
#endif
}


/******************************************
 * Library-global variables and functions *
 ******************************************/

/* Find out everything we can about the current system.  All strings
 * are allocated with ncptl_malloc() and should be ncptl_free()d by
 * the caller. */
void ncptl_discern_system_information (SYSTEM_INFORMATION *info)
{
  memset ((void *)info, 0, sizeof(SYSTEM_INFORMATION));
#ifdef HAVE_BGPPERSONALITY
  memset ((void *)&ncptl_bgp_personality, 0, sizeof(_BGP_Personality_t));
  if (Kernel_GetPersonality(&ncptl_bgp_personality, sizeof(_BGP_Personality_t)))
    ncptl_fatal ("Failed to retrieve the BlueGene/P personality");
#endif
#ifdef HAVE_BGLPERSONALITY
  memset ((void *)&ncptl_bgl_personality, 0, sizeof(BGLPersonality));
  if (rts_get_personality (&ncptl_bgl_personality, sizeof(BGLPersonality)))
    ncptl_fatal ("Failed to retrieve the BlueGene/L personality");
#endif
  fill_in_sys_desc (info);
  fill_in_cpu_info (info);
  fill_in_mem_info (info);
  fill_in_network_info (info);
}
