ifeq ($(OS),Windows_NT)
	CCFLAGS += -D WIN32
	ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
		CCFLAGS += -D AMD64
	endif
	ifeq ($(PROCESSOR_ARCHITECTURE),x86)
		CCFLAGS += -D IA32
	endif
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		CCFLAGS += -D LINUX
	endif
	ifeq ($(UNAME_S),Darwin)
		CCFLAGS += -D OSX
	endif
	UNAME_P := $(shell uname -p)
	ifeq ($(UNAME_P),x86_64)
		CCFLAGS += -D AMD64
	endif
	ifneq ($(filter %86,$(UNAME_P)),)
		CCFLAGS += -D IA32
	endif
	ifneq ($(filter arm%,$(UNAME_P)),)
		CCFLAGS += -D ARM
	endif
endif

osx:
	go install
	sed 's|\$$GOPATH|'"${GOPATH}"'|g' com.camlittle.PhotoManagement.plist > $(HOME)/Library/LaunchAgents/com.camlittle.PhotoManagement.plist
	if [ ! -f ${HOME}/.gophotoconfig ] ; \
	then \
		cp gophotoconfig.json ${HOME}/.gophotoconfig ; \
	fi;
	launchctl load $(HOME)/Library/LaunchAgents/com.camlittle.PhotoManagement.plist

test:
	go test
	plutil -lint com.camlittle.PhotoManagement.plist
