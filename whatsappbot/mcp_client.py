import os, asyncio, httpx
from typing import Optional

# ✅ use a connectable host, not 0.0.0.0
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8086/mcp")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "your-secret-token")

class MCPError(Exception): ...

class MCPClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(self, method: str, path: str, *, json=None, params=None):
        # drop None-valued query params
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        try:
            r = await self._client.request(method, path, json=json, params=params)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            # surface server message to you
            raise MCPError(
                f"{method} {r.request.url} -> {r.status_code} {r.reason_phrase}\n{r.text}"
            ) from e
        except httpx.RequestError as e:
            # network/DNS/timeout
            raise MCPError(f"Network error calling {method} {path}: {e}") from e
        return r.json()

    async def add_task(self, phone: str, scope: str, text: str):
        return await self._request("POST", "/add_task", json={"phone": phone, "scope": scope, "text": text})

    async def list_tasks(self, phone: str, scope: Optional[str] = None):
        return await self._request("GET", "/list_tasks", params={"phone": phone, "scope": scope})

    async def complete_task(self, phone: str, text_or_id: str):
        return await self._request("POST", "/complete_task", json={"phone": phone, "text_or_id": text_or_id})

    async def delete_task(self, phone: str, text_or_id: str):
        # some servers ignore JSON bodies on DELETE; send as query params for compatibility
        return await self._request("DELETE", "/delete_task", params={"phone": phone, "text_or_id": text_or_id})

# quick smoke test
async def main():
    client = MCPClient(MCP_SERVER_URL, MCP_AUTH_TOKEN)
    try:
        print(await client.add_task("+919999999999", "personal", "Buy milk"))
        print(await client.list_tasks("+919999999999"))
        print(await client.complete_task("+919999999999", "Buy milk"))
        print(await client.delete_task("+919999999999", "Buy milk"))
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())