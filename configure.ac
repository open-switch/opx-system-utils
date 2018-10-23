#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([opx-system-utils],[0.1.0],[ops-dev@lists.openswitch.net])
AM_INIT_AUTOMAKE([foreign subdir-objects])
AC_CONFIG_SRCDIR([.])
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_MACRO_DIRS([m4])
AM_MAINTAINER_MODE([enable])

# Checks for programs.
#AC_PROG_CXX
AM_PATH_PYTHON
AC_PROG_CXX
AC_PROG_CC
LT_INIT([shared])

# Checks for header files
AC_CHECK_HEADERS([curl/curl.h string.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
#AC_CHECK_HEADER_STDBOOL
#AC_C_INLINE
#AC_TYPE_SIZE_T

# Checks for library functions.
#AC_FUNC_MMAP
AC_FUNC_STRERROR_R
AC_CHECK_FUNCS([memset fclose snprintf unlink])

AC_CONFIG_FILES([Makefile inc/Makefile])
AC_OUTPUT
