#!/bin/bash
#
# Run Property-Based Tests for SkyWalking Cluster Deployment
#
# This script runs all property-based tests with appropriate configuration.
# It validates universal properties across randomized inputs with 100 iterations per test.
#
# Usage:
#   ./run-property-tests.sh [options]
#
# Options:
#   -v, --verbose       Verbose output
#   -q, --quiet         Quiet output (errors only)
#   -f, --fast          Fast mode (10 examples instead of 100)
#   -c, --coverage      Generate coverage report
#   -h, --help          Show this help message
#
# Examples:
#   ./run-property-tests.sh                    # Run all property tests
#   ./run-property-tests.sh -v                 # Run with verbose output
#   ./run-property-tests.sh -f                 # Fast mode for quick validation
#   ./run-property-tests.sh -c                 # Run with coverage report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
VERBOSE=""
FAST_MODE=""
COVERAGE=""
QUIET=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE="-v --hypothesis-verbosity=verbose"
      shift
      ;;
    -q|--quiet)
      QUIET="-q"
      shift
      ;;
    -f|--fast)
      FAST_MODE="--hypothesis-max-examples=10"
      shift
      ;;
    -c|--coverage)
      COVERAGE="--cov=. --cov-report=html --cov-report=term"
      shift
      ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo -e "${RED}Error: Unknown option: $1${NC}"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SkyWalking Property-Based Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Error: python3 is not installed${NC}"
  exit 1
fi

# Check if pytest is installed
if ! python3 -c "import pytest" &> /dev/null; then
  echo -e "${YELLOW}Warning: pytest is not installed${NC}"
  echo -e "${YELLOW}Installing dependencies...${NC}"
  pip install -r requirements.txt
  echo ""
fi

# Check if Hypothesis is installed
if ! python3 -c "import hypothesis" &> /dev/null; then
  echo -e "${YELLOW}Warning: hypothesis is not installed${NC}"
  echo -e "${YELLOW}Installing dependencies...${NC}"
  pip install -r requirements.txt
  echo ""
fi

# Check if required files exist
if [ ! -f "../helm-values/base-values.yaml" ]; then
  echo -e "${RED}Error: base-values.yaml not found${NC}"
  echo -e "${RED}Expected location: ../helm-values/base-values.yaml${NC}"
  exit 1
fi

if [ ! -f "../helm-values/minikube-values.yaml" ]; then
  echo -e "${RED}Error: minikube-values.yaml not found${NC}"
  echo -e "${RED}Expected location: ../helm-values/minikube-values.yaml${NC}"
  exit 1
fi

# Display test configuration
echo -e "${GREEN}Test Configuration:${NC}"
echo "  - Test files: property_test_*.py"
echo "  - Max examples: $([ -n "$FAST_MODE" ] && echo "10 (fast mode)" || echo "100 (default)")"
echo "  - Verbosity: $([ -n "$VERBOSE" ] && echo "verbose" || echo "normal")"
echo "  - Coverage: $([ -n "$COVERAGE" ] && echo "enabled" || echo "disabled")"
echo ""

# Run property-based tests
echo -e "${GREEN}Running property-based tests...${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest property_test_*.py -m property"

# Add options
[ -n "$VERBOSE" ] && PYTEST_CMD="$PYTEST_CMD $VERBOSE"
[ -n "$QUIET" ] && PYTEST_CMD="$PYTEST_CMD $QUIET"
[ -n "$FAST_MODE" ] && PYTEST_CMD="$PYTEST_CMD $FAST_MODE"
[ -n "$COVERAGE" ] && PYTEST_CMD="$PYTEST_CMD $COVERAGE"

# Add default options if not quiet
if [ -z "$QUIET" ]; then
  PYTEST_CMD="$PYTEST_CMD --tb=short"
fi

# Execute tests
if eval $PYTEST_CMD; then
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}All property-based tests passed!${NC}"
  echo -e "${GREEN}========================================${NC}"

  # Show coverage report location if generated
  if [ -n "$COVERAGE" ]; then
    echo ""
    echo -e "${BLUE}Coverage report generated:${NC}"
    echo "  HTML: file://$(pwd)/htmlcov/index.html"
  fi

  exit 0
else
  echo ""
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}Some property-based tests failed!${NC}"
  echo -e "${RED}========================================${NC}"
  echo ""
  echo -e "${YELLOW}Troubleshooting tips:${NC}"
  echo "  1. Check test output above for specific failures"
  echo "  2. Run with -v for verbose output"
  echo "  3. Run with -f for fast mode to quickly identify issues"
  echo "  4. Check that all required Helm values files exist"
  echo "  5. Verify YAML syntax in configuration files"
  echo ""
  exit 1
fi
