# twilio_handler.py

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Twilio credentials from environment
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# Default WhatsApp sandbox number if not set
from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
to_number = os.getenv("TWILIO_TO_NUMBER")

# Initialize Twilio client
client = Client(account_sid, auth_token)

def send_whatsapp_message(body: str):
    if not all([from_number, to_number, account_sid, auth_token]):
        print("❌ Twilio credentials or phone numbers missing.")
        return

    try:
        print("📤 Sending WhatsApp message:", body)
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=body
        )
        print("✅ WhatsApp message sent! SID:", message.sid)
    except Exception as e:
        print("❌ Failed to send WhatsApp message:", e)
