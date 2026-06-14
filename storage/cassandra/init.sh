#!/bin/sh
# wait for Cassandra to be ready
until cqlsh cassandra -e 'DESCRIBE KEYSPACES' > /dev/null 2>&1; do
  echo 'Waiting for Cassandra...'
  sleep 2
done

echo 'Cassandra is up, running init.cql'
cqlsh cassandra -f /init.cql