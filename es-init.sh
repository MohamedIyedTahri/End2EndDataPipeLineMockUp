#!/bin/bash

CRED_DIR=/usr/share/elasticsearch/credentials
ELASTIC_PASSWORD_FILE=$CRED_DIR/elastic_password
SERVICE_TOKEN_FILE=$CRED_DIR/kibana_service_token

mkdir -p $CRED_DIR

if [ ! -f "$ELASTIC_PASSWORD_FILE" ]; then
  echo "Setting elastic password and creating kibana service token..."

  # Wait for ES to be available with proper error handling
  MAX_TRIES=60
  COUNT=0
  until curl -s -u elastic:changeme http://localhost:9200 >/dev/null 2>&1; do
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_TRIES ]; then
      echo "ERROR: Elasticsearch did not start within expected time"
      exit 1
    fi
    echo "Waiting for Elasticsearch to start... (attempt $COUNT/$MAX_TRIES)"
    sleep 5
  done

  echo "Elasticsearch is ready!"

  NEW_PASS="Q*aPCff9cD3Q6WDKjYpR"
  echo "Changing elastic user password via API..."
  curl -X POST "http://localhost:9200/_security/user/elastic/_password" \
    -H "Content-Type: application/json" \
    -u "elastic:changeme" \
    -d "{\"password\":\"$NEW_PASS\"}"
  
  echo ""
  echo "Password changed successfully!"

  echo $NEW_PASS > $ELASTIC_PASSWORD_FILE
  chmod 600 $ELASTIC_PASSWORD_FILE

  echo "Creating Kibana service token..."
  # Delete existing token if it exists
  /usr/share/elasticsearch/bin/elasticsearch-service-tokens delete elastic/kibana/kibana-token 2>/dev/null || true
  
  TOKEN_OUTPUT=$(/usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/kibana kibana-token)
  echo "$TOKEN_OUTPUT" | grep "SERVICE_TOKEN" | awk '{print $NF}' > $SERVICE_TOKEN_FILE
  chmod 600 $SERVICE_TOKEN_FILE

  echo "Credentials saved successfully."
  echo "Elastic password saved to: $ELASTIC_PASSWORD_FILE"
  echo "Kibana token saved to: $SERVICE_TOKEN_FILE"
else
  echo "Credentials already exist. Skipping initialization."
fi
