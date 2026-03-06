# uvicorn websocket_node_service:app --workers 1 --host 0.0.0.0 --port 8001 --reload

import ast
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(); origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.active_connections_mapping: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.active_connections_mapping[client_id] = websocket

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            print('connection =', connection)
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    print('connection params = ', websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            print('data = ', data)
            data_dict = ast.literal_eval(data)
            print('data_dict =', data_dict)
            receiver = data_dict['receiver']
            msg_text = data_dict['message']
            await manager.send_personal_message(msg_text, manager.active_connections_mapping[receiver])
            # await manager.send_personal_message(f"{msg_text}", websocket)
            # await manager.send_personal_message(f"[{client_id}] {msg_text}", manager.active_connections_mapping[receiver])   ################
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # await manager.broadcast(f"Client #{client_id} left the chat")
        