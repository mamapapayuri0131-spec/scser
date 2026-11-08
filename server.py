import asyncio
import json
import os
import websockets

# scser - Cloud Variable Server for TurboWarp / PenguinMod / Packager
# Connect via: wss://scser.com

ROOMS = {}

async def handler(websocket):
    project_id = None
    user = "Anonymous"
    
    try:
        async for message in websocket:
            lines = message.strip().split('\n')
            for line in lines:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                method = data.get("method")

                if method == "handshake":
                    project_id = str(data.get("project_id", "default"))
                    user = data.get("user", "Anonymous")
                    if project_id not in ROOMS:
                        ROOMS[project_id] = {"clients": set(), "vars": {}}
                    ROOMS[project_id]["clients"].add(websocket)
                    
                    # 接続時に現在の変数を同期
                    for var_name, var_val in ROOMS[project_id]["vars"].items():
                        await websocket.send(json.dumps({
                            "method": "set",
                            "name": var_name,
                            "value": var_val
                        }) + "\n")

                elif method == "set":
                    if project_id is None:
                        continue
                    var_name = data.get("name")
                    var_val = data.get("value")
                    
                    ROOMS[project_id]["vars"][var_name] = var_val

                    # 同じプロジェクトの他のクライアントへブロードキャスト
                    broadcast_msg = json.dumps({
                        "method": "set",
                        "name": var_name,
                        "value": var_val
                    }) + "\n"
                    
                    for client in ROOMS[project_id]["clients"]:
                        if client != websocket:
                            try:
                                await client.send(broadcast_msg)
                            except Exception:
                                pass

                elif method == "ping":
                    await websocket.send(json.dumps({"method": "ping"}) + "\n")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if project_id and project_id in ROOMS:
            ROOMS[project_id]["clients"].discard(websocket)
            if not ROOMS[project_id]["clients"] and not ROOMS[project_id]["vars"]:
                del ROOMS[project_id]

async def main():
    port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())