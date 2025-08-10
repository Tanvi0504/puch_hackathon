# whatsappbot/mcp_client.py

import os
import httpx
from typing import Optional

# Get the MCP server URL and authentication token from environment variables
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8086/mcp")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "your-secret-token")

async def mcp_add_task(phone: str, scope: str, text: str):
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    payload = {"phone": phone, "scope": scope, "text": text}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{MCP_SERVER_URL}/add_task", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

async def mcp_list_tasks(phone: str, scope: Optional[str] = None):
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    params = {"phone": phone, "scope": scope}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{MCP_SERVER_URL}/list_tasks", headers=headers, params=params)
        r.raise_for_status()
        return r.json()

async def mcp_complete_task(phone: str, text_or_id: str):
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    payload = {"phone": phone, "text_or_id": text_or_id}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{MCP_SERVER_URL}/complete_task", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

async def mcp_delete_task(phone: str, text_or_id: str):
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}
    payload = {"phone": phone, "text_or_id": text_or_id}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(f"{MCP_SERVER_URL}/delete_task", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()