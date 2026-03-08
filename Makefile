#!/usr/bin/make -f

-include .env

.PHONY: help build clean deploy local

help:
	$(info make build|clean|local|deploy)

build:
	uv run build.py

clean:
	rm -rf site/*

local:
	sudo rsync -ahvc --checksum --delete site/* /var/www/html

deploy:
	rsync -ahvcz --checksum --delete site/* $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_PATH)
