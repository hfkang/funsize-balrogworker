#!/bin/bash

: "${TASKCLUSTER_CLIENT_ID:?Need to set TASKCLUSTER_CLIENT_ID}"
: "${TASKCLUSTER_ACCESS_TOKEN:?Need to set TASKCLUSTER_ACCESS_TOKEN}"
: "${SCRIPTWORKER_WORKER_ID:?Need to set SCRIPTWORKER_WORKER_ID}"
: "${BALROG_API_ROOT:?Need to set BALROG_API_ROOT}"

/app/py3.5/bin/scriptworker /app/config.json
