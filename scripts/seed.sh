#!/bin/bash

# Simple wrapper to run the database seeding script
# Usage: ./scripts/seed.sh [--clean]

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Set PYTHONPATH to include the root directory so imports work
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# Run the seeding script
python3 "$SCRIPT_DIR/seed_db.py" "$@"
