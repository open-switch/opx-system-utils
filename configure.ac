AC_PREREQ([2.69])
AC_INIT([opx-system-utils], [0.1.0], [ops-dev@lists.openswitch.net])
AM_INIT_AUTOMAKE([foreign subdir-objects])
AC_CONFIG_SRCDIR([configure.ac])
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_MACRO_DIRS([m4])

AM_PATH_PYTHON
AC_PROG_CC
PKG_CHECK_MODULES([libcurl], [libcurl])
LT_INIT([shared])

AC_CONFIG_FILES([Makefile inc/Makefile])
AC_OUTPUT
