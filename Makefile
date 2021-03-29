#!/usr/bin/make -f

.PHONY: help build clean deploy

help:
	$(info make build|clean|deploy)

clean:
	rm -r dst

build:
	sh generate.sh