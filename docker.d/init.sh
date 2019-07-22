#!/bin/bash
set -e

# == START: This system variables are set by cloudops ==
test $PROJECT_NAME
test $ENV  # ENV should be set to "dev", "stage" or "prod"
test $COT_PRODUCT  # either "firefox" or "thunderbird"
test $TASKCLUSTER_CLIENT_ID
test $TASKCLUSTER_ACCESS_TOKEN
#test $ED25519_PRIVKEY  # optional since on staging we don't sign CoT files
# == END ==

TEMPLATEDIR=/app/docker.d/configs
CONFIGDIR=/app/configs
CONFIGLOADER=/app/bin/configloader
SCRIPTWORKER=/app/bin/scriptworker

# export JSON-e related vars
export TASK_SCRIPT_CONFIG="$CONFIGDIR/worker.json"

mkdir -p -m 700 $CONFIGDIR

# Eval JSON-e expressions in the config templates
$CONFIGLOADER --worker-id-prefix=$PROJECT_NAME- $TEMPLATEDIR/scriptworker.yaml $CONFIGDIR/scriptworker.json
$CONFIGLOADER $TEMPLATEDIR/worker.json $CONFIGDIR/worker_config.json

echo $ED25519_PRIVKEY > $CONFIGDIR/ed25519_privkey
chmod 600 $CONFIGDIR/ed25519_privkey

exec $SCRIPTWORKER $CONFIGDIR/scriptworker.json
