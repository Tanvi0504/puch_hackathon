from fastapi import FastAPI, Request, Response, HTTPException
from dotenv import load_dotenv
import os, json
import httpx

from whatsappbot import nlu
from whatsappbot.db import init_db, add_task, list_tasks, complete_task, delete_task
from whatsappbot import mcp_client  # NEW

load_dotenv()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
USE_MCP = os.getenv("USE_MCP", "false").lower() == "true"

API_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages" if PHONE_NUMBER_ID else ""

app = FastAPI(title="WhatsApp Bot")

@app.on_event("startup")
def on_start():
    init_db()

@app.get("/")
def home():
    return {"message": "WhatsApp Bot is running!"}

async def send_whatsapp_text(to_phone: str, text: str):
    if not (WHATSAPP_TOKEN and API_URL):
        print("WARN: Missing WHATSAPP_TOKEN or PHONE_NUMBER_ID.")
        return
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(API_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

@app.get("/wa/webhook")
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/wa/webhook")
async def incoming(request: Request):
    body = await request.json()
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}

        msg = messages[0]
        from_phone = msg.get("from")
        msg_type = msg.get("type")

        user_text = None
        if msg_type == "text":
            user_text = msg["text"]["body"]
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if "button_reply" in interactive:
                user_text = interactive["button_reply"]["title"]
            elif "list_reply" in interactive:
                user_text = interactive["list_reply"]["title"]

        if from_phone and user_text:
            # --- NLU ---
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

    except Exception as e:
        print("Webhook error:", e, "\nBody:", json.dumps(body, indent=2))

    return {"status": "ok"}

@app.get("/healthz")
def health():
    return {"ok": True}