#!/bin/bash

# Random Log Generator Script
# Generates fake logs using fuzzy-train for testing Loki ingestion

echo "🚀 Starting random log generators..."

# Create log directory if it doesn't exist
mkdir -p ${HOME}/data/log/logger

# Stop any existing log generators
echo "🛑 Stopping existing log generators..."
ps aux | grep fuzzy-train | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Check if fuzzy-train is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check if fuzzy-train exists
FUZZY_TRAIN_PATH="${HOME}/Documents/git/fuzzy-train/fuzzy-train.py"
if [[ ! -f "$FUZZY_TRAIN_PATH" ]]; then
    echo "❌ Error: fuzzy-train not found at $FUZZY_TRAIN_PATH"
    echo "💡 Clone fuzzy-train: git clone https://github.com/sagarnikam123/fuzzy-train.git"
    exit 1
fi

echo "📝 Starting log generators..."

# Generator 1: JSON logs (default)
echo "  Starting fuzzy-train-1 (JSON logs)..."
python3 "$FUZZY_TRAIN_PATH" \
    --output file \
    --file ${HOME}/data/log/logger/fuzzy-train-1.log \
    --lines-per-second 2 \
    --log-format JSON \
    --min-log-length 90 \
    --max-log-length 150 > /dev/null 2>&1 &

# Generator 2: Logfmt logs
echo "  Starting fuzzy-train-2 (logfmt logs)..."
python3 "$FUZZY_TRAIN_PATH" \
    --output file \
    --file ${HOME}/data/log/logger/fuzzy-train-2.log \
    --lines-per-second 1 \
    --log-format logfmt \
    --min-log-length 80 \
    --max-log-length 120 > /dev/null 2>&1 &

# Generator 3: Apache common logs
echo "  Starting fuzzy-train-3 (Apache logs)..."
python3 "$FUZZY_TRAIN_PATH" \
    --output file \
    --file ${HOME}/data/log/logger/fuzzy-train-3.log \
    --lines-per-second 3 \
    --log-format "apache common" \
    --min-log-length 100 \
    --max-log-length 200 > /dev/null 2>&1 &

# Generator 4: High volume JSON logs
echo "  Starting fuzzy-train-4 (high volume)..."
python3 "$FUZZY_TRAIN_PATH" \
    --output file \
    --file ${HOME}/data/log/logger/fuzzy-train-4.log \
    --lines-per-second 5 \
    --log-format JSON \
    --min-log-length 50 \
    --max-log-length 100 > /dev/null 2>&1 &

sleep 2

echo "✅ Log generators started successfully!"
echo ""
echo "📊 Active generators:"
ps aux | grep fuzzy-train | grep -v grep | awk '{print "  PID " $2 ": " $11 " " $12 " " $13}'
echo ""
echo "📁 Log files:"
echo "  ${HOME}/data/log/logger/fuzzy-train-1.log (JSON, 2 lines/sec)"
echo "  ${HOME}/data/log/logger/fuzzy-train-2.log (logfmt, 1 line/sec)"
echo "  ${HOME}/data/log/logger/fuzzy-train-3.log (Apache, 3 lines/sec)"
echo "  ${HOME}/data/log/logger/fuzzy-train-4.log (JSON high volume, 5 lines/sec)"
echo ""
echo "🔍 Monitor logs:"
echo "  tail -f ${HOME}/data/log/logger/fuzzy-train-*.log"
echo ""
echo "🛑 Stop generators:"
echo "  ps aux | grep fuzzy-train | grep -v grep | awk '{print \$2}' | xargs kill -9"
