from fastapi import FastAPI, Request, Response, HTTPException
from dotenv import load_dotenv
import os, json
import httpx
from twilio.rest import Client
from twilio.request_validator import RequestValidator

from whatsappbot import nlu
from whatsappbot.db import init_db, add_task, list_tasks, complete_task, delete_task
from whatsappbot import mcp_client

load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
USE_MCP = os.getenv("USE_MCP", "false").lower() == "true"

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = FastAPI(title="WhatsApp Bot")

@app.on_event("startup")
def on_start():
    init_db()

@app.get("/")
def home():
    return {"message": "WhatsApp Bot is running!"}

async def send_whatsapp_text(to_phone: str, text: str):
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER):
        print("WARN: Missing Twilio credentials in environment variables.")
        return
    
    try:
        message = client.messages.create(
            to=f"whatsapp:{to_phone}",
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
            body=text
        )
        return message.sid
    except Exception as e:
        print(f"Error sending WhatsApp message via Twilio: {e}")
        return None

# Twilio webhook endpoint with validation
@app.post("/wa/webhook")
async def incoming(request: Request):
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    url = str(request.url)
    form_data = await request.form()
    signature = request.headers.get('X-Twilio-Signature', '')
    
    # Twilio's recommended validation
    if not validator.validate(url, dict(form_data), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # The rest of your bot logic remains the same
    from_phone = form_data.get("From", "").replace("whatsapp:", "")
    user_text = form_data.get("Body", "")

    if from_phone and user_text:
        parsed = nlu.parse(user_text)
        intent = parsed["intent"]
        scope = parsed["scope"]
        text = parsed["text"]

        if intent == "help":
            reply = ("Try:\n"
                     "- add buy milk to today\n"
                     "- show today\n"
                     "- complete buy milk\n"
                     "- delete 3 (by id)\n")

        elif intent == "add" and scope and text:
            if USE_MCP:
                resp = await mcp_client.mcp_add_task(from_phone, scope, text)
                reply = resp["message"]
            else:
                task_id = add_task(from_phone, scope, text)
                reply = f"✅ Added (#{task_id}) to {scope}: “{text}”"

        elif intent == "list":
            if USE_MCP:
                resp = await mcp_client.mcp_list_tasks(from_phone, scope)
                reply = resp["message"]
            else:
                rows = list_tasks(from_phone, scope)
                if not rows:
                    sc = scope or "all"
                    reply = f"(empty) No open tasks in {sc}."
                else:
                    lines = [f"• #{r['id']} [{r['scope']}] {r['text']}" for r in rows]
                    reply = "Your tasks:\n" + "\n".join(lines)

        elif intent == "complete" and text:
            if USE_MCP:
                resp = await mcp_client.mcp_complete_task(from_phone, text)
                reply = resp["message"]
            else:
                count = complete_task(from_phone, text)
                reply = "✅ Marked done." if count else "Couldn’t find that task."

        elif intent == "delete" and text:
            if USE_MCP:
                resp = await mcp_client.mcp_delete_task(from_phone, text)
                reply = resp["message"]
            else:
                count = delete_task(from_phone, text)
                reply = "🗑️ Deleted." if count else "Couldn’t find that task."

        else:
            reply = "Sorry, I didn’t get that. Type *help* for examples."

        await send_whatsapp_text(from_phone, reply)
    
    return {"status": "ok"}

@app.get("/healthz")
def health():
    return {"ok": True}