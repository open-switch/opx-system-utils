ACLOCAL_AMFLAGS=-I m4
SUBDIRS = inc

pyutilsdir= /usr/lib/opx/sys-utils
pyutils_SCRIPTS = scripts/lib/python/*.py

uidir= /usr/lib/opx/sys-utils/templates
ui_SCRIPTS = scripts/lib/python/templates/*

staticdir= /usr/lib/opx/sys-utils/images
static_SCRIPTS = scripts/lib/python/images/*

webdir= /usr/lib/opx/sys-utils/scripts
web_SCRIPTS = scripts/lib/python/scripts/*

pluginsdir= /usr/lib/opx/sys-utils/plugins
plugins_SCRIPTS = scripts/lib/python/plugins/*.py

lib_LTLIBRARIES=libopx_system_utils.la
libopx_system_utils_la_SOURCES= src/sys_utils_file_transfer.c


COMMON_HARDEN_FLAGS=-fexceptions -fstack-protector-strong -fstack-protector-all -D_FORTIFY_SOURCE=2 -Wall -Wformat -Wformat-security -Werror
C_HARDEN_FLAGS=-Wimplicit-function-declaration
LD_HARDEN_FLAGS=-Wl,-z,defs -Wl,-z,now

libopx_system_utils_la_CPPFLAGS= -D_FILE_OFFSET_BITS=64 -I$(top_srcdir)/inc/opx -I$(includedir)/opx $(COMMON_HARDEN_FLAGS) -fPIC
libopx_system_utils_la_CXXFLAGS=-std=c++11
libopx_system_utils_la_CFLAGS=$(C_HARDEN_FLAGS)
libopx_system_utils_la_LDFLAGS=-lcurl -shared -version-info 1:1:0 $(LD_HARDEN_FLAGS)
libopx_system_utils_la_LIBADD=-lopx_common


systemdconfdir=/lib/systemd/system
systemdconf_DATA = $(top_srcdir)/scripts/init/*.service
