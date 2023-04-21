#!/bin/bash

set -e

# Set your variables
SONAR_API_URL="https://sonarcloud.io/api"
SONAR_ORG_KEY="${SONAR_ORGANIZATION_KEY}"
SONAR_PROJECT_KEY="${SONAR_PROJECT_KEY}"
SONAR_TOKEN="${SONAR_TOKEN}"

# Retrieve the list of issues
issues=$(curl -s -G \
  -H "Authorization: Basic $(echo -n "${SONAR_TOKEN}": | base64)" \
  --data-urlencode "organization=${SONAR_ORG_KEY}" \
  --data-urlencode "projects=${SONAR_PROJECT_KEY}" \
  --data-urlencode "ps=500" \
  --data-urlencode "types=BUG, VULNERABILITY, CODE_SMELL" \
  --data-urlencode "statuses=OPEN, CONFIRMED" \
  "${SONAR_API_URL}/issues/search")

# Extract the suggested fixes using jq and output them as a JSON array
fixes=$(echo "$issues" | jq -r '[.issues[] | .message]')

echo "$fixes"