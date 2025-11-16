import os
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Bot Status</title>
</head>
<body>
    <div style="text-align: center; margin-top: 50px;">
        <h1>Telegram Bot is Running</h1>
        <p>The bot is currently active and listening for messages.</p>
        <p><a href="/health">Health Check</a></p>
    </div>
</body>
</html>
"""

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "telegram-bot"})
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Bot Status</title>
</head>
<body>
    <div style="text-align: center; margin-top: 50px;">
        <h1>Telegram Bot is Running</h1>
        <p>The bot is currently active and listening for messages.</p>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)