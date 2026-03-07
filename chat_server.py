import asyncio
import json
import datetime
import websockets

clients = set()
messages = []
posts = []

async def handler(ws):
    clients.add(ws)
    try:
        await ws.send(json.dumps({"type":"init","messages":messages,"posts":posts}))
        async for msg in ws:
            try:
                data = json.loads(msg)
            except:
                continue
            if data.get("type") == "chat":
                m = {
                    "user": data.get("user","guest"),
                    "text": data.get("text",""),
                    "time": datetime.datetime.utcnow().isoformat()
                }
                messages.append(m)
                if len(messages) > 500:
                    messages.pop(0)
                payload = json.dumps({"type":"chat","message":m})
                await asyncio.gather(*(c.send(payload) for c in clients))
            elif data.get("type") == "post":
                p = data.get("post") or {}
                pid = p.get("id") or f"p{int(datetime.datetime.utcnow().timestamp()*1000)}"
                item = {
                    "id": pid,
                    "boardId": p.get("boardId",""),
                    "title": p.get("title",""),
                    "author": p.get("author","guest"),
                    "time": p.get("time") or datetime.datetime.utcnow().isoformat()[:16].replace("T"," "),
                    "up": int(p.get("up",0)),
                    "down": int(p.get("down",0)),
                    "content": p.get("content","")
                }
                exists = next((x for x in posts if x.get("id")==pid), None)
                if not exists:
                    posts.append(item)
                    if len(posts) > 1000:
                        posts.pop(0)
                    payload = json.dumps({"type":"post","post":item})
                    await asyncio.gather(*(c.send(payload) for c in clients))
    finally:
        clients.discard(ws)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
