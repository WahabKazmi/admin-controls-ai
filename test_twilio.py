from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")  # "whatsapp:+14155238886"
to_number = "whatsapp:" + os.getenv("TWILIO_TO_NUMBER")  # adds "whatsapp:" prefix

print("✅ FROM:", from_number)
print("✅ TO:", to_number)

# Check for empty
if not to_number or not from_number:
    print("❌ ERROR: Number missing from environment!")
    exit()

msg = client.messages.create(
    from_=from_number,
    to=to_number,
    body="🚀 WhatsApp message from Twilio test is successful!"
)

print("✅ Sent! SID:", msg.sid)
