#!/usr/bin/make -f

USERNAME=''
REMOTE=''
DESTINATION=''

.PHONY: help build clean deploy

help:
	$(info make build|clean|remote)

deploy:
		rsync -ahvuz dst/ $(USERNAME)@$(REMOTE):$(DESTINATION)

clean:
	    rm -r dst

build:
	    sh build.sh
