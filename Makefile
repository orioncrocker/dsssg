#!/usr/bin/make -f

USERNAME=''
REMOTE=''
DESTINATION=''

.PHONY: help build clean deploy

help:
	$(info make build|clean|remote)

deploy:
	rsync -ahvuz site/* $(USERNAME)@$(REMOTE):$(DESTINATION)

clean:
	rm -rf site/*

build:
	python3 build.py

local:
	sudo rsync -auvt site/* /var/www/html
