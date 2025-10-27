#!/bin/bash
cd "$HOME/loki-stack/grafana"
export GF_PATHS_DATA="$HOME/.loki-data/grafana"
echo "Starting Grafana..."
echo "Grafana will be available at http://127.0.0.1:3000"
./bin/grafana server
