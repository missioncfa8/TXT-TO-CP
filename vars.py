#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = 22984163
API_HASH = "18c3760d602be96b599fa42f1c322956"
BOT_TOKEN = "8348577322:AAHOpd-XLXdVpBl3eC_d6iKyt_nNQ6sDXaQ"

OWNER = 915101089
CREDIT = environ.get("CREDIT", "Unknown")

TOTAL_USER = os.environ.get('TOTAL_USERS', '').split(',')
TOTAL_USERS = [int(user_id) for user_id in TOTAL_USER if user_id.strip()]

AUTH_USER = os.environ.get('AUTH_USERS', '').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER if user_id.strip()]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set
