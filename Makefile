#!/usr/bin/make -f

include config

.PHONY: help build clean deploy

help:
	$(info make build|clean|remote)

deploy:
		rsync -ahvuz -e 'ssh -p $(PORT)' dst/ orion@$(REMOTE):sites/orionc.dev

clean:
	    rm -r dst

build:
	    sh generate.sh
