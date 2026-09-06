#!/usr/bin/env bash
# ==============================================================================
# OpenTelemetry Hands-on Course - Top-Level Test Runner
#
# Validates:
#   1. Markdown linting via npx markdownlint-cli2
#   2. YAML & Collector configuration syntax
#   3. Python syntax and compilation across all modules
#   4. Python runnable lessons and automated tests via uv
#   5. Java Maven projects compilation across all modules
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

PASSED_COUNT=0
TOTAL_COUNT=5
START_TIME=$(date +%s)

echo -e "${BOLD}${BLUE}================================================================${NC}"
echo -e "${BOLD}${BLUE}   OpenTelemetry Course - Automated Verification Suite        ${NC}"
echo -e "${BOLD}${BLUE}================================================================${NC}"
echo -e "Target Directory: ${SCRIPT_DIR}\n"

# ------------------------------------------------------------------------------
# 1. Markdown Linting
# ------------------------------------------------------------------------------
echo -e "${BOLD}[1/5] Checking Markdown Formatting (npx markdownlint-cli2)...${NC}"
if npx markdownlint-cli2 "**/*.md"; then
  echo -e "${GREEN}✓ Markdown lint passed cleanly (0 issues).${NC}\n"
  PASSED_COUNT=$((PASSED_COUNT + 1))
else
  echo -e "${RED}✗ Markdown lint failed.${NC}\n"
  exit 1
fi

# ------------------------------------------------------------------------------
# 2. YAML & Collector Configurations Validation
# ------------------------------------------------------------------------------
echo -e "${BOLD}[2/5] Validating YAML & Collector Configurations...${NC}"
python3 - << 'EOF'
import glob, yaml, sys

yaml_files = sorted(glob.glob("**/*.yaml", recursive=True) + glob.glob("**/*.yml", recursive=True))
print(f"Found {len(yaml_files)} YAML configuration files.")
errors = 0
for f in yaml_files:
    try:
        with open(f, "r") as fp:
            list(yaml.safe_load_all(fp.read()))
    except Exception as e:
        print(f"  [FAIL] {f}: {e}", file=sys.stderr)
        errors += 1

if errors > 0:
    print(f"YAML validation failed with {errors} error(s).", file=sys.stderr)
    sys.exit(1)
else:
    print("All YAML files validated successfully.")
EOF
echo -e "${GREEN}✓ All YAML manifests and collector pipelines are syntactically valid.${NC}\n"
PASSED_COUNT=$((PASSED_COUNT + 1))

# ------------------------------------------------------------------------------
# 3. Python Syntax & Compilation
# ------------------------------------------------------------------------------
echo -e "${BOLD}[3/5] Verifying Python Syntax Across All Modules...${NC}"
python3 -m py_compile $(find . -name "*.py")
echo -e "${GREEN}✓ All Python source files compiled with 0 syntax errors.${NC}\n"
PASSED_COUNT=$((PASSED_COUNT + 1))

# ------------------------------------------------------------------------------
# 4. Python Runnable Lessons & Unit Tests
# ------------------------------------------------------------------------------
echo -e "${BOLD}[4/5] Running Python Module Executions & Unit Tests (via uv)...${NC}"

echo -n "  -> 02-observability-fundamentals: "
(cd 02-observability-fundamentals/01-signals-comparison/python && uv run --with-requirements requirements.txt python main.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 03-semantic-conventions (pytest): "
(cd 03-semantic-conventions/01-semconv-span/python && uv run --with-requirements requirements.txt --with pytest pytest test_semconv.py -q >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 04-api-sdk-architecture (noop & manual): "
(cd 04-api-sdk-architecture/01-approaches/python && uv run --with-requirements requirements.txt python api_noop.py >/dev/null 2>&1 && uv run --with-requirements requirements.txt python manual_sdk.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 06-traces-and-context-propagation: "
(cd 06-traces-and-context-propagation/01-propagation/python && uv run --with-requirements requirements.txt python client_server_demo.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 07-metrics (instruments): "
(cd 07-metrics/01-instruments/python && uv run --with-requirements requirements.txt python main.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 08-logs (correlation bridge): "
(cd 08-logs/01-log-correlation/python && uv run --with-requirements requirements.txt python main.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 09-sdk-pipelines (samplers): "
(cd 09-sdk-pipelines/01-samplers-and-processors/python && uv run --with-requirements requirements.txt python main.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -n "  -> 14-maintaining-and-debugging: "
(cd 14-maintaining-and-debugging/01-broken-pipelines && uv run --with-requirements requirements.txt python diagnose.py >/dev/null 2>&1)
echo -e "${GREEN}PASS${NC}"

echo -e "${GREEN}✓ All Python execution and unit tests passed.${NC}\n"
PASSED_COUNT=$((PASSED_COUNT + 1))

# ------------------------------------------------------------------------------
# 5. Java Projects Compilation (Maven)
# ------------------------------------------------------------------------------
echo -e "${BOLD}[5/5] Compiling Java Projects (Maven & OTel BOM 1.65.0)...${NC}"
JAVA_PROJECTS=(
  "01-introduction/01-hello-trace/java"
  "02-observability-fundamentals/01-signals-comparison/java"
  "03-semantic-conventions/01-semconv-span/java"
  "04-api-sdk-architecture/01-approaches/java"
  "05-data-model-and-otlp/01-otlp-protocols/java"
  "06-traces-and-context-propagation/01-propagation/java"
  "07-metrics/01-instruments/java"
  "08-logs/01-log-correlation/java"
  "09-sdk-pipelines/01-samplers-and-processors/java"
  "10-auto-instrumentation/02-java-agent"
  "15-capstone-distributed-app/worker-java"
)

for proj in "${JAVA_PROJECTS[@]}"; do
  echo -n "  -> Compiling ${proj}: "
  (cd "$proj" && mvn test-compile -q)
  echo -e "${GREEN}PASS${NC}"
done

echo -e "${GREEN}✓ All 11 Java projects compiled cleanly with 0 errors.${NC}\n"
PASSED_COUNT=$((PASSED_COUNT + 1))

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${BOLD}${BLUE}================================================================${NC}"
echo -e "${BOLD}${GREEN}   VERIFICATION SUITE COMPLETED: ${PASSED_COUNT}/${TOTAL_COUNT} STAGES PASSED (${DURATION}s)   ${NC}"
echo -e "${BOLD}${BLUE}================================================================${NC}"
