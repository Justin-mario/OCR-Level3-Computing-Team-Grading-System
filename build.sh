#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Initialize the database
python init_db.py