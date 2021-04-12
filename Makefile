#!/usr/bin/make -f

include config

.PHONY: help build clean deploy

help:
	$(info make build|clean|remote)

deploy:
		rsync -ahvuz dst/ $(USERNAME)@$(REMOTE):$(DESTINATION)

clean:
	    rm -r dst

build:
	    sh build.sh
