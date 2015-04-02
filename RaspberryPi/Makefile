#############################################################################
#
# Makefile for datagram program on the Raspberry Pi
#
# License: GPL (General Public License)
# Author:  Eskild Schroll-Fleischer <eskild.sf@coderer.com>
# Date:    2015/04/01 (version 1.0)
#
# Description:
# ------------
# Use make to make the datagram program
prefix := /usr/local

# Detect the Raspberry Pi by the existence of the bcm_host.h file
BCMLOC=/opt/vc/include/bcm_host.h

ifneq ("$(wildcard $(BCMLOC))","")
# The recommended compiler flags for the Raspberry Pi
CCFLAGS=-Ofast -mfpu=vfp -mfloat-abi=hard -march=armv6zk -mtune=arm1176jzf-s
endif

# define all programs
PROGRAMS = requestData
SOURCES = ${PROGRAMS:=.cpp}

all: ${PROGRAMS}

${PROGRAMS}: ${SOURCES}
	g++ ${CCFLAGS} -Wall -I../ -lrf24-bcm $@.cpp -o $@

clean:
	rm -rf $(PROGRAMS)

install: all
	test -d $(prefix) || mkdir $(prefix)
	test -d $(prefix)/bin || mkdir $(prefix)/bin
	for prog in $(PROGRAMS); do \
	  install -m 0755 $$prog $(prefix)/bin; \
	done

.PHONY: install
