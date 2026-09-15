#!/usr/bin/env bash
set -euo pipefail

cqlsh "${CASSANDRA_HOST:-localhost}" -f "$(dirname "$0")/cassandra/init.cql"
echo "Cassandra schema applied."

MAPPING=$(python3 -c "
import json, sys
d = json.load(open('$(dirname "$0")/elasticsearch/init.json'))
print(json.dumps(d['INDEX_MAPPING']))
")
curl -sf -X PUT "http://${ES_HOST:-localhost}:${ES_PORT:-9200}/${ES_INDEX:-search}" \
  -H "Content-Type: application/json" \
  -d "$MAPPING"
echo "ES index created."
