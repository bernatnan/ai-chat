#!/bin/bash
# Script to substitute environment variables in librechat.test.yaml
# Usage: ./substitute-env.sh

set -e

ENV_FILE=".env.test.local"
YAML_FILE="librechat.test.yaml"
OUTPUT_FILE="librechat.test.yaml.tmp"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

if [ ! -f "$YAML_FILE" ]; then
    echo "Error: $YAML_FILE not found"
    exit 1
fi

echo "Substituting environment variables from $ENV_FILE into $YAML_FILE..."

# Read env file and substitute variables
cp "$YAML_FILE" "$OUTPUT_FILE"

while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue
    
    # Extract variable name and value
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        var_name="${BASH_REMATCH[1]}"
        var_value="${BASH_REMATCH[2]}"
        
        # Remove quotes if present
        var_value="${var_value%\"}"
        var_value="${var_value#\"}"
        var_value="${var_value%\'}"
        var_value="${var_value#\'}"
        
        # Substitute in YAML file
        if [ -n "$var_value" ]; then
            sed -i "s|\${${var_name}}|${var_value}|g" "$OUTPUT_FILE"
            echo "  Substituted \${${var_name}}"
        fi
    fi
done < "$ENV_FILE"

# Replace original file
mv "$OUTPUT_FILE" "$YAML_FILE"

echo "Done! Variables substituted in $YAML_FILE"
