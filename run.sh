#!/bin/bash

source /usr/local/vee/environments/westernx/master/etc/bashrc

unset SGCACHE

cd /var/lib/sgevents/sgevents

mkdir -p var/logs

exec python -m sgevents.daemon \
	--email-errors 'mboers@mail.westernx' \
	--log-dir var/logs \
	--state-path var/state.json \
	--plugin-dir plugins

	
