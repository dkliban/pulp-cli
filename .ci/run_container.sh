#!/bin/sh

BASEPATH=$(dirname $(readlink -f $0))
if ls /usr/bin/podman
then
  RUNTIME=podman
else
  RUNTIME=docker
fi

"${RUNTIME}" run --rm --detach --name "pulp" --volume "${BASEPATH}/settings:/etc/pulp" --publish "8080:80" pulp/pulp-fedora31
for i in $(seq 10)
do
  sleep 3
  if curl --fail http://localhost:8080/pulp/api/v3/status/
  then
    break
  fi
done

trap "${RUNTIME} stop pulp" EXIT

"${RUNTIME}" exec -t pulp bash -c "pulpcore-manager reset-admin-password --password password"

"$@"
