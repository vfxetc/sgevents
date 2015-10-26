#!/bin/bash

# This should already be done by the user's profile,
# but lets just be super sure.
source /usr/local/vee/environments/westernx/master/etc/bashrc

# Make sure to NOT use the Shotgun cache for this.
unset SGCACHE

# Move here.
cd "$(dirname "${BASH_SOURCE[0]}")"

mkdir -p var/logs

exec python -m sgevents.commands.daemon \
        --verbose \
        --email-errors 'mboers@mail.westernx' \
	--email-errors 'mreid@mail.westernx' \
	--log-dir var/logs \
	--state-path var/state.json \
	--plugin-dir plugins/westernx

	
