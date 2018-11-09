ACLOCAL_AMFLAGS = -I m4
SUBDIRS = inc

COMMON_HARDEN_FLAGS = -fexceptions -fstack-protector-strong -fstack-protector-all -D_FORTIFY_SOURCE=2 -Wall -Wformat -Wformat-security -Werror
C_HARDEN_FLAGS = -Wimplicit-function-declaration
LD_HARDEN_FLAGS = -Wl,-z,defs -Wl,-z,now

lib_LTLIBRARIES = libopx_system_utils.la
libopx_system_utils_la_SOURCES = src/sys_utils_file_transfer.c
libopx_system_utils_la_CPPFLAGS = $(COMMON_HARDEN_FLAGS) $(libcurl_CFLAGS) -D_FILE_OFFSET_BITS=64 -fPIC -I$(top_srcdir)/inc/opx
libopx_system_utils_la_CXXFLAGS = -std=c++11
libopx_system_utils_la_CFLAGS = $(C_HARDEN_FLAGS)
libopx_system_utils_la_LDFLAGS = $(LD_HARDEN_FLAGS) -shared -version-info 1:1:0
libopx_system_utils_la_LIBADD = $(libcurl_LIBS) -lopx_common

pluginsdir = /usr/lib/opx/sys-utils/plugins
plugins_SCRIPTS = scripts/lib/python/plugins/*.py

pyutilsdir = /usr/lib/opx/sys-utils
pyutils_SCRIPTS = scripts/lib/python/*.py

staticdir = /usr/lib/opx/sys-utils/images
static_SCRIPTS = scripts/lib/python/images/*

uidir = /usr/lib/opx/sys-utils/templates
ui_SCRIPTS = scripts/lib/python/templates/*

webdir = /usr/lib/opx/sys-utils/scripts
web_SCRIPTS = scripts/lib/python/scripts/*

systemdconfdir = /lib/systemd/system
systemdconf_DATA = scripts/init/*.service

