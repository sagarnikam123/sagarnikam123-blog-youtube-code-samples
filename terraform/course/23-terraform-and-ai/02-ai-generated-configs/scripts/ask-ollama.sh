#!/bin/bash
# =============================================================================
# External data source script — calls Ollama API
# =============================================================================
# Reads JSON input from stdin (Terraform passes variables this way)
# Calls Ollama's generate API
# Returns JSON output to stdout
#
# IMPORTANT: External data sources MUST:
#   1. Read JSON from stdin
#   2. Write ONLY valid JSON to stdout
#   3. No other output (no echo, no debug prints to stdout)
# =============================================================================

set -e

# Read input from Terraform (JSON on stdin)
INPUT=$(cat)

# Extract variables from the JSON input
MODEL=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['model'])")
PROMPT=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['prompt'])")
OLLAMA_URL=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ollama_url', 'http://localhost:11434'))")

# Call Ollama API (non-streaming)
RESPONSE=$(curl -s "${OLLAMA_URL}/api/generate" \
  -d "{
    \"model\": \"${MODEL}\",
    \"prompt\": \"${PROMPT}\",
    \"stream\": false,
    \"options\": {
      \"temperature\": 0.3,
      \"num_predict\": 500
    }
  }")

# Extract the response text
AI_RESPONSE=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('response', 'No response'))
")

# Extract timing info
TOTAL_DURATION=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ns = data.get('total_duration', 0)
print(f'{ns / 1e9:.2f}s')
" 2>/dev/null || echo "unknown")

# Return valid JSON to Terraform
# All values MUST be strings in external data source output
python3 -c "
import json, sys
response = '''${AI_RESPONSE}'''
output = {
    'response': response.strip()[:4000],
    'model': '${MODEL}',
    'duration': '${TOTAL_DURATION}'
}
json.dump(output, sys.stdout)
"
