#!/bin/bash
# Seed script wrapper to run the Python seed script

cd "$(dirname "$0")/server"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the seed script
echo "Running database seed script..."
python seed_data.py

echo "Seed script completed!"
