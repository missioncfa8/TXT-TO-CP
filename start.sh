#!/bin/sh

# Start the Flask web server in the background
gunicorn --bind 0.0.0.0:$PORT app:app &

# Start the Telegram bot
python3 main.py