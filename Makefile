#!/usr/bin/make -f

USERNAME=''
REMOTE=''
DESTINATION=''

.PHONY: help build clean deploy

help:
	$(info make build|clean|remote)

deploy:
	rsync -ahvuz site/* $(USERNAME)@$(REMOTE):$(DESTINATION)
	rsync -ahvuz static $(USERNAME)@$(REMOTE):$(DESTINATION)

clean:
	rm -r site/*

build:
	python3 build.py

local:
	sudo rsync -auvt site/* /var/www/html
	sudo rsync -auvt static /var/www/html
