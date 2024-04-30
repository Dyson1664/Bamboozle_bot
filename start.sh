#!/usr/bin/env bash
# exit on error
set -o errexit

# Set PATH for Chrome, needed for Selenium
export PATH="/opt/render/project/src/.render/chrome/opt/google/chrome:$PATH"

# Start the Flask application using Gunicorn
gunicorn main:app --timeout 120