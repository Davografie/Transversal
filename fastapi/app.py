from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from typing import Dict, List
import json
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - line %(lineno)d - %(message)s')
stream_handler = logging.StreamHandler()

class ColorFormatter(logging.Formatter):
	def format(self, record):
		CYAN = "\033[1;96m"
		BLUE = "\033[94m"
		YELLOW = "\033[93m"
		ORANGE = "\033[93m"
		RESET = "\033[0m"

		if record.levelname == "INFO":
			COLOR = CYAN
		elif record.levelname == "DEBUG":
			COLOR = BLUE
		elif record.levelname == "WARNING":
			COLOR = YELLOW
		elif record.levelname == "ERROR":
			COLOR = ORANGE
		else:
			COLOR = RESET
		original_msg = super().format(record)
		# Only color the actual message part
		if record.msg:
			msg_str = str(record.getMessage())
			colored_msg = f"{COLOR}{msg_str}{RESET}"
			# Replace only the message part in the formatted string
			return original_msg.replace(msg_str, colored_msg, 1)
		return original_msg

log_formatter = ColorFormatter(
	"%(asctime)s [%(levelname)s] %(name)s/%(funcName)s(%(lineno)d): %(message)s",
	datefmt="%Y-%m-%d %H:%M:%S"
)

stream_handler.setFormatter(log_formatter)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logger.addHandler(stream_handler)

logger.info("Starting server")

app = FastAPI()

class ConnectionManager:
	def __init__(self):
		self.active_connections: Dict[str, WebSocket] = {}

	async def connect(self, websocket: WebSocket, player_id: str):
		await websocket.accept()
		self.active_connections[player_id] = websocket

		logger.debug(f"Connected player: {player_id}")

		try:
			while True:
				data = await websocket.receive_json()
				logger.debug(f"Received data: {data}")
				await self.broadcast(data, player_id)
		except WebSocketDisconnect:
			self.active_connections.pop(player_id, None)
	
	async def broadcast(self, message: Dict[str, str], from_player_id: str):
		"""
		Send message to all other active connections
		"""
		for player_id, connection in self.active_connections.items():
			if player_id != from_player_id:
				await connection.send_json(message)
			

# example endpoint url: ws://localhost:8000/ws/123
@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
	manager = ConnectionManager()
	await manager.connect(websocket, player_id)
	

		