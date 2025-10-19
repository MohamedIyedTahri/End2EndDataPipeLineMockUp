#!/bin/bash

CRED_DIR=/usr/share/elasticsearch/credentials
SERVICE_TOKEN_FILE=$CRED_DIR/kibana_service_token

# Wait for Elasticsearch to be ready
MAX_TRIES=60
COUNT=0
until curl -s http://elasticsearch:9200 >/dev/null 2>&1; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_TRIES ]; then
    echo "ERROR: Elasticsearch is not ready"
    exit 1
  fi
  echo "Waiting for Elasticsearch to be ready... (attempt $COUNT/$MAX_TRIES)"
  sleep 5
done

echo "Elasticsearch is ready!"

# Wait for service token to be created
COUNT=0
until [ -f "$SERVICE_TOKEN_FILE" ] && [ -s "$SERVICE_TOKEN_FILE" ]; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_TRIES ]; then
    echo "ERROR: Service token file not found or empty"
    exit 1
  fi
  echo "Waiting for Kibana service token... (attempt $COUNT/$MAX_TRIES)"
  sleep 2
done

SERVICE_TOKEN=$(cat $SERVICE_TOKEN_FILE)
echo "Service token loaded successfully"

# Write the kibana configuration with the service token
cat > /usr/share/kibana/config/kibana.yml <<EOF
server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: [ "http://elasticsearch:9200" ]

# Service token authentication
elasticsearch.serviceAccountToken: "${SERVICE_TOKEN}"

# Encryption keys
xpack.security.encryptionKey: "Fz72I9z+1xOa1dY59pWqT4EZ0SsNROjp"
xpack.encryptedSavedObjects.encryptionKey: "76ws91KdS1VqlWCIQXeNGXEESjsa9Pgu"
xpack.reporting.encryptionKey: "gCW4QASWodnFv9fzxv8GoDfDNzNg8q5k"
EOF

echo "Kibana configuration written successfully"
echo "Starting Kibana with service token authentication..."
echo "Elasticsearch Host: http://elasticsearch:9200"
exec /usr/local/bin/kibana-docker
